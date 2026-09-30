"""Tests for anything-to-skill web ingest: throttle, robots, discovery, fetch, run.

All network traffic goes to a local http.server; agent-browser is never launched.
"""

# ruff: noqa: PLR2004 - status codes and counts are the assertions here, not magic numbers

import argparse
import asyncio
import itertools
import json
import random
import subprocess
import sys
import threading
import time
from collections.abc import Coroutine, Iterator
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import trafilatura
from curl_cffi.requests.impersonate import DEFAULT_CHROME

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'anything-to-skill' / 'scripts'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from anything_to_skill import cli  # noqa: E402
from anything_to_skill.core import store as store_module  # noqa: E402
from anything_to_skill.core.models import EFFORT_BUDGET, RunSummary, Unit  # noqa: E402
from anything_to_skill.core.ssrf import SSRFError  # noqa: E402
from anything_to_skill.core.store import Store  # noqa: E402
from anything_to_skill.core.workspace import Ctx, Workspace  # noqa: E402
from anything_to_skill.sources.web import (  # noqa: E402
    browser,
    discover,
    extract,
    fetch,
    frontier,
    run as web_run,
)
from anything_to_skill.sources.web.throttle import (  # noqa: E402
    HostBlockedError,
    HostThrottle,
    RobotsCache,
    parse_retry_after,
)

FIXTURES = Path(__file__).parent / 'fixtures' / 'anything_to_skill' / 'web'
FIVE = 5
PLAIN_ROBOTS = 'User-agent: *\nAllow: /\n'
SITEMAP_ROBOTS = PLAIN_ROBOTS + 'Sitemap: {BASE}/sitemap_index.xml\n'
SIXTY = 60.0
Response = tuple[int, dict[str, str], str]


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding='utf-8')


def para(topic: str) -> str:
    return (
        f'<p>{topic} matters when a table grows large. The planner weighs {topic} vs '
        f'sequential scans, statistics, and available memory before choosing a plan for '
        f'the query. Measure {topic} with EXPLAIN ANALYZE rather than guessing.</p>'
    )


def page(title: str, body: str = '', links: tuple[str, ...] = (), nav: str = '') -> str:
    anchors = ''.join(
        f'<li><a href="{href}">{href.strip("/")}</a></li>' for href in links
    )
    return (
        f'<html><head><title>{title}</title></head><body><nav>{nav}</nav>'
        f'<main><h1>{title}</h1>{para(title)}{body}<ul>{anchors}</ul></main>'
        f'<footer>copyright</footer></body></html>'
    )


# --- local site --------------------------------------------------------------


class Site:
    """A scriptable local HTTP site. routes[path] is a Response, a list (consumed in
    order, last one repeats) or a callable(request headers) -> Response."""

    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}
        self.hits: list[tuple[str, dict[str, str]]] = []
        site = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def do_GET(self) -> None:
                path = self.path.split('?')[0]
                headers = {k.lower(): v for k, v in self.headers.items()}
                site.hits.append((path, headers))
                status, out_headers, body = site.respond(path, headers)
                data = body.replace('{BASE}', site.url).encode()
                self.send_response(status)
                for key, value in out_headers.items():
                    self.send_header(key, value)
                self.send_header(
                    'Content-Length', str(len(data)) if status != 304 else '0'
                )
                self.end_headers()
                if status != 304:
                    self.wfile.write(data)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def respond(self, path: str, headers: dict[str, str]) -> Response:
        route = self.routes.get(path)
        if callable(route):
            return cast('Response', route(headers))
        if isinstance(route, list):
            return route.pop(0) if len(route) > 1 else route[0]
        return route or (404, {}, 'not found')

    def html(self, path: str, body: str) -> None:
        self.routes[path] = (200, {'Content-Type': 'text/html; charset=utf-8'}, body)

    def text(self, path: str, body: str, ctype: str = 'text/plain') -> None:
        self.routes[path] = (200, {'Content-Type': ctype}, body)

    def hit_paths(self) -> list[str]:
        return [p for p, _ in self.hits]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def site() -> Iterator[Site]:
    s = Site()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def no_real_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(browser.shutil, 'which', lambda _name: None)


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    async def wrapped() -> T:
        try:
            return await coro
        finally:
            await fetch.close_session()

    return asyncio.run(wrapped())


def make_net(*, allow_private: bool = True, events: list | None = None) -> fetch.Net:
    log = (lambda *a, **_k: events.append(a)) if events is not None else None
    return fetch.Net(HostThrottle(log, floor=0.0), RobotsCache(), allow_private)


@pytest.fixture
def ctx(tmp_path: Path) -> Iterator[Ctx]:
    ws = Workspace.create('t', base=tmp_path)
    with ws.open_store() as store:
        store.set_meta('goal', 'indexing performance')
        yield Ctx.open(ws, store, allow_private=True)


def args_for(*extra: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    web_run.add_args(parser)
    return parser.parse_args(['--min-delay', '0', '--workers', '2', *extra])


def seed(ctx: Ctx, uri: str, scope: str | None = None) -> None:
    ctx.store.add_unit(
        'web', uri, kind='seed', priority=100.0, meta={'scope': scope} if scope else {}
    )


def crawl(ctx: Ctx, *extra: str) -> RunSummary:
    return web_run.run(ctx, args_for(*extra))


def unit_at(ctx: Ctx, uri: str) -> Unit:
    unit = ctx.store.get_by_uri(uri)
    assert unit is not None, uri
    return unit


def statuses(store: Store) -> dict[str, str]:
    return {u.uri.split('/', 3)[-1]: u.status for u in store.units(source='web')}


# --- throttle ------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds


def fake_throttle(events: list, clock: FakeClock, **kw: Any) -> HostThrottle:
    return HostThrottle(
        lambda *a: events.append(a),
        clock=clock,
        sleep=clock.sleep,
        rng=random.Random(7),  # noqa: S311 - deterministic jitter, not security
        **kw,
    )


def test_delay_is_floor_times_jitter_and_crawl_delay_wins() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock)

    async def gaps(n: int) -> list[float]:
        stamps = []
        for _ in range(n):
            await throttle.acquire('h')
            stamps.append(clock.now)
            throttle.release('h', 200)
        return [b - a for a, b in itertools.pairwise(stamps)]

    assert all(1.0 <= g <= 2.0 for g in asyncio.run(gaps(6)))
    throttle.set_crawl_delay('h', 3.0)
    assert all(3.0 <= g <= 6.0 for g in asyncio.run(gaps(6)))


def test_aimd_grows_after_successes_and_halves_on_429() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, start=2, ceiling=4, grow_after=3)

    async def go() -> None:
        for _ in range(3):
            await throttle.acquire('h')
            throttle.release('h', 200)
        assert throttle.host('h').limit == 3
        await throttle.acquire('h')
        throttle.release('h', 429)

    asyncio.run(go())
    assert throttle.host('h').limit == 1
    assert [e[1] for e in events] == ['backoff']
    assert events[0][2] == 429


def test_retry_after_beats_jitter_and_is_logged() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, backoff_base=0.0)

    async def go() -> float:
        await throttle.acquire('h')
        throttle.release('h', 503, retry_after=30.0)
        before = clock.now
        await throttle.acquire('h')
        return clock.now - before

    assert asyncio.run(go()) >= 30.0
    assert 'retry-after=30s' in events[0][4]


def test_full_jitter_backoff_is_bounded_by_the_exponential_cap() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, backoff_base=10.0)

    async def go() -> None:
        for _ in range(3):
            await throttle.acquire('h')
            throttle.release('h', 429)

    asyncio.run(go())
    waits = [e[3] for e in events]
    assert all(0 <= w <= 10.0 * 2**n for n, w in enumerate(waits, start=1))


def test_parse_retry_after_seconds_date_and_garbage() -> None:
    assert parse_retry_after('7') == 7.0
    assert parse_retry_after(' 12 ') == 12.0
    assert parse_retry_after(formatdate(time.time() + 90, usegmt=True)) == pytest.approx(
        90, abs=3
    )
    assert parse_retry_after(formatdate(time.time() - 500, usegmt=True)) == 0.0
    assert parse_retry_after('soon') is None
    assert parse_retry_after(None) is None


def _trip(throttle: HostThrottle, status: int = 403) -> None:
    async def go() -> None:
        for _ in range(FIVE):
            await throttle.acquire('h')
            throttle.release('h', status)

    asyncio.run(go())


def test_breaker_opens_after_five_blocks_then_probe_closes_it() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, cooldown=SIXTY, backoff_base=0.0)
    _trip(throttle)
    assert events[-1][1] == 'breaker_open'
    tripped_at = clock.now

    async def probe() -> None:
        await throttle.acquire('h')
        throttle.release('h', 200)

    asyncio.run(probe())
    assert clock.now - tripped_at >= SIXTY
    assert [e[1] for e in events][-2:] == ['breaker_open', 'breaker_closed']
    assert not throttle.host('h').tripped


def test_breaker_gives_up_when_the_probe_is_refused() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, cooldown=SIXTY, backoff_base=0.0)
    _trip(throttle, 429)

    async def probe() -> None:
        await throttle.acquire('h')
        throttle.release('h', 429)
        await throttle.acquire('h')

    with pytest.raises(HostBlockedError):
        asyncio.run(probe())
    assert 'host_skipped' in [e[1] for e in events]


def test_a_healthy_response_resets_the_block_count() -> None:
    clock, events = FakeClock(), []
    throttle = fake_throttle(events, clock, floor=0.0, backoff_base=0.0)

    async def go() -> None:
        for status in (403, 403, 200, 403, 403, 403, 403):
            await throttle.acquire('h')
            throttle.release('h', status)

    asyncio.run(go())
    assert not throttle.host('h').tripped


# --- robots ---------------------------------------------------------------------


def test_robots_rules_crawl_delay_and_sitemaps() -> None:
    robots = RobotsCache()
    robots.load('http://x', 200, fixture_text('robots.txt'))
    assert robots.allowed('http://x', 'http://x/docs/a.html')
    assert not robots.allowed('http://x', 'http://x/private/a.html')
    assert robots.crawl_delay('http://x') == 2.0
    assert robots.sitemaps('http://x') == ['{BASE}/sitemap_index.xml']


def test_robots_wildcards_and_longest_match() -> None:
    robots = RobotsCache()
    robots.load(
        'http://x',
        200,
        'User-agent: *\nDisallow: /*.pdf$\nDisallow: /*?session=\n'
        'Disallow: /private/\nAllow: /private/ok\n',
    )
    for url, allowed in (
        ('http://x/a.pdf', False),
        ('http://x/a.pdf?page=2', True),
        ('http://x/a?session=1', False),
        ('http://x/private/ok', True),
        ('http://x/private/no', False),
        ('http://x/docs', True),
    ):
        assert robots.allowed('http://x', url) is allowed, url


@pytest.mark.parametrize(
    ('status', 'allowed'),
    [
        (500, False),
        (503, False),
        (429, True),
        (401, True),
        (403, True),
        (404, True),
        (410, True),
    ],
)
def test_robots_status_policy(status: int, allowed: bool) -> None:
    robots = RobotsCache()
    robots.load('http://x', status, 'irrelevant')
    assert robots.allowed('http://x', 'http://x/a') is allowed


def test_robots_network_error_disallows_and_cache_expires_after_24h() -> None:
    now = [0.0]
    robots = RobotsCache(clock=lambda: now[0])
    robots.load('http://x', None)
    assert not robots.allowed('http://x', 'http://x/a')
    assert robots.fresh('http://x')
    now[0] = 86400 - 1
    assert robots.fresh('http://x')
    now[0] = 86400 + 1
    assert not robots.fresh('http://x')


# --- extraction -------------------------------------------------------------------


def test_pre_blocks_survive_as_fences_via_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = fixture_text('pre_heavy.html')
    real = trafilatura.extract
    monkeypatch.setattr(
        trafilatura,
        'extract',
        lambda *_a, **_k: 'Indexes let the planner avoid scanning.',
    )
    md, title = extract.to_markdown(html, 'http://x/docs/cookbook.html')
    assert title == 'Indexing Cookbook'
    assert md.count('```') // 2 >= 3
    assert 'CREATE INDEX idx_orders_customer ON orders (customer_id);' in md
    assert 'Copyright Acme' not in md
    monkeypatch.setattr(trafilatura, 'extract', real)
    md2, _ = extract.to_markdown(html, 'http://x/docs/cookbook.html')
    assert 'CREATE INDEX idx_open_orders' in md2


def test_prose_only_pages_do_not_trigger_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = []
    monkeypatch.setattr(
        extract, '_via_html_to_markdown', lambda *a: called.append(a) or 'alt'
    )
    md, title = extract.to_markdown(page('Statistics'), 'http://x/docs/s.html')
    assert 'Statistics' in md
    assert title == 'Statistics'
    assert not called


def test_content_container_is_found_with_balanced_nesting() -> None:
    html = (
        '<div id="top"><nav>menu</nav><div id="docContent"><div><p>a</p></div>'
        '<pre>code</pre></div><footer>foot</footer></div>'
    )
    assert extract.content_container(html) == (
        '<div id="docContent"><div><p>a</p></div><pre>code</pre></div>'
    )
    with_main = '<div id="content">x</div><main><p>m</p></main>'
    assert extract.content_container(with_main) == '<main><p>m</p></main>'
    assert extract.content_container('<p>plain</p>') == '<p>plain</p>'


def test_resolve_links_absolutizes_and_unwraps_same_page_links() -> None:
    md = (
        '# [uv](https://h/uv/getting-started/#uv)\n'
        'See [guides](../guides/ "Guides") and [top](#top) and [ext](https://x.io/a).\n'
        '```\n[keep](../as-is/)\n```\n'
    )
    out = extract.resolve_links(md, 'https://h/uv/getting-started/')
    assert out.splitlines()[0] == '# uv'
    assert '[guides](https://h/uv/guides/ "Guides")' in out
    assert 'and top and' in out
    assert '[ext](https://x.io/a)' in out
    assert '[keep](../as-is/)' in out


def test_js_shell_and_blocked_detection() -> None:
    assert extract.is_js_shell(fixture_text('js_shell.html'))
    assert not extract.is_js_shell(page('Doc'))
    assert not extract.is_js_shell('<html><body>tiny</body></html>')
    assert extract.is_blocked(fixture_text('blocked.html'))
    long_doc = page('Doc', para('captcha handling') * 40)
    assert not extract.is_blocked(long_doc)


def strip_repeated_lines(docs: dict[int, str]) -> dict[int, str]:
    return extract.remove_boilerplate(docs, *extract.find_boilerplate(docs))


def test_boilerplate_keeps_table_headers_rules_and_code_blank_runs() -> None:
    table = '| Option | Description |\n| --- | --- |\n| a | b |'
    code = '```python\ndef f():\n    pass\n\n\ndef g():\n    pass\n```'
    nav = 'Subscribe to the newsletter'
    docs = {i: f'{nav}\n\n{table}\n\n---\n\n{code}\n\nUnique {i}\n' for i in range(6)}
    out = strip_repeated_lines(docs)
    assert set(out) == set(docs)
    assert nav not in out[0]
    assert '| Option | Description |' in out[0]
    assert '| --- | --- |' in out[0]
    assert '\n---\n' in out[0]
    assert 'pass\n\n\ndef g' in out[0]


def test_strip_repeated_lines_keeps_headings_code_and_unique_prose() -> None:
    nav = 'Subscribe to the newsletter'
    docs = {
        i: f'# Parameters\n\n{nav}\n\nUnique body {i}\n\n```\n{nav}\n```\n'
        for i in range(6)
    }
    out = strip_repeated_lines(docs)
    assert set(out) == set(docs)
    assert nav not in out[0].replace('```\n' + nav + '\n```', '')
    assert '# Parameters' in out[0]
    assert f'```\n{nav}\n```' in out[0]
    assert 'Unique body 3' in out[3]
    assert strip_repeated_lines({k: docs[k] for k in range(3)}) == {}


def test_strip_repeated_lines_takes_banners_and_footers_at_30_percent() -> None:
    banner = 'September 24, 2026: [Beta 4 Released!](https://x.test/news/1)'
    footer = (
        'use [this form](https://x.test/comments/{n}) to report a documentation issue.'
    )
    docs = {
        i: (f'{banner}\n\n' if i < 4 else '')
        + f'# T{i}\n\nBody {i}\n\n{footer.format(n=i)}\n'
        for i in range(10)
    }
    docs[0] += f'\nBody again\n\n{banner}\n'
    out = strip_repeated_lines(docs)
    assert set(out) == set(docs)
    assert all(banner not in out[i].split('Body')[0] for i in range(4))
    assert all('documentation issue' not in d for d in out.values())
    assert 'Body 7' in out[7]


def test_strip_host_boilerplate_is_per_host_over_all_stored_pages_and_idempotent(
    ctx: Ctx,
) -> None:
    banner = 'Site-wide banner: v19 Beta 4 Released!'
    ids = {}
    for host, count, has_banner in (('a.test', 6, True), ('b.test', 40, False)):
        for i in range(count):
            uid = ctx.store.add_unit('web', f'https://{host}/p{i}')
            top = f'{banner}\n\n' if has_banner else ''
            ctx.store.finish(uid, f'{top}# P{i}\n\nUnique {host} {i}\n')
            ids[host, i] = uid
    assert web_run.strip_host_boilerplate(ctx.store) == 6
    assert banner not in ctx.store.read_markdown(ids['a.test', 0])
    assert 'Unique a.test 0' in ctx.store.read_markdown(ids['a.test', 0])
    assert web_run.strip_host_boilerplate(ctx.store) == 0
    late = ctx.store.add_unit('web', 'https://a.test/late')
    ctx.store.finish(late, f'{banner}\n\n# Late\n\nUnique late\n')
    for i in range(40):
        ctx.store.finish(
            ctx.store.add_unit('web', f'https://a.test/x{i}'), f'# X{i}\n\nU{i}\n'
        )
    assert web_run.strip_host_boilerplate(ctx.store) == 1
    assert banner not in ctx.store.read_markdown(late)


PG_NAV = (
    '| [Prev](https://x.test/a "A") | [Up](https://x.test/u "U") | Cmds '
    '| [Home](https://x.test/ "H") | [Next](https://x.test/b "B") |'
)


def pg_page(title: str, *, banner: str = '') -> str:
    return (
        f'| {title:<20} | | | | |\n| {"-" * 20} | --- | --- | --- | --- |\n'
        f'{PG_NAV}\n\n---\n\n{banner}## {title}\n\n'
        f'Body text of {title} explaining {title}.\n\n'
        f'```\n{title} --flag\n```\n\nMore about {title}.\n\n---\n\n'
        f'- PREV [Home](https://x.test/ "H") NEXT\n'
    )


def test_strip_nav_removes_prev_up_home_tables_and_bars_at_page_edges() -> None:
    out = extract.strip_nav(pg_page('psql'))
    assert out.startswith('## psql\n')
    assert 'Prev' not in out
    assert '| psql' not in out
    assert 'Home' not in out
    assert out.rstrip().endswith('More about psql.')
    assert '```\npsql --flag\n```' in out
    assert extract.strip_nav(out) == out


def test_strip_nav_removes_link_only_bar_above_the_author_footer() -> None:
    bar = (
        '[Previous page](https://x.test/a "P")[](https://x.test/a "P")'
        '[Next page](https://x.test/b "N")'
    )
    md = '# T\n\n' + '\n\n'.join(f'Paragraph {i}.' for i in range(6))
    md += f'\n\n{bar}\n\n## About the Author\n\nShort bio.\n'
    out = extract.strip_nav(md)
    assert 'Previous page' not in out
    assert 'Short bio.' in out
    assert 'Paragraph 5.' in out


def test_strip_nav_removes_a_bar_whose_chapter_titles_are_long() -> None:
    bar = (
        '- 7.2. Table Expressions [Home](https://x.test/ "Docs") '
        '7.4. Combining Queries (`UNION`, `INTERSECT`, `EXCEPT`)'
    )
    md = (
        '# T\n\n'
        + '\n\n'.join(f'Paragraph {i}.' for i in range(6))
        + f'\n\n---\n\n{bar}\n'
    )
    out = extract.strip_nav(md)
    assert 'Home' not in out
    assert out.rstrip().endswith('Paragraph 5.')


def test_strip_nav_keeps_data_tables_and_single_word_mentions() -> None:
    table = '| Option | Meaning |\n| --- | --- |\n| next | [Next](https://x.test/n) |\n'
    md = f'# Opts\n\n{table}\nGo [home](https://x.test/) whenever you like, read on.\n'
    assert extract.strip_nav(md) == md


def test_linked_banner_on_a_few_pages_is_boilerplate_but_plain_repeats_are_not() -> None:
    banner = 'September 24, 2026: [Beta 4 Released!](https://x.test/news/1)'
    plain = 'The scripts here are ready to run and were tested on MySQL.'
    docs = {i: f'# T{i}\n\nBody {i} of the page.\n' for i in range(60)}
    for i in range(4):
        docs[i] = f'{banner}\n\n{docs[i]}'
        docs[10 + i] = f'{plain}\n\n{docs[10 + i]}'
    for i in range(2):
        docs[20 + i] = f'[Two page link](https://x.test/two)\n\n{docs[20 + i]}'
    out = strip_repeated_lines(docs)
    assert all(banner not in out[i] for i in range(4))
    assert all(plain in docs[10 + i] and 10 + i not in out for i in range(4))
    assert 20 not in out


def test_strip_host_boilerplate_takes_nav_tables_and_banners_and_is_idempotent(
    ctx: Ctx,
) -> None:
    banner = (
        'September 24, 2026: [PostgreSQL 19 Beta 4 Released!](https://x.test/n/1)\n\n'
    )
    ids = []
    for i in range(30):
        uid = ctx.store.add_unit('web', f'https://x.test/docs/p{i}')
        ctx.store.finish(uid, pg_page(f'Page{i}', banner=banner if i < 3 else ''))
        ids.append(uid)
    before = ctx.store.token_total()
    assert web_run.strip_host_boilerplate(ctx.store) == 30
    docs = [ctx.store.read_markdown(uid) for uid in ids]
    assert all(d.startswith('## Page') for d in docs)
    assert not any('Prev' in d or 'Beta 4' in d for d in docs)
    assert ctx.store.token_total() < before
    assert web_run.strip_host_boilerplate(ctx.store) == 0


def test_crawl_stops_before_the_token_budget_is_passed(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    names = [f'p{i}' for i in range(12)]
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/llms.txt',
        '# D\n\n' + ''.join(f'- [{n}]({{BASE}}/docs/{n}.html)\n' for n in names),
    )
    for name in names:
        site.html(
            f'/docs/{name}.html',
            page(name, ''.join(para(f'{name}{k}') for k in range(6))),
        )
    site.html('/docs/', page('Home', para('home')))
    seed(ctx, site.url + '/docs/')
    ctx.effort = 'quick'
    monkeypatch.setitem(EFFORT_BUDGET, 'quick', 1500)
    crawl(ctx, '--workers', '4')
    total = ctx.store.token_total()
    assert 0 < total <= 1500
    assert len(ctx.store.units(source='web', status='pending')) > 0


def big_dropped_page(ctx: Ctx, tokens_of: str = 'word ') -> int:
    uid = ctx.store.add_unit('web', 'https://elsewhere.test/big')
    ctx.store.finish(uid, tokens_of * 3000)
    return uid


def budget_site(site: Site) -> None:
    names = [f'p{i}' for i in range(6)]
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/llms.txt',
        '# D\n\n' + ''.join(f'- [{n}]({{BASE}}/docs/{n}.html)\n' for n in names),
    )
    for name in names:
        site.html(f'/docs/{name}.html', page(name, para(name)))
    site.html('/docs/', page('Home', para('home')))


def test_dropped_pages_do_not_count_against_the_crawl_budget(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: 55k of 190k stored tokens were user-dropped pages, yet they stopped the
    crawl at the 200k standard budget with 1239 pages still pending."""
    budget_site(site)
    monkeypatch.setitem(EFFORT_BUDGET, 'standard', 3000)
    dropped = big_dropped_page(ctx)
    assert ctx.store.token_total() > 3000
    seed(ctx, site.url + '/docs/')
    assert crawl(ctx).done == 0
    ctx.store.set_meta('dropped_units', {str(dropped): 'off-goal'})
    assert crawl(ctx, '--workers', '1').done > 0


def test_judge_drops_do_not_count_against_the_crawl_budget(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    budget_site(site)
    monkeypatch.setitem(EFFORT_BUDGET, 'standard', 3000)
    dropped = big_dropped_page(ctx)
    ctx.ws.judge_path.write_text(json.dumps({'drop': [{'id': dropped, 'reason': 'x'}]}))
    seed(ctx, site.url + '/docs/')
    assert crawl(ctx, '--workers', '1').done > 0
    ctx.ws.judge_path.write_text(
        json.dumps({'annotate_only': True, 'drop': [{'id': dropped, 'reason': 'x'}]})
    )
    assert ctx.dropped_ids() == set()


# --- frontier ---------------------------------------------------------------------


def test_rules_scorer_prefers_keyword_scope_and_docs() -> None:
    scorer = frontier.RulesScorer('postgres indexing performance', '/docs/')
    links = [
        frontier.Link('http://x/docs/indexing-performance.html', 'Indexing'),
        frontier.Link('http://x/docs/misc.html', 'Misc'),
        frontier.Link('http://x/blog/indexing.html', 'Indexing'),
        frontier.Link('http://x/docs/logo.png', 'Indexing'),
    ]
    good, plain, out_of_scope, image = scorer.score('', '', '', links)
    assert good > plain
    assert good > out_of_scope
    assert image == 0.0
    assert all(0.0 <= s <= 1.0 for s in (good, plain, out_of_scope))


def test_rules_scorer_ranks_site_chrome_behind_content() -> None:
    scorer = frontier.RulesScorer('postgres indexing performance')
    paths = ['contact', 'privacy-policy', 'shop/cart', 'tag/sql', 'author/jane', 'about']
    chrome = scorer.score('', '', '', [frontier.Link(f'http://x/{p}') for p in paths])
    content = scorer.score('', '', '', [frontier.Link('http://x/docs/tutorial/basics')])[
        0
    ]
    assert all(c < content for c in chrome)
    assert all(0.0 <= c <= 1.0 for c in chrome)


def test_rules_scorer_keeps_chrome_paths_the_goal_asks_for() -> None:
    scorer = frontier.RulesScorer('privacy policy design')
    asked, other = scorer.score(
        '', '', '', [frontier.Link('http://x/privacy'), frontier.Link('http://x/contact')]
    )
    assert asked > other


def test_rules_scorer_weighs_goal_terms_by_rarity_and_stems_plurals() -> None:
    """A term in most candidate URLs ('sql' on a SQL docs site) must not decide the order;
    the rare terms do, and 'indexing' meets 'indexes'."""
    scorer = frontier.RulesScorer('psql SQL indexing query performance', '/docs/')
    names = [f'sql-cmd{i}' for i in range(40)]
    names += ['performance-tips', 'indexes-types', 'psql-tricks', 'unrelated-page']
    links = [frontier.Link(f'http://x/docs/{n}.html') for n in names]
    by_name = dict(zip(names, scorer.score('', '', '', links), strict=True))
    common = by_name['sql-cmd0']
    assert len({by_name[n] for n in names[:40]}) == 1
    assert by_name['performance-tips'] > common
    assert by_name['indexes-types'] > common
    assert by_name['psql-tricks'] > common
    assert common > by_name['unrelated-page']


def test_extract_links_absolute_deduped_with_heading_context() -> None:
    html = (
        '<h2>Tuning</h2><a href="/docs/a.html#top">Tune <b>a</b></a>'
        '<a href="/docs/a.html#other">again</a><a href="mailto:x@y.z">mail</a>'
        '<h2>Backup</h2><a href="b.html">Backup</a>'
    )
    links = frontier.extract_links(html, 'http://x/docs/index.html')
    assert [(link.url, link.anchor, link.heading) for link in links] == [
        ('http://x/docs/a.html', 'Tune a', 'Tuning'),
        ('http://x/docs/b.html', 'Backup', 'Backup'),
    ]


def test_extract_links_keeps_the_named_anchor_over_the_nav_bar_one() -> None:
    """Regression: first-wins scored a page's link to its next chapter as 'Next' (nav bar)
    and lost 'Using EXPLAIN' (contents)."""
    html = (
        '<a href="/d/using-explain.html">Next</a>'
        '<ul><li><a href="/d/using-explain.html">14.1. Using EXPLAIN</a></li></ul>'
    )
    (link,) = frontier.extract_links(html, 'http://x/d/performance-tips.html')
    assert link.anchor == '14.1. Using EXPLAIN'


def test_rules_hits_are_the_idf_weighted_share_of_goal_terms_present() -> None:
    scorer = frontier.RulesScorer('psql indexing performance', '/docs/')
    names = [f'sql-cmd{i}' for i in range(30)] + ['performance-tips', 'indexes-tuning']
    links = [frontier.Link(f'http://x/docs/{n}.html') for n in names]
    links.append(frontier.Link('http://x/docs/using-explain.html', '14.1 Indexing'))
    hits = scorer.hits('', links)
    assert hits[0] == 0.0
    assert all(0 < h <= 1 for h in hits[-3:])
    assert hits[-1] == pytest.approx(hits[-2])
    assert hits[-1] != pytest.approx(hits[-3])


def test_make_scorer_rules_and_laya_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    logs: list[str] = []
    assert isinstance(
        frontier.make_scorer('g', 'rules', None, logs.append), frontier.RulesScorer
    )

    def missing(_name: str) -> None:
        raise ImportError('no laya')

    monkeypatch.setattr(frontier.importlib, 'import_module', missing)
    scorer = frontier.make_scorer('sql indexing', 'laya', '/docs/', logs.append)
    assert isinstance(scorer, frontier.RulesScorer)
    assert 'unavailable' in logs[-1]

    class Broken:
        def __init__(self, _goal: str) -> None:
            pass

        def score(self, *_a: object) -> list[float]:
            raise RuntimeError('model exploded')

    monkeypatch.setattr(
        frontier.importlib, 'import_module', lambda _n: SimpleNamespace(LayaScorer=Broken)
    )
    logs.clear()
    guarded = frontier.make_scorer('sql indexing', 'laya', '/docs/', logs.append)
    links = [frontier.Link('http://x/docs/sql-indexing.html')]
    first = guarded.score('sql indexing', '', '', links)
    guarded.score('sql indexing', '', '', links)
    assert first[0] > 0
    assert len(logs) == 1
    assert 'failed' in logs[0]


# --- fetch --------------------------------------------------------------------------


def test_fetch_sends_negotiation_and_chrome_headers_only(site: Site) -> None:
    site.html('/a', '<p>hi</p>')
    site.html('/b', '<p>hi</p>')
    res = run_async(
        fetch.fetch(
            site.url + '/a',
            'W/"v1"',
            'Wed, 01 Jan 2025 00:00:00 GMT',
            referer=site.url + '/b',
            allow_private=True,
        )
    )
    headers = site.hits[0][1]
    assert res.status == 200
    assert headers['accept'] == 'text/markdown, text/html;q=0.8'
    assert headers['accept-language'].startswith('en')
    assert 'Chrome/' in headers['user-agent']
    assert 'sec-ch-ua' in headers
    assert headers['referer'] == site.url + '/b'
    assert headers['sec-fetch-site'] == 'same-origin'
    assert headers['if-none-match'] == 'W/"v1"'
    assert headers['if-modified-since'] == 'Wed, 01 Jan 2025 00:00:00 GMT'


def test_fetch_304_has_no_body_and_redirects_are_followed(site: Site) -> None:
    site.routes['/cached'] = (304, {'ETag': '"e1"'}, '')
    site.routes['/old'] = (301, {'Location': '/new'}, '')
    site.html('/new', '<p>fresh</p>')
    cached = run_async(
        fetch.fetch(site.url + '/cached', '"e1"', None, allow_private=True)
    )
    moved = run_async(fetch.fetch(site.url + '/old', None, None, allow_private=True))
    assert (cached.status, cached.body) == (304, '')
    assert moved.url == site.url + '/new'
    assert moved.history == [site.url + '/old']
    assert '<p>fresh</p>' in moved.body


def test_fetch_denies_private_hosts_without_allow_private(site: Site) -> None:
    site.html('/a', 'x')
    with pytest.raises(SSRFError):
        run_async(fetch.fetch(site.url + '/a', None, None))
    assert site.hits == []


def test_every_redirect_hop_is_vetted_before_it_is_requested(
    site: Site, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.routes['/start'] = (302, {'Location': '/internal'}, '')
    site.html('/internal', 'secret')

    def deny_internal(url: str, **_kw: object) -> str:
        if '/internal' in url:
            raise SSRFError('private')
        return url

    monkeypatch.setattr(fetch, 'check_url', deny_internal)
    with pytest.raises(SSRFError):
        run_async(fetch.fetch(site.url + '/start', None, None))
    assert site.hit_paths() == ['/start']


@pytest.mark.parametrize('status', [429, 503])
def test_fetch_retries_throttled_responses_after_retry_after(
    site: Site, status: int
) -> None:
    site.routes['/a'] = [(status, {'Retry-After': '1'}, ''), (200, {}, 'ok')]
    events: list = []
    net = make_net(events=events)
    started = time.monotonic()
    res = run_async(net.get(site.url + '/a'))
    assert (res.status, res.body) == (200, 'ok')
    assert time.monotonic() - started >= 1.0
    assert [e[1] for e in events] == ['backoff']
    assert site.hit_paths().count('/a') == 2


def test_fetch_returns_the_throttled_response_when_retries_run_out(site: Site) -> None:
    site.routes['/a'] = (429, {}, '')
    res = run_async(make_net().get(site.url + '/a'))
    assert res.status == 429
    assert site.hit_paths().count('/a') == fetch.RETRIES


def test_fetch_wraps_network_errors() -> None:
    with pytest.raises(fetch.FetchError):
        run_async(fetch.fetch('http://127.0.0.1:1/', None, None, allow_private=True))


def test_net_honors_robots_including_after_redirects(site: Site) -> None:
    site.text('/robots.txt', 'User-agent: *\nDisallow: /private/\nCrawl-delay: 1\n')
    site.html('/private/x.html', 'x')
    site.routes['/go'] = (302, {'Location': '/private/x.html'}, '')
    net = make_net()
    with pytest.raises(fetch.RobotsDisallowedError):
        run_async(net.get(site.url + '/private/x.html'))
    with pytest.raises(fetch.RobotsDisallowedError):
        run_async(net.get(site.url + '/go'))
    assert '/private/x.html' not in site.hit_paths()
    assert net.throttle.host(site.url.split('//')[1]).crawl_delay == 1.0


# --- discovery ----------------------------------------------------------------------


def test_normalize_scope_and_in_scope() -> None:
    assert (
        discover.normalize_scope('http://h/docs/current/app.html', None)
        == '/docs/current/'
    )
    assert discover.normalize_scope('http://h/', None) == '/'
    assert discover.normalize_scope('http://h/docs', 'guide') == '/guide'
    assert discover.normalize_scope('http://h/x', 'http://h/docs/') == '/docs/'
    assert discover.in_scope('http://H/docs/a.html', 'h', '/docs/')
    assert not discover.in_scope('http://h/blog/a.html', 'h', '/docs/')
    assert not discover.in_scope('http://other/docs/a.html', 'h', '/docs/')
    assert not discover.in_scope('http://h/docs/a.png', 'h', '/docs/')


def test_parse_sitemap_index_urlset_and_hostile_xml() -> None:
    pages, children = discover.parse_sitemap(fixture_text('sitemap_index.xml'))
    assert pages == []
    assert children == ['{BASE}/sitemap_docs.xml', '{BASE}/sitemap_more.xml']
    pages, children = discover.parse_sitemap(fixture_text('sitemap_docs.xml'))
    assert len(pages) == FIVE
    assert children == []
    bomb = (
        '<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaa">]>'
        '<urlset><url><loc>&a;</loc></url></urlset>'
    )
    assert discover.parse_sitemap(bomb) == ([], [])
    assert discover.parse_sitemap('not xml') == ([], [])


def test_llms_txt_discovery_scope_priority_and_seed_retyped(site: Site, ctx: Ctx) -> None:
    site.text('/llms.txt', fixture_text('llms.txt'))
    seed(ctx, site.url + '/docs/')
    added = run_async(discover.discover(ctx, site.url + '/docs/', None, make_net()))
    units = {u.uri.replace(site.url, ''): u for u in ctx.store.units(source='web')}
    assert added == 2
    assert set(units) == {'/docs/', '/docs/start.html', '/docs/indexing.md'}
    assert units['/docs/start.html'].hint == {'llms': True, 'group': 'Guides'}
    assert units['/docs/start.html'].priority > units['/docs/indexing.md'].priority >= 50
    assert units['/docs/'].kind == 'page'
    assert units['/docs/'].status == 'pending'
    assert ctx.store.get_meta('web.scopes') == [[site.url, '/docs/', 'llms']]


def urlset(*locs: str, extra: str = '') -> str:
    body = ''.join(f'<url><loc>{{BASE}}{loc}</loc>{extra}</url>' for loc in locs)
    return (
        '<?xml version="1.0"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{body}</urlset>'
    )


def test_sitemap_seeds_share_the_crawl_by_rank_not_by_score(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    pg = [f'/pg/page{i}.html' for i in range(8)] + ['/pg/indexing.html']
    luke = [f'/luke/indexing-{i}.html' for i in range(8)]
    site.text('/sitemap.xml', urlset(*pg, *luke), 'application/xml')
    for base, scope in ((site.url + '/pg/', '/pg/'), (site.url + '/luke/', '/luke/')):
        seed(ctx, base, scope)
        run_async(discover.discover(ctx, base, scope, make_net()))
    queue = [
        u
        for u in sorted(ctx.store.units(source='web'), key=lambda u: -u.priority)
        if u.hint.get('sitemap')
    ]
    top = [u.uri.replace(site.url, '').split('/')[1] for u in queue[:8]]
    assert top.count('pg') == top.count('luke') == 4
    assert queue[0].uri.endswith('/pg/indexing.html') or queue[0].uri.endswith(
        '/luke/indexing-0.html'
    )
    assert (
        unit_at(ctx, site.url + '/pg/indexing.html').priority
        > unit_at(ctx, site.url + '/pg/page7.html').priority
    )


def test_sitemap_ranking_prefers_pages_near_the_seed_page(site: Site, ctx: Ctx) -> None:
    ctx.goal = 'unrelated words'
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/sitemap.xml',
        urlset('/d/zzz.html', '/d/app-pgdump.html', '/d/app-psql.html', '/d/yyy.html'),
        'application/xml',
    )
    seed(ctx, site.url + '/d/app-psql.html', '/d/')
    run_async(discover.discover(ctx, site.url + '/d/app-psql.html', '/d/', make_net()))
    by_priority = sorted(
        (u for u in ctx.store.units(source='web') if u.hint.get('sitemap')),
        key=lambda u: -u.priority,
    )
    assert by_priority[0].uri.endswith('/d/app-pgdump.html')


def test_sitemap_ranking_puts_rare_goal_terms_before_the_ubiquitous_one(
    site: Site, ctx: Ctx
) -> None:
    """Regression: with 'sql' in most URLs and the seed on psql, the order was the sql-*
    pages and seed-neighbours while performance-tips was never reached."""
    ctx.goal = 'best practices for psql, SQL, indexing and query performance'
    site.text('/robots.txt', PLAIN_ROBOTS)
    sql_pages = [f'/d/sql-{n}.html' for n in 'abcdefghijklmnopqrstuvwxyz']
    site.text(
        '/sitemap.xml',
        urlset(
            *sql_pages,
            '/d/psql-tricks.html',
            '/d/app-psql.html',
            '/d/performance-tips.html',
            '/d/indexes-types.html',
            '/d/zzz-other.html',
        ),
        'application/xml',
    )
    seed(ctx, site.url + '/d/app-psql.html', '/d/')
    run_async(discover.discover(ctx, site.url + '/d/app-psql.html', '/d/', make_net()))
    ranked = [
        u.uri.rsplit('/', 1)[-1]
        for u in sorted(ctx.store.units(source='web'), key=lambda u: -u.priority)
        if u.hint.get('sitemap')
    ]
    assert set(ranked[:3]) == {
        'performance-tips.html',
        'indexes-types.html',
        'psql-tricks.html',
    }
    assert ranked.index('zzz-other.html') > ranked.index('sql-z.html')


def test_crawl_brain_reranks_pending_sitemap_pages_ranked_by_rules(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: discover-only ran with rules, and the later --brain laya crawl found no
    pending seed, so Laya never ranked anything and web.sitemap_rank was never written."""
    monkeypatch.setattr(discover, 'make_scorer', lambda *_a, **_k: BoostZzz())
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/sitemap.xml',
        urlset('/d/indexing.html', '/d/o.html', '/d/zzz.html'),
        'application/xml',
    )
    seed(ctx, site.url + '/d/', '/d/')
    crawl(ctx, '--discover-only')
    assert ctx.store.get_meta('web.ranked_by') == {site.url + '/d/': 'rules'}
    assert ctx.store.get_meta('web.sitemap_rank') is None
    assert (
        unit_at(ctx, site.url + '/d/o.html').priority
        > unit_at(ctx, site.url + '/d/zzz.html').priority
    )
    crawl(ctx, '--discover-only', '--brain', 'laya')
    assert ctx.store.get_meta('web.ranked_by') == {site.url + '/d/': 'laya'}
    assert site.url + '/d/' in ctx.store.get_meta('web.sitemap_rank')
    assert (
        unit_at(ctx, site.url + '/d/zzz.html').priority
        > unit_at(ctx, site.url + '/d/o.html').priority
    )


def test_sitemap_drops_other_locales_by_path_and_hreflang(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    alt = (
        '<xhtml:link rel="alternate" hreflang="fr" href="{BASE}/docs/fr-only.html"/>'
        '<xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/docs/a.html"/>'
    )
    xml = urlset('/docs/a.html', '/docs/b.html', '/docs/fr-only.html', '/de/docs/a.html')
    xml = xml.replace(
        '<url><loc>{BASE}/docs/a.html</loc>', f'<url><loc>{{BASE}}/docs/a.html</loc>{alt}'
    )
    site.text('/sitemap.xml', xml, 'application/xml')
    seed(ctx, site.url + '/docs/a.html', '/')
    added = run_async(discover.discover(ctx, site.url + '/docs/a.html', '/', make_net()))
    uris = {u.uri.replace(site.url, '') for u in ctx.store.units(source='web')}
    assert uris == {'/docs/a.html', '/docs/b.html'}
    assert added == 1
    assert ctx.store.get_meta('web.locale_skipped') == {site.url + '/docs/a.html': 2}


def test_locale_detection() -> None:
    assert discover.locale_of('https://x.test/de/sql/a') == 'de'
    assert discover.locale_of('https://x.test/docs/pt-BR/a') == 'pt-br'
    assert discover.locale_of('https://x.test/docs/go/a') is None
    assert discover.locale_of('https://x.test/sql/anatomy') is None
    assert discover.same_locale('https://x.test/en/a', 'https://x.test/a')
    assert not discover.same_locale('https://x.test/ja/a', 'https://x.test/a')
    assert discover.same_locale('https://x.test/ja/b', 'https://x.test/ja/a')


class BoostZzz:
    def score(self, _goal: str, _title: str, _heading: str, cands: list) -> list[float]:
        return [1.0 if 'zzz' in c.url else 0.0 for c in cands]


def by_priority(ctx: Ctx, site: Site) -> list[str]:
    return [
        u.uri.replace(site.url + '/d/', '').removesuffix('.html')
        for u in sorted(ctx.store.units(source='web'), key=lambda u: -u.priority)
        if u.hint.get('sitemap')
    ]


def test_brain_laya_breaks_rules_ties_but_cannot_outweigh_a_rules_lead(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: Laya's score was added to the rules score, so its 0.94 for an off-goal
    page outweighed rules' whole spread and buried the pages that matched the goal."""
    monkeypatch.setattr(discover, 'make_scorer', lambda *_a, **_k: BoostZzz())
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/sitemap.xml',
        urlset('/d/indexing.html', '/d/aaa.html', '/d/zzz.html', '/d/o.html'),
        'application/xml',
    )
    seed(ctx, site.url + '/d/', '/d/')
    run_async(discover.discover(ctx, site.url + '/d/', '/d/', make_net(), 'laya'))
    assert by_priority(ctx, site) == ['indexing', 'zzz', 'aaa', 'o']


def test_brain_laya_only_reorders_the_rules_shortlist_and_logs_overlap_only(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(discover, 'make_scorer', lambda *_a, **_k: BoostZzz())
    monkeypatch.setattr(discover, 'LAYA_SHORTLIST', 2)
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/sitemap.xml',
        urlset('/d/indexing.html', '/d/aaa.html', '/d/o.html', '/d/zzz.html'),
        'application/xml',
    )
    seed(ctx, site.url + '/d/', '/d/')
    run_async(discover.discover(ctx, site.url + '/d/', '/d/', make_net(), 'laya'))
    assert by_priority(ctx, site)[2:] == ['o', 'zzz']
    log = ctx.store.get_meta('web.sitemap_rank')[site.url + '/d/']
    assert log == {'n': discover.RANK_N, 'candidates': 4, 'shortlist': 2, 'overlap': 0.4}


def test_llms_txt_falls_back_to_well_known_and_ignores_html_soft_404(
    site: Site, ctx: Ctx
) -> None:
    site.html('/llms.txt', '<html>spa index</html>')
    site.text('/.well-known/llms.txt', fixture_text('llms.txt'))
    seed(ctx, site.url + '/docs/')
    added = run_async(discover.discover(ctx, site.url + '/docs/', '/docs/', make_net()))
    assert added == 2
    assert '/.well-known/llms.txt' in site.hit_paths()


def test_sitemap_index_via_robots_scope_filtered(site: Site, ctx: Ctx) -> None:
    sitemap_site(site)
    seed(ctx, site.url + '/docs/start.html')
    added = run_async(
        discover.discover(ctx, site.url + '/docs/start.html', '/docs/', make_net())
    )
    uris = {u.uri.replace(site.url, '') for u in ctx.store.units(source='web')}
    assert uris == {
        '/docs/start.html',
        '/docs/indexing.html',
        '/docs/tuning.html',
        '/docs/backup.html',
    }
    assert added == 3
    assert all(
        u.hint.get('sitemap')
        for u in ctx.store.units(source='web')
        if u.kind == 'page' and u.uri.endswith('tuning.html')
    )
    assert ctx.store.get_meta('web.scopes')[0][2] == 'sitemap'
    assert unit_at(ctx, site.url + '/docs/start.html').kind == 'page'


def test_default_sitemap_xml_used_when_robots_lists_none(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text('/sitemap.xml', fixture_text('sitemap_docs.xml'), 'application/xml')
    seed(ctx, site.url + '/')
    added = run_async(discover.discover(ctx, site.url + '/', None, make_net()))
    assert added >= 4


def test_bfs_fallback_when_nothing_is_published(site: Site, ctx: Ctx) -> None:
    seed(ctx, site.url + '/docs/')
    added = run_async(discover.discover(ctx, site.url + '/docs/', None, make_net()))
    assert added == 0
    assert ctx.store.get_meta('web.scopes') == [[site.url, '/docs/', 'bfs']]
    unit = unit_at(ctx, site.url + '/docs/')
    assert (unit.kind, unit.status) == ('page', 'pending')


def test_discover_rejects_private_seed(ctx: Ctx) -> None:
    seed(ctx, 'http://127.0.0.1:9/docs/')
    with pytest.raises(SSRFError):
        run_async(
            discover.discover(
                ctx, 'http://127.0.0.1:9/docs/', None, make_net(allow_private=False)
            )
        )


# --- end to end ---------------------------------------------------------------------


def sitemap_site(site: Site) -> None:
    site.text('/robots.txt', SITEMAP_ROBOTS)
    for name in ('sitemap_index.xml', 'sitemap_docs.xml', 'sitemap_more.xml'):
        site.text('/' + name, fixture_text(name), 'application/xml')


def docs_site(site: Site) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text('/llms.txt', fixture_text('llms.txt'))
    site.html('/docs/', page('Docs home', links=('/docs/start.html',)))
    site.html('/docs/start.html', page('Getting started', para('Bootstrapping')))
    site.routes['/docs/indexing.md'] = (
        200,
        {'Content-Type': 'text/markdown; charset=utf-8'},
        '# Indexing guide\n\nUse `CREATE INDEX` on selective columns.\n',
    )


def test_llms_site_end_to_end_with_markdown_negotiation(site: Site, ctx: Ctx) -> None:
    docs_site(site)
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    assert (summary.done, summary.failed, summary.blocked) == (3, 0, 0)
    by_path = {u.uri.replace(site.url, ''): u for u in ctx.store.units(source='web')}
    assert {u.status for u in by_path.values()} == {'done'}
    md = ctx.store.read_markdown(by_path['/docs/indexing.md'].id)
    assert md.startswith('# Indexing guide')
    assert by_path['/docs/indexing.md'].title == 'Indexing guide'
    assert by_path['/docs/indexing.md'].meta['content_type'] == 'text/markdown'
    start = by_path['/docs/start.html']
    assert start.title == 'Getting started'
    assert 'Bootstrapping' in ctx.store.read_markdown(start.id)
    assert start.tokens > 0
    assert '/blog/post.html' not in by_path


def test_other_4xx_and_empty_pages_are_skipped_with_a_reason(
    site: Site, ctx: Ctx
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/docs/', page('Docs home', links=('/docs/teapot', '/docs/empty')))
    site.routes['/docs/teapot'] = (418, {}, 'short and stout')
    site.html('/docs/empty', '<html><body><main></main></body></html>')
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    assert summary.skipped == 2
    reasons = {u.uri.rsplit('/', 1)[-1]: u.error for u in ctx.store.units(source='web')}
    assert reasons['teapot'] == 'HTTP 418'
    assert reasons['empty'] == 'no extractable content'


def test_a_page_that_keeps_failing_ends_as_failed(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store_module, 'BACKOFF_BASE_S', 0)
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/docs/', page('Docs home', links=('/docs/flaky',)))
    site.routes['/docs/flaky'] = (503, {}, 'down')
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    assert summary.failed == 1
    flaky = unit_at(ctx, site.url + '/docs/flaky')
    assert (flaky.status, flaky.attempts) == ('failed', store_module.MAX_ATTEMPTS)
    assert any('HTTP 503' in e for e in summary.errors)


def test_malformed_href_does_not_abort_the_crawl(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/docs/', page('Docs home', links=('//[oops', '/docs/start.html')))
    site.html('/docs/start.html', page('Getting started'))
    seed(ctx, site.url + '/docs/')
    assert crawl(ctx).done == 2


def test_unexpected_error_on_a_page_is_recorded_not_fatal(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs_site(site)

    async def boom(*_args: object) -> None:
        raise ValueError('boom')

    monkeypatch.setattr(web_run._Crawl, 'content', boom)  # noqa: SLF001
    monkeypatch.setattr(web_run, 'MAX_IDLE_WAIT_S', 0.0)
    seed(ctx, site.url + '/docs/')
    crawl(ctx)
    failing = unit_at(ctx, site.url + '/docs/')
    assert failing.status != 'running'
    assert failing.error is not None
    assert 'ValueError: boom' in failing.error


def test_discovery_drops_malformed_urls_instead_of_crashing(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/llms.txt',
        '# D\n\n- [bad](http://[oops/x)\n- [ok]({BASE}/docs/ok.html)\n',
    )
    seed(ctx, site.url + '/docs/')
    added = run_async(discover.discover(ctx, site.url + '/docs/', None, make_net()))
    assert added == 1
    assert not discover.in_scope('http://[oops/x', '127.0.0.1', '/')
    assert discover.normalize('http://[oops/x') == ''


def test_throttled_page_is_retried_and_events_reach_status_json(
    site: Site, ctx: Ctx, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_site(site)
    site.routes['/docs/start.html'] = [
        (429, {'Retry-After': '1'}, ''),
        (
            200,
            {'Content-Type': 'text/html'},
            page('Getting started', para('Bootstrapping')),
        ),
    ]
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    assert summary.done == 3
    assert (
        cli.main(['status', '--json', '--slug', 't', '--base', str(ctx.ws.dir.parent)])
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    host = site.url.split('//')[1]
    assert report['throttle']['per_host'][host]['backoff'] == 1
    assert report['throttle']['events'][0]['status'] == 429


def test_robots_disallow_marks_units_skipped_without_fetching(
    site: Site, ctx: Ctx
) -> None:
    site.text('/robots.txt', 'User-agent: *\nDisallow: /private/\n')
    site.text(
        '/llms.txt',
        '# Docs\n\n- [Secret]({BASE}/private/x.html)\n- [Ok]({BASE}/ok.html)\n',
    )
    site.html('/private/x.html', page('Secret', para('Secrets')))
    site.html('/ok.html', page('Fine', para('Fine things')))
    site.html('/', page('Home'))
    seed(ctx, site.url + '/')
    summary = crawl(ctx)
    private = unit_at(ctx, site.url + '/private/x.html')
    assert private.status == 'skipped'
    assert 'robots' in (private.error or '')
    assert '/private/x.html' not in site.hit_paths()
    assert summary.skipped == 1
    assert unit_at(ctx, site.url + '/ok.html').status == 'done'


def test_ssrf_denied_seed_is_skipped_and_nothing_is_requested(
    site: Site, ctx: Ctx
) -> None:
    ctx.allow_private = False
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    unit = unit_at(ctx, site.url + '/docs/')
    assert (unit.status, summary.skipped) == ('skipped', 1)
    assert 'ssrf' in (unit.error or '')
    assert site.hits == []


def test_js_shell_without_browser_becomes_needs_js(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/app', fixture_text('js_shell.html'))
    seed(ctx, site.url + '/app')
    summary = crawl(ctx)
    assert (summary.needs_js, summary.done) == (1, 0)
    assert unit_at(ctx, site.url + '/app').status == 'needs_js'


def test_js_shell_uses_the_browser_when_available(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/app', fixture_text('js_shell.html'))
    seen: list[str] = []
    monkeypatch.setattr(
        browser,
        'render',
        lambda url: seen.append(url) or ('# Rendered\n\n' + 'body ' * 60, url),
    )
    seed(ctx, site.url + '/app')
    summary = crawl(ctx)
    assert summary.done == 1
    assert seen == [site.url + '/app']
    assert ctx.store.read_markdown(unit_at(ctx, site.url + '/app').id).startswith(
        '# Rendered'
    )


def test_403_and_challenge_pages_try_the_browser_but_login_walls_do_not(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/llms.txt',
        '# D\n\n- [a]({BASE}/a.html)\n- [b]({BASE}/b.html)\n- [c]({BASE}/c.html)\n',
    )
    site.html('/a.html', fixture_text('blocked.html'))
    site.routes['/b.html'] = (403, {}, 'forbidden')
    site.routes['/c.html'] = (401, {}, 'login required')
    site.html('/', page('Home'))
    calls: list[str] = []
    monkeypatch.setattr(browser, 'render', lambda url: calls.append(url))
    seed(ctx, site.url + '/')
    summary = crawl(ctx)
    assert summary.blocked == 3
    assert {
        u.status for u in ctx.store.units(source='web') if u.uri.endswith('.html')
    } == {'blocked'}
    assert sorted(calls) == [site.url + '/a.html', site.url + '/b.html']


def test_403_that_renders_in_the_browser_is_kept(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.routes['/walled'] = (403, {}, 'forbidden')
    monkeypatch.setattr(browser, 'render', lambda url: ('# Real\n\n' + 'body ' * 60, url))
    seed(ctx, site.url + '/walled')
    assert crawl(ctx).done == 1
    assert unit_at(ctx, site.url + '/walled').status == 'done'


def test_no_browser_keeps_a_403_blocked(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.routes['/walled'] = (403, {}, 'forbidden')
    calls: list[str] = []
    monkeypatch.setattr(browser, 'render', lambda url: calls.append(url))
    seed(ctx, site.url + '/walled')
    assert crawl(ctx, '--no-browser').blocked == 1
    assert calls == []


def test_challenge_in_the_browser_is_blocked(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/app', fixture_text('js_shell.html'))

    def refuse(_url: str) -> None:
        raise browser.BrowserBlockedError

    monkeypatch.setattr(browser, 'render', refuse)
    seed(ctx, site.url + '/app')
    assert crawl(ctx).blocked == 1
    assert unit_at(ctx, site.url + '/app').status == 'blocked'


def test_browser_result_that_ended_off_limits_is_dropped(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', 'User-agent: *\nDisallow: /private/\n')
    site.html('/app', fixture_text('js_shell.html'))
    monkeypatch.setattr(
        browser, 'render', lambda _u: ('x' * 300, site.url + '/private/page')
    )
    seed(ctx, site.url + '/app')
    assert crawl(ctx).needs_js == 1
    assert unit_at(ctx, site.url + '/app').status == 'needs_js'


def test_needs_js_units_are_retried_once_a_browser_exists(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/app', fixture_text('js_shell.html'))
    seed(ctx, site.url + '/app')
    assert crawl(ctx).needs_js == 1
    monkeypatch.setattr(browser.shutil, 'which', lambda _n: '/bin/agent-browser')
    monkeypatch.setattr(browser, 'render', lambda u: ('# R\n\n' + 'body ' * 60, u))
    assert crawl(ctx).done == 1
    assert unit_at(ctx, site.url + '/app').status == 'done'


def test_oversized_response_is_skipped(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/big', 'x' * 5000)
    monkeypatch.setattr(fetch, 'MAX_PAGE_BYTES', 1000)
    seed(ctx, site.url + '/big')
    assert crawl(ctx).skipped == 1
    assert 'over 1000 bytes' in (unit_at(ctx, site.url + '/big').error or '')


def test_bfs_crawl_stays_in_scope_and_fetches_best_first(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html(
        '/docs/',
        page(
            'Home',
            links=(
                '/docs/misc.html',
                '/docs/indexing-performance.html',
                '/blog/x.html',
                '/docs/logo.png',
            ),
        ),
    )
    site.html(
        '/docs/misc.html', page('Misc', para('Miscellany'), links=('/docs/deep.html',))
    )
    site.html(
        '/docs/indexing-performance.html', page('Indexing performance', para('Indexing'))
    )
    site.html('/docs/deep.html', page('Deep', para('Depth')))
    site.html('/blog/x.html', page('Blog', para('Blogging')))
    seed(ctx, site.url + '/docs/')
    ctx.max_pages = 2
    crawl(ctx)
    done = {p for p in statuses(ctx.store).items() if p[1] == 'done'}
    assert ('docs/', 'done') in done
    assert ('docs/indexing-performance.html', 'done') in done
    assert ('docs/misc.html', 'pending') in set(statuses(ctx.store).items())
    assert 'blog/x.html' not in statuses(ctx.store)
    assert 'docs/logo.png' not in statuses(ctx.store)
    ctx.max_pages = None
    crawl(ctx)
    final = statuses(ctx.store)
    assert final['docs/deep.html'] == 'done'
    assert set(final.values()) == {'done'}


def test_bfs_depth_limit(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/docs/', page('Home', links=('/docs/a.html',)))
    site.html('/docs/a.html', page('A', para('Alpha'), links=('/docs/b.html',)))
    site.html('/docs/b.html', page('B', para('Beta')))
    seed(ctx, site.url + '/docs/')
    crawl(ctx, '--max-depth', '1')
    assert 'docs/b.html' not in statuses(ctx.store)


def test_conditional_get_keeps_markdown_on_304(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    body = page('Stable', para('Stability'))

    def stable(headers: dict[str, str]) -> Response:
        if headers.get('if-none-match') == '"v1"':
            return 304, {'ETag': '"v1"'}, ''
        return 200, {'Content-Type': 'text/html', 'ETag': '"v1"'}, body

    site.routes['/docs/'] = stable
    seed(ctx, site.url + '/docs/')
    crawl(ctx)
    unit = unit_at(ctx, site.url + '/docs/')
    before = ctx.store.read_markdown(unit.id)
    assert unit.etag == '"v1"'
    assert ctx.store.requeue('done') == 1
    summary = crawl(ctx)
    again = unit_at(ctx, site.url + '/docs/')
    assert (summary.done, again.status) == (1, 'done')
    assert ctx.store.read_markdown(again.id) == before
    assert site.hits[-1][1]['if-none-match'] == '"v1"'


def test_discover_only_queues_pages_without_fetching_them(site: Site, ctx: Ctx) -> None:
    docs_site(site)
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx, '--discover-only')
    assert summary.done == 0
    pending = {
        u.uri.replace(site.url, '')
        for u in ctx.store.units(source='web', status='pending')
    }
    assert pending == {'/docs/', '/docs/start.html', '/docs/indexing.md'}
    assert all(not p.startswith('/docs/') for p in site.hit_paths() if p != '/docs/')


def test_crawl_fetches_a_page_linked_from_a_relevant_page_before_ranked_filler(
    site: Site, ctx: Ctx
) -> None:
    """Regression: using-explain has no goal word in its URL, so it sat behind every page
    that has one and was never fetched, though performance-tips links straight to it."""
    fillers = [f'/docs/filler-{n:02}.html' for n in range(25)]
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text(
        '/sitemap.xml',
        urlset(
            '/docs/start.html',
            '/docs/performance-tips.html',
            *fillers,
            '/docs/using-explain.html',
        ),
        'application/xml',
    )
    site.html('/docs/start.html', page('Start', links=('/docs/performance-tips.html',)))
    toc = '<ul><li><a href="/docs/using-explain.html">14.1. Using EXPLAIN</a></li></ul>'
    site.html('/docs/performance-tips.html', page('Performance Tips', toc))
    site.html('/docs/using-explain.html', page('Using EXPLAIN'))
    site.html(fillers[0], page('Filler'))
    seed(ctx, site.url + '/docs/start.html', '/docs/')
    ctx.max_pages = 3
    crawl(ctx, '--workers', '1')
    explain = unit_at(ctx, site.url + '/docs/using-explain.html')
    assert explain.status == 'done'
    assert explain.hint['anchors'] == ['14.1. Using EXPLAIN']
    assert unit_at(ctx, site.url + fillers[0]).status == 'pending'


def add_listed(
    ctx: Ctx, host: str, scope: str, n: int, key: str = 'sitemap'
) -> list[str]:
    """n pending listed pages in rank order, priorities as discovery leaves them."""
    uris = [f'http://{host}{scope}page{i:02}.html' for i in range(n)]
    for i, uri in enumerate(uris):
        ctx.store.add_unit('web', uri, priority=10 - i * 0.01, hint={key: True})
    return uris


def fetched(ctx: Ctx, uri: str) -> Unit:
    unit = unit_at(ctx, uri) if ctx.store.get_by_uri(uri) else None
    if unit is None:
        unit = ctx.store.get(ctx.store.add_unit('web', uri, hint={'sitemap': True}))
    ctx.store.mark(unit.id, 'done')
    return ctx.store.get(unit.id)


def queue(ctx: Ctx, host: str) -> list[str]:
    pending = ctx.store.units(source='web', status='pending')
    ranked = sorted(
        (u for u in pending if host in u.uri), key=lambda u: (-u.priority, u.id)
    )
    return [u.uri for u in ranked]


@pytest.mark.parametrize('key', ['sitemap', 'llms'])
def test_link_boost_promotes_linked_pages_within_their_own_seed(
    ctx: Ctx, key: str
) -> None:
    mine = add_listed(ctx, 'a.test', '/docs/', 40, key)
    other = add_listed(ctx, 'b.test', '/', 40)
    before = {u.uri: u.priority for u in ctx.store.units(source='web')}
    hub = fetched(ctx, 'http://a.test/docs/performance-tips.html')
    links = [
        frontier.Link(mine[-1], '14.1. Using EXPLAIN'),
        frontier.Link(mine[5], 'Next'),
        frontier.Link(other[3], 'Elsewhere'),
    ]
    assert discover.boost_linked(ctx, hub, 'Performance Tips', links, '/docs/') == 1
    assert queue(ctx, 'a.test')[0] == mine[-1]
    assert unit_at(ctx, mine[-1]).hint['anchors'] == ['14.1. Using EXPLAIN']
    assert 'anchors' not in unit_at(ctx, mine[5]).hint
    now = {u.uri: u.priority for u in ctx.store.units(source='web')}
    assert sorted(now[u] for u in mine) == sorted(before[u] for u in mine)
    assert {u: now[u] for u in other} == {u: before[u] for u in other}


def promoted_place(ctx: Ctx, scope: str, parent: str, n_linked: int) -> int:
    pages = add_listed(ctx, 'a.test', scope, 60)
    hub = fetched(ctx, f'http://a.test{scope}{parent}.html')
    links = [
        frontier.Link(u, f'Topic {j}') for j, u in enumerate(reversed(pages[-n_linked:]))
    ]
    discover.boost_linked(ctx, hub, parent.title(), links, scope)
    return queue(ctx, 'a.test' + scope).index(pages[-1])


def test_link_boost_scales_with_the_linking_pages_relevance_and_fan_out(ctx: Ctx) -> None:
    relevant = promoted_place(ctx, '/g/', 'indexing-performance', 3)
    irrelevant = promoted_place(ctx, '/i/', 'licence', 3)
    see_also = promoted_place(ctx, '/s/', 'indexing-performance', 30)
    assert irrelevant == 59
    assert relevant < 3
    assert relevant < see_also < irrelevant


def test_link_boost_accumulates_across_pages_and_stops_at_the_cap(ctx: Ctx) -> None:
    pages = add_listed(ctx, 'a.test', '/docs/', 60)
    target = pages[-1]
    for name in ('indexing', 'performance', 'indexing-performance'):
        hub = fetched(ctx, f'http://a.test/docs/{name}.html')
        discover.boost_linked(
            ctx, hub, name, [frontier.Link(target, 'Details')], '/docs/'
        )
    boost = unit_at(ctx, target).hint['boost']
    assert boost <= discover.MAX_BOOST
    assert queue(ctx, 'a.test')[0] == target


def test_link_boost_keeps_the_first_anchors_only(ctx: Ctx) -> None:
    (target,) = add_listed(ctx, 'a.test', '/docs/', 1)
    for n in range(discover.MAX_ANCHORS + 2):
        hub = fetched(ctx, f'http://a.test/docs/hub{n}.html')
        discover.boost_linked(
            ctx, hub, '', [frontier.Link(target, f'name {n}')], '/docs/'
        )
    assert unit_at(ctx, target).hint['anchors'] == [
        f'name {n}' for n in range(discover.MAX_ANCHORS)
    ]


def test_rerank_gives_the_scorer_the_anchors_stored_on_pending_pages(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[frontier.Link] = []

    class Recorder:
        def score(
            self, _goal: str, _title: str, _heading: str, cands: list
        ) -> list[float]:
            seen.extend(cands)
            return [0.0] * len(cands)

    monkeypatch.setattr(discover, 'make_scorer', lambda *_a, **_k: Recorder())
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text('/sitemap.xml', urlset('/d/a.html', '/d/b.html'), 'application/xml')
    seed(ctx, site.url + '/d/', '/d/')
    crawl(ctx, '--discover-only')
    explain = unit_at(ctx, site.url + '/d/a.html')
    ctx.store.set_hint(explain.id, {'sitemap': True, 'anchors': ['Using EXPLAIN']})
    crawl(ctx, '--discover-only', '--brain', 'laya')
    assert {link.url.rsplit('/', 1)[-1]: link.anchor for link in seen} == {
        'a.html': 'Using EXPLAIN',
        'b.html': '',
    }


def test_repeated_boilerplate_is_stripped_after_the_crawl(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    names = [f'p{i}' for i in range(6)]
    site.text(
        '/llms.txt',
        '# D\n\n' + ''.join(f'- [{n}]({{BASE}}/docs/{n}.html)\n' for n in names),
    )
    boiler = '<p>Subscribe to our weekly newsletter today.</p>'
    for name in names:
        site.html(f'/docs/{name}.html', page(name.upper(), para(name) + boiler))
    site.html('/docs/', page('Home'))
    seed(ctx, site.url + '/docs/')
    crawl(ctx)
    docs = [
        ctx.store.read_markdown(u.id)
        for u in ctx.store.units(source='web', status='done')
    ]
    assert len(docs) == len(names) + 1
    assert not any('Subscribe to our weekly newsletter' in d for d in docs)
    assert all('matters when a table grows large' in d for d in docs)


def test_unsupported_and_missing_pages_are_skipped(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.text('/llms.txt', '# D\n\n- [pdf]({BASE}/a.html)\n- [gone]({BASE}/gone.html)\n')
    site.routes['/a.html'] = (200, {'Content-Type': 'application/pdf'}, '%PDF')
    site.html('/', page('Home'))
    seed(ctx, site.url + '/')
    summary = crawl(ctx)
    assert summary.skipped == 2
    assert (unit_at(ctx, site.url + '/a.html').error or '').startswith('unsupported')
    assert unit_at(ctx, site.url + '/gone.html').error == 'HTTP 404'


def test_server_errors_back_off_and_stay_pending_for_a_later_run(
    site: Site, ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(web_run, 'MAX_IDLE_WAIT_S', 0.0)
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.routes['/docs/'] = (500, {}, 'boom')
    seed(ctx, site.url + '/docs/')
    summary = crawl(ctx)
    unit = unit_at(ctx, site.url + '/docs/')
    assert unit.status == 'pending'
    assert unit.attempts == 1
    assert unit.error == 'HTTP 500'
    assert summary.done == 0


# --- browser -------------------------------------------------------------------------


VERBS = ('read', 'open', 'wait', 'get', 'set', 'close')


class FakeAgentBrowser:
    def __init__(self, outputs: dict[str, list[str]]) -> None:
        self.calls: list[list[str]] = []
        self.outputs = outputs

    def __call__(self, cmd: list[str], **_kw: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(cmd)
        verb = next((t for t in cmd[1:] if t in VERBS), '')
        queue = self.outputs.get(verb, [])
        out = queue.pop(0) if len(queue) > 1 else (queue[0] if queue else '')
        return subprocess.CompletedProcess(cmd, 0, out, '')

    def verbs(self) -> list[str]:
        return [next(t for t in c[1:] if t in VERBS) for c in self.calls]

    def launches(self) -> list[list[str]]:
        return [c for c in self.calls if 'open' in c]


LONG = '# Rendered page\n\n' + 'content ' * 60
NO_READ = '{"success":false}'


def quick(text: str, final: str) -> str:
    return json.dumps({'success': True, 'data': {'content': text, 'finalUrl': final}})


def install_browser(
    monkeypatch: pytest.MonkeyPatch, outputs: dict[str, list[str]]
) -> FakeAgentBrowser:
    fake = FakeAgentBrowser(outputs)
    monkeypatch.setattr(browser.shutil, 'which', lambda _n: '/bin/agent-browser')
    monkeypatch.setattr(browser.subprocess, 'run', fake)
    return fake


def test_browser_unavailable_returns_none() -> None:
    assert browser.render('http://x.dev/') is None


def test_browser_quick_read_needs_no_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install_browser(monkeypatch, {'read': [quick(LONG, 'http://x.dev/docs/page')]})
    assert browser.render('http://x.dev/docs/page') == (
        LONG.strip(),
        'http://x.dev/docs/page',
    )
    assert fake.verbs() == ['read']
    call = fake.calls[0]
    assert call[call.index('--allowed-domains') + 1] == 'x.dev,*.x.dev'


def test_browser_launch_uses_stealth_identity_and_stays_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = install_browser(
        monkeypatch,
        {'read': [NO_READ, LONG], 'get': ['http://x.dev/docs/page\n']},
    )
    assert browser.render('http://x.dev/docs/page') == (
        LONG.strip(),
        'http://x.dev/docs/page',
    )
    assert fake.verbs() == ['read', 'open', 'set', 'wait', 'get', 'read', 'close']
    (opened,) = fake.launches()
    assert opened[opened.index('--allowed-domains') + 1] == 'x.dev,*.x.dev'
    assert opened[opened.index('--args') + 1] == browser.STEALTH_ARGS
    agent = opened[opened.index('--user-agent') + 1]
    assert f'Chrome/{browser.chrome_major()}.0.0.0' in agent
    assert '--headed' not in opened
    assert opened[-2:] == ['open', 'http://x.dev/docs/page']
    setting = next(c for c in fake.calls if 'set' in c)
    assert setting[-3:] == ['viewport', '1440', '900']
    waiting = next(c for c in fake.calls if 'wait' in c)
    assert waiting[-2:] == ['--load', 'networkidle']
    # agent-browser refuses --allowed-domains together with --profile
    assert not any('--profile' in c for c in fake.calls)


def test_browser_user_agent_matches_the_fetcher_chrome() -> None:
    assert browser.chrome_major() in str(DEFAULT_CHROME)


def test_browser_discards_a_page_that_ended_on_another_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_browser(
        monkeypatch,
        {'read': [NO_READ, LONG], 'get': ['http://169.254.169.254/x']},
    )
    assert browser.render('http://x.dev/app') is None


def test_browser_discards_a_quick_read_from_another_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = install_browser(
        monkeypatch,
        {'read': [quick(LONG, 'http://evil.dev/x'), NO_READ], 'get': ['']},
    )
    assert browser.render('http://x.dev/app') is None
    assert 'open' in fake.verbs()


def test_browser_retries_headed_only_after_a_headless_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = 'Just a moment... Verify you are human. ' * 3
    fake = install_browser(
        monkeypatch,
        {'read': [NO_READ, challenge, LONG], 'get': ['http://x.dev/']},
    )
    assert browser.render('http://x.dev/') == (LONG.strip(), 'http://x.dev/')
    headless, headed = fake.launches()
    assert '--headed' not in headless
    assert '--headed' in headed
    assert headed[headed.index('--allowed-domains') + 1] == 'x.dev,*.x.dev'


def test_browser_challenge_after_the_headed_retry_raises_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = 'Just a moment... Verify you are human. ' * 3
    fake = install_browser(
        monkeypatch, {'read': [NO_READ, challenge], 'get': ['http://x.dev/']}
    )
    with pytest.raises(browser.BrowserBlockedError):
        browser.render('http://x.dev/')
    assert len(fake.launches()) == 2


def test_browser_plain_failure_is_not_retried_headed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = install_browser(monkeypatch, {'read': [NO_READ, ''], 'get': ['http://x.dev/']})
    assert browser.render('http://x.dev/') is None
    assert len(fake.launches()) == 1


# --- shim -----------------------------------------------------------------------------


def test_cli_imports_without_web_dependencies() -> None:
    # Stdlib-only shims (a2s.py, ingest_local.py) must not import the crawler's packages.
    code = (
        'import sys\n'
        "for m in ('curl_cffi', 'defusedxml', 'protego', 'trafilatura'):\n"
        '    sys.modules[m] = None\n'
        f'sys.path.insert(0, {str(SCRIPTS_DIR)!r})\n'
        'import anything_to_skill.cli\n'
    )
    done = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(
    'shim', sorted(p.name for p in SCRIPTS_DIR.glob('*.py')), ids=lambda n: n
)
def test_every_shim_answers_help(shim: str) -> None:
    done = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / shim), '--help'],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr


def test_ingest_web_shim_exposes_web_flags() -> None:
    done = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / 'ingest_web.py'), '--help'],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0
    for flag in (
        '--brain',
        '--discover-only',
        '--min-delay',
        '--no-browser',
        '--max-pages',
    ):
        assert flag in done.stdout


def test_run_summary_shape_is_serialisable(site: Site, ctx: Ctx) -> None:
    site.text('/robots.txt', PLAIN_ROBOTS)
    site.html('/docs/', page('Home', para('Homes')))
    seed(ctx, site.url + '/docs/')
    payload = json.loads(crawl(ctx).to_json())
    assert payload['done'] == 1
    assert payload['errors'] == []
