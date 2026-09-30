"""Unit tests for anything-to-skill core: store, sanitize, ssrf, detect, cli."""

import io
import json
import subprocess
import sys
import unicodedata
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'anything-to-skill' / 'scripts'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from anything_to_skill import cli, sources  # noqa: E402
from anything_to_skill.core import tokens  # noqa: E402
from anything_to_skill.core.models import (  # noqa: E402
    MAX_ERRORS,
    RunSummary,
    source_label,
)
from anything_to_skill.core.sanitize import find_invisible, strip_invisible  # noqa: E402
from anything_to_skill.core.ssrf import SSRFError, check_url  # noqa: E402
from anything_to_skill.core.store import (  # noqa: E402
    BACKOFF_BASE_S,
    LEASE_S,
    MAX_ATTEMPTS,
    USER_DROPS_KEY,
    Store,
    backoff,
)
from anything_to_skill.core.workspace import Ctx, Workspace, WorkspaceError  # noqa: E402

NOW = 1_000_000.0
TWO = 2
THREE = 3
ZWSP = chr(0x200B)
TAG_A = chr(0xE0041)
RLO = chr(0x202E)


def fake_resolver(*ips: str) -> Callable[[str, int], list]:
    def resolve(_host: str, _port: int) -> list:
        return [(2, 1, 6, '', (ip, 0)) for ip in ips]

    return resolve


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store(tmp_path / 'ws') as s:
        yield s


# --- sanitize / tokens -------------------------------------------------------


def test_strip_invisible_removes_zero_width_tags_and_bidi() -> None:
    dirty = f'a{ZWSP}b{TAG_A}c{RLO}d'
    assert strip_invisible(dirty) == 'abcd'
    assert [cp for _, cp in find_invisible(dirty)] == [0x200B, 0xE0041, 0x202E]


def test_strip_invisible_keeps_normal_unicode() -> None:
    assert strip_invisible('naïve café 日本語 ✓') == 'naïve café 日本語 ✓'


def test_strip_invisible_covers_hidden_text_channels() -> None:
    hidden = [
        *(0xAD, 0x34F, 0x115F, 0x1160, 0x17B4, 0x180B, 0x180D, 0x2028, 0x2029),
        *(0x206A, 0x206F, 0x3164, 0xFFA0, 0xFFF9, 0xFFFB, 0xFE00, 0xFE0F),
        *(0xE0100, 0xE01EF),
    ]
    for cp in hidden:
        assert strip_invisible(f'a{chr(cp)}b') == 'ab', hex(cp)


def test_strip_invisible_covers_every_format_control() -> None:
    visible_prefixes = {*range(0x600, 0x606), 0x6DD, 0x70F, 0x890, 0x891, 0x8E2}
    visible_prefixes |= {0x110BD, 0x110CD}
    missed = [
        hex(cp)
        for cp in range(0x110000)
        if unicodedata.category(chr(cp)) == 'Cf'
        and cp not in visible_prefixes
        and strip_invisible(chr(cp))
    ]
    assert missed == []


def test_source_label_hides_credentials_and_local_paths() -> None:
    assert (
        source_label('https://u:p@x.test/d?token=abc&v=1&api_key=z#frag')
        == 'https://x.test/d?v=1'
    )
    assert source_label('file:///Users/me/proj/a%20b.md') == 'a b.md'
    assert source_label('file:///Users/me/proj/a.md', 'docs/a.md') == 'docs/a.md'
    assert source_label('/home/me/notes.txt') == 'notes.txt'


def test_token_count_is_chars_over_four() -> None:
    assert tokens.count('') == 0
    assert tokens.count('abcd') == 1
    assert tokens.count('abcde') == TWO


# --- store -------------------------------------------------------------------


def test_add_unit_is_idempotent_on_uri(store: Store) -> None:
    a = store.add_unit('web', 'https://x.test/a')
    assert store.add_unit('web', 'https://x.test/a') == a
    assert len(store.units()) == 1


def test_claim_orders_by_priority_and_leases(store: Store) -> None:
    low = store.add_unit('web', 'https://x.test/low', priority=1)
    high = store.add_unit('web', 'https://x.test/high', priority=9)
    first = store.claim(limit=1, now=NOW)
    assert [u.id for u in first] == [high]
    assert first[0].attempts == 1
    assert [u.id for u in store.claim(limit=5, now=NOW)] == [low]
    assert store.claim(limit=5, now=NOW) == []
    assert [u.id for u in store.claim(limit=5, now=NOW + LEASE_S + 1)] == [high, low]


def test_claim_filters_by_source_and_status(store: Store) -> None:
    w = store.add_unit('web', 'https://x.test/a')
    y = store.add_unit('youtube', 'https://youtu.be/1', kind='video')
    store.mark(y, 'needs_asr')
    assert [u.id for u in store.claim(source='web', now=NOW)] == [w]
    assert [u.id for u in store.claim(status='needs_asr', now=NOW)] == [y]


def test_finish_sanitizes_counts_tokens_and_writes_md(store: Store) -> None:
    uid = store.add_unit(
        'web', 'https://x.test/a', hint={'path': 'guide'}, meta={'scope': '/d/'}
    )
    unit = store.finish(
        uid,
        f'# T{ZWSP}itle\n\nbody{TAG_A}!',
        title='T',
        hint={'crumb': 'x'},
        etag='"e1"',
        last_modified='Mon',
    )
    text = (store.root / 'md' / f'{uid}.md').read_text(encoding='utf-8')
    assert text == '# Title\n\nbody!'
    assert unit.status == 'done'
    assert unit.md_path == f'md/{uid}.md'
    assert unit.tokens == tokens.count(text)
    assert len(unit.sha or '') == 64  # noqa: PLR2004
    assert unit.hint == {'path': 'guide', 'crumb': 'x'}
    assert unit.meta == {'scope': '/d/'}
    assert store.read_markdown(uid) == text


def test_finish_cleans_title_hint_and_meta(store: Store) -> None:
    uid = store.add_unit('web', 'https://x.test/a', hint={'path': f'g{TAG_A}uide'})
    unit = store.finish(
        uid,
        'body',
        title=f'Docs{TAG_A}\n title',
        hint={'headings': [f'H{ZWSP}1']},
        meta={'channel': f'c{RLO}h'},
    )
    assert unit.title == 'Docs title'
    assert unit.hint == {'path': 'guide', 'headings': ['H1']}
    assert unit.meta == {'channel': 'ch'}


def test_finish_same_content_gives_same_sha(store: Store) -> None:
    a = store.add_unit('web', 'https://x.test/a')
    b = store.add_unit('web', 'https://x.test/b')
    assert store.finish(a, f'same{ZWSP}').sha == store.finish(b, 'same').sha


def test_resume_after_reopen_keeps_done_and_requeues_expired_lease(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'ws'
    with Store(root) as s:
        done = s.add_unit('web', 'https://x.test/done')
        stuck = s.add_unit('web', 'https://x.test/stuck')
        s.claim(limit=2, now=NOW)
        s.finish(done, 'ok')
    with Store(root) as s:
        assert s.get(done).status == 'done'
        assert s.claim(now=NOW + 1) == []  # lease still held
        assert [u.id for u in s.claim(now=NOW + LEASE_S + 1)] == [stuck]


def test_fail_backs_off_then_gives_up(store: Store) -> None:
    uid = store.add_unit('web', 'https://x.test/a')
    store.claim(now=NOW)
    assert store.fail(uid, 'boom', now=NOW) == 'pending'
    unit = store.get(uid)
    assert unit.next_at == NOW + BACKOFF_BASE_S
    assert unit.error == 'boom'
    assert store.claim(now=NOW + BACKOFF_BASE_S - 1) == []
    assert store.claim(now=NOW + BACKOFF_BASE_S)[0].attempts == TWO
    assert store.fail(uid, 'boom', now=NOW + 60) == 'pending'
    assert store.get(uid).next_at == NOW + 60 + BACKOFF_BASE_S * TWO
    for i in range(MAX_ATTEMPTS):
        store.claim(now=NOW + 10_000 * (i + 1))
    assert store.fail(uid, 'final') == 'failed'
    assert store.get(uid).status == 'failed'


def test_backoff_grows_and_caps() -> None:
    assert [backoff(n) for n in (1, 2, 3)] == [30, 60, 120]
    assert backoff(50) == 3600  # noqa: PLR2004


def test_fail_keeps_needs_asr_status_while_retrying(store: Store) -> None:
    uid = store.add_unit('youtube', 'https://youtu.be/1', kind='video')
    store.mark(uid, 'needs_asr')
    store.claim(status='needs_asr', now=NOW)
    assert store.fail(uid, 'gpu busy', now=NOW) == 'needs_asr'


def test_etag_and_last_modified_survive_304_and_refetch(store: Store) -> None:
    uid = store.add_unit('web', 'https://x.test/a')
    store.finish(uid, 'v1', etag='"e1"', last_modified='Mon')
    store.mark(uid, 'pending')
    unit = store.claim(now=NOW)[0]
    assert (unit.etag, unit.last_modified) == ('"e1"', 'Mon')
    store.not_modified(uid)
    assert store.get(uid).status == 'done'
    assert store.get(uid).etag == '"e1"'
    store.finish(uid, 'v2')  # no new validators: keep the old ones
    assert store.get(uid).etag == '"e1"'
    store.finish(uid, 'v3', etag='"e2"')
    assert store.get(uid).etag == '"e2"'


def test_mark_rejects_unknown_status_and_resets_retry_budget(store: Store) -> None:
    uid = store.add_unit('web', 'https://x.test/a')
    store.claim(now=NOW)
    with pytest.raises(ValueError, match='unknown status'):
        store.mark(uid, 'weird')
    store.mark(uid, 'needs_js', error='shell')
    unit = store.get(uid)
    assert (unit.status, unit.attempts, unit.next_at) == ('needs_js', 0, 0)


def test_requeue_and_counts(store: Store) -> None:
    a = store.add_unit('web', 'https://x.test/a')
    b = store.add_unit('web', 'https://x.test/b')
    store.add_unit('local', '/tmp/f.md', kind='file')  # noqa: S108
    store.mark(a, 'failed')
    store.mark(b, 'needs_js')
    assert store.requeue('failed', 'needs_js') == TWO
    assert store.counts() == {'web': {'pending': TWO}, 'local': {'pending': 1}}


def test_next_due_reports_backed_off_units(store: Store) -> None:
    uid = store.add_unit('web', 'https://x.test/a')
    store.claim(now=NOW)
    store.fail(uid, 'x', now=NOW)
    assert store.next_due(source='web') == NOW + BACKOFF_BASE_S
    assert store.next_due(source='youtube') is None


def test_throttle_counts_cover_the_whole_log_not_the_recent_tail(store: Store) -> None:
    total = 260
    for _ in range(total):
        store.log_throttle('old.test', '429', status=429)
    store.log_throttle('new.test', 'backoff')
    assert store.throttle_counts() == {
        'old.test': {'429': total},
        'new.test': {'backoff': 1},
    }
    assert len(store.throttle_events()) < total


def test_meta_and_throttle_log_roundtrip(store: Store) -> None:
    store.set_meta('goal', 'psql')
    store.set_meta('goal', 'sql')
    assert store.get_meta('goal') == 'sql'
    assert store.get_meta('missing', 'd') == 'd'
    store.log_throttle('x.test', '429', status=429, wait=2.5, detail='Retry-After')
    store.log_throttle('x.test', 'breaker_open')
    events = store.throttle_events()
    assert [e['event'] for e in events] == ['429', 'breaker_open']
    assert events[0]['wait'] == pytest.approx(2.5)


def test_user_dropped_units_are_never_claimed_or_waited_for(store: Store) -> None:
    gone = store.add_unit('web', 'https://x.test/gone', priority=9)
    kept = store.add_unit('web', 'https://x.test/kept')
    store.set_meta(USER_DROPS_KEY, {str(gone): 'x'})
    assert [u.id for u in store.claim(limit=5, now=NOW)] == [kept]
    assert store.next_due('web') == store.get(kept).next_at


def test_set_priority_reorders_the_claim_queue(store: Store) -> None:
    a = store.add_unit('web', 'https://x.test/a', priority=1)
    b = store.add_unit('web', 'https://x.test/b', priority=2)
    store.set_priority(a, 5)
    assert [u.id for u in store.claim(limit=2, now=NOW)] == [a, b]


def test_token_total_counts_done_only(store: Store) -> None:
    a = store.add_unit('web', 'https://x.test/a')
    store.add_unit('web', 'https://x.test/b')
    store.finish(a, 'x' * 40)
    assert store.token_total() == 10  # noqa: PLR2004
    assert store.token_total('youtube') == 0
    assert store.token_total(exclude=[a]) == 0


# --- ssrf --------------------------------------------------------------------


@pytest.mark.parametrize(
    'ip',
    [
        '127.0.0.1',
        '10.1.2.3',
        '192.168.0.9',
        '169.254.169.254',
        '::1',
        '::ffff:127.0.0.1',
        '100.64.0.1',
        '0.0.0.0',  # noqa: S104
    ],
)
def test_ssrf_denies_non_public_addresses(ip: str) -> None:
    with pytest.raises(SSRFError):
        check_url('https://evil.test/x', resolve=fake_resolver(ip))


def test_ssrf_allows_public_and_denies_mixed_answers() -> None:
    assert check_url('https://ok.test/x', resolve=fake_resolver('93.184.216.34')) == (
        'https://ok.test/x'
    )
    with pytest.raises(SSRFError):
        check_url('https://ok.test/x', resolve=fake_resolver('93.184.216.34', '10.0.0.1'))


@pytest.mark.parametrize(
    'url', ['file:///etc/passwd', 'ftp://x.test/', 'gopher://x', '//x.test', 'https://']
)
def test_ssrf_rejects_scheme_and_host(url: str) -> None:
    with pytest.raises(SSRFError):
        check_url(url, resolve=fake_resolver('93.184.216.34'))


def test_ssrf_allow_private_skips_host_but_not_scheme() -> None:
    assert check_url('http://127.0.0.1:8000/', allow_private=True)
    with pytest.raises(SSRFError):
        check_url('file:///etc/passwd', allow_private=True)


def test_ssrf_denies_nat64_embedding_private_ipv4() -> None:
    for embedded in ('64:ff9b::7f00:1', '64:ff9b::a9fe:a9fe'):
        with pytest.raises(SSRFError):
            check_url(
                'https://x.test/',
                resolve=lambda *_a, ip=embedded: [(10, 1, 6, '', (ip, 0))],
            )
    check_url(
        'https://x.test/', resolve=lambda *_a: [(10, 1, 6, '', ('64:ff9b::5db8:d822', 0))]
    )


def test_ssrf_unresolvable_host_is_denied() -> None:
    def boom(_host: str, _port: int) -> list:
        raise OSError('nxdomain')

    with pytest.raises(SSRFError, match='cannot resolve'):
        check_url('https://nope.test/', resolve=boom)


# --- workspace ---------------------------------------------------------------


def test_workspace_layout_and_slug_validation(tmp_path: Path) -> None:
    ws = Workspace.create('pg-docs', tmp_path)
    assert ws.dir == tmp_path / 'pg-docs'
    assert ws.authored_dir.is_dir()
    assert ws.plan_path.name == 'plan.json'
    for bad in ('../x', 'A B', '', '-x'):
        with pytest.raises(WorkspaceError):
            Workspace.create(bad, tmp_path)


def test_workspace_find_requires_slug_when_ambiguous(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceError, match='no workspace'):
        Workspace.find(None, tmp_path)
    for slug in ('a', 'b'):
        Workspace.create(slug, tmp_path).open_store().close()
    with pytest.raises(WorkspaceError, match='--slug'):
        Workspace.find(None, tmp_path)
    assert Workspace.find('b', tmp_path).slug == 'b'


def test_ctx_reads_goal_effort_and_budget(tmp_path: Path) -> None:
    ws = Workspace.create('w', tmp_path)
    with ws.open_store() as s:
        s.set_meta('goal', 'indexes')
        s.set_meta('effort', 'quick')
        ctx = Ctx.open(ws, s, max_pages=THREE)
        assert (ctx.goal, ctx.effort, ctx.max_pages) == ('indexes', 'quick', THREE)
        assert ctx.token_budget == 50_000  # noqa: PLR2004
        assert not ctx.over_budget()
        s.finish(s.add_unit('web', 'https://x.test/a'), 'x' * 200_000)
        assert ctx.over_budget()
        s.set_meta(USER_DROPS_KEY, {'1': 'x'})
        assert not ctx.over_budget()
        s.set_meta(USER_DROPS_KEY, {})
        ctx.effort = 'complete'
        assert not ctx.over_budget()


# --- source detect routing ---------------------------------------------------


@pytest.mark.parametrize(
    ('arg', 'expected'),
    [
        ('https://www.youtube.com/watch?v=abc', ('youtube', 10)),
        ('https://youtu.be/abc', ('youtube', 10)),
        ('https://docs.example.com/guide/', ('web', 1)),
        ('http://example.com', ('web', 1)),
        ('a topic to research', None),
        ('ftp://example.com/x', None),
    ],
)
def test_route_urls_and_topics(arg: str, expected: tuple[str, int] | None) -> None:
    assert sources.route(arg) == expected


def test_route_local_paths_win_over_web(tmp_path: Path) -> None:
    (tmp_path / 'book.pdf').write_bytes(b'%PDF')
    assert sources.route(str(tmp_path)) == ('local', 10)
    assert sources.route(str(tmp_path / 'book.pdf')) == ('local', 10)
    assert sources.route(str(tmp_path / 'missing.pdf')) is None


def test_unknown_source_name_is_rejected() -> None:
    with pytest.raises(ValueError, match='unknown source'):
        sources.load_run('gopher')


def test_routing_imports_no_run_modules_or_heavy_deps() -> None:
    probe = (
        'import sys; sys.path.insert(0, sys.argv[1]);'
        'from anything_to_skill import sources; sources.route("https://example.com");'
        'bad = [m for m in sys.modules if m.endswith(".run") or m.split(".")[0] in '
        '("curl_cffi", "docling", "yt_dlp", "laya", "trafilatura")];'
        'print(bad); sys.exit(1 if bad else 0)'
    )
    done = subprocess.run(
        [sys.executable, '-c', probe, str(SCRIPTS_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout


# --- cli ---------------------------------------------------------------------


def test_cli_init_seed_status_estimate(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = str(tmp_path / '.cc-arsenal' / 'a2s')
    doc = tmp_path / 'notes'
    doc.mkdir()
    code = cli.main(['init', 'pg', '--base', base, '--goal', 'psql', '--effort', 'quick'])
    assert code == 0
    assert json.loads(capsys.readouterr().out)['slug'] == 'pg'

    monkeypatch.setattr(
        sys,
        'stdin',
        io.StringIO('https://a.test/docs#frag\n# c\n\nnot a url\n'),
    )
    code = cli.main(
        [
            'seed',
            '--base',
            base,
            '--slug',
            'pg',
            str(doc),
            'https://youtu.be/x',
            '--urls',
            '-',
        ]
    )
    out = json.loads(capsys.readouterr().out)
    assert (code, out['added'], out['rejected']) == (0, THREE, ['not a url'])

    cli.main(['seed', '--base', base, 'https://a.test/docs'])
    assert json.loads(capsys.readouterr().out)['existing'] == 1

    with Workspace.find('pg', Path(base)).open_store() as s:
        uris = {u.uri: u for u in s.units()}
        assert 'https://a.test/docs' in uris
        assert uris['https://a.test/docs'].kind == 'seed'
        assert uris[str(doc.resolve())].source == 'local'
        wid = s.add_unit('web', 'https://a.test/p1')
        s.finish(wid, 'x' * 400)
        s.log_throttle('a.test', '429', status=429, wait=3)
        s.add_unit('web', 'https://a.test/p2')

    assert cli.main(['status', '--base', base, '--json']) == 0
    status = json.loads(capsys.readouterr().out)
    assert status['sources']['web']['by_status']['done'] == 1
    assert status['sources']['web']['tokens'] == 100  # noqa: PLR2004
    assert status['throttle']['per_host'] == {'a.test': {'429': 1}}
    assert status['effort'] == 'quick'

    assert cli.main(['estimate', '--base', base, '--json']) == 0
    est = json.loads(capsys.readouterr().out)
    web = est['sources']['web']
    assert (web['done'], web['pending'], web['avg_tokens']) == (1, 1, 100)
    assert web['corpus_tokens'] == 200  # noqa: PLR2004
    assert est['token_budget'] == 50_000  # noqa: PLR2004
    assert est['projected_llm_tokens']['total'] > 0
    assert any('Laya' in d for d in est['first_run_downloads'])

    assert cli.main(['status', '--base', base]) == 0
    assert 'web:' in capsys.readouterr().out


def test_estimate_projects_what_the_effort_budget_will_fetch(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    ws = Workspace.create('pg', base=tmp_path)
    with ws.open_store() as s:
        s.set_meta('effort', 'quick')
        s.finish(s.add_unit('web', 'https://a.test/done'), 'x' * 40_000)
        for i in range(400):
            s.add_unit('web', f'https://a.test/p{i}')

    def estimate(*extra: str) -> dict:
        cli.main(['estimate', '--base', str(tmp_path), '--slug', 'pg', '--json', *extra])
        return json.loads(capsys.readouterr().out)

    capped = estimate()
    assert capped['uncapped_tokens'] == 10_000 + 400 * 10_000
    assert capped['fetched_tokens'] == 10_000  # noqa: PLR2004
    assert (capped['pending'], capped['will_fetch']) == (400, 4)
    assert capped['corpus_tokens'] == 50_000  # noqa: PLR2004
    assert capped['capped_by'] == ['budget']
    limited = estimate('--max-pages', '3')
    assert (limited['will_fetch'], limited['capped_by']) == (3, ['max_pages'])
    assert limited['corpus_tokens'] == 40_000  # noqa: PLR2004
    assert cli.main(['estimate', '--base', str(tmp_path), '--slug', 'pg']) == 0
    assert 'crawl stops at budget 50000' in capsys.readouterr().out


def test_estimate_and_requeue_honor_drops(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    ws = Workspace.create('pg', base=tmp_path)
    with ws.open_store() as s:
        done = s.add_unit('web', 'https://a.test/done')
        s.finish(done, 'x' * 40_000)
        for i in range(4):
            s.add_unit('web', f'https://a.test/p{i}')
        video = s.add_unit('youtube', 'https://youtu.be/v1', kind='video')
        s.mark(video, 'needs_asr')
    base = ['--base', str(tmp_path), '--slug', 'pg']

    def web() -> dict:
        cli.main(['estimate', '--json', *base])
        return json.loads(capsys.readouterr().out)['sources']['web']

    before = web()
    assert (before['done'], before['pending'], before['done_tokens']) == (1, 4, 10_000)
    assert cli.main(['drop', str(done), 'https://a.test/p0', '--reason', 'x', *base]) == 0
    capsys.readouterr()
    after = web()
    assert (after['done'], after['pending'], after['done_tokens']) == (0, 3, 0)
    cli.main(['status', '--json', *base])
    assert json.loads(capsys.readouterr().out)['corpus_tokens'] == 0

    assert cli.main(['requeue', 'https://youtu.be/v1', '--status', 'pending', *base]) == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1]) == {
        'requeued': [video],
        'status': 'pending',
    }
    with ws.open_store() as s:
        assert s.get(video).status == 'pending'
    assert cli.main(['requeue', '999', *base]) == TWO
    assert '999' in capsys.readouterr().err


def test_cli_detect_prints_routes(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    assert (
        cli.main(
            [
                'detect',
                '--json',
                'https://youtu.be/a',
                'https://a.test',
                'nothing',
                str(tmp_path),
            ]
        )
        == 0
    )
    rows = json.loads(capsys.readouterr().out)
    assert [r['source'] for r in rows] == ['youtube', 'web', None, 'local']


def test_cli_reports_missing_workspace(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    assert cli.main(['status', '--base', str(tmp_path / 'none')]) == TWO
    assert 'run init first' in capsys.readouterr().err


def test_cli_plan_and_verify_dispatch_on_empty_workspace(tmp_path: Path) -> None:
    base = str(tmp_path / '.cc-arsenal' / 'a2s')
    cli.main(['init', 'pg', '--base', base])
    assert cli.main(['plan', '--base', base]) == 0
    assert cli.main(['verify', '--base', base]) == TWO


def test_cli_seed_rejects_urls_with_userinfo(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    base = str(tmp_path / '.cc-arsenal' / 'a2s')
    cli.main(['init', 'pg', '--base', base])
    capsys.readouterr()
    cli.main(['seed', '--slug', 'pg', '--base', base, 'https://u:pw@docs.test/a'])
    out = json.loads(capsys.readouterr().out)
    assert out['added'] == 0
    assert out['rejected'] == ['https://docs.test/a']


def test_run_summary_notes_dedupe_and_cap() -> None:
    summary = RunSummary()
    for i in range(MAX_ERRORS * 2):
        summary.note(f'e{i % (MAX_ERRORS + 5)}')
    assert len(summary.errors) == MAX_ERRORS
    assert len(set(summary.errors)) == MAX_ERRORS
