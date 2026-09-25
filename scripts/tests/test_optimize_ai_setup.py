"""Unit tests for the optimize-ai-setup evidence collector.

The script lives in ``skills/optimize-ai-setup/scripts/`` -- a hyphenated
package dir that can't be imported normally -- so it is loaded by path via
importlib, same as ``test_inject_fastapi_docs.py``.
"""

import importlib.util
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest

EXPECTED_TWO = 2
OPUS_HIGH_2280 = ('claude-opus-5-5', 'high', '2.1.280')

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'optimize-ai-setup'
    / 'scripts'
    / 'collect.py'
)
CHECKS_MD_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'optimize-ai-setup'
    / 'references'
    / 'checks.md'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        'optimize_ai_setup_collect', MODULE_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass field resolution needs this registered
    spec.loader.exec_module(module)
    return module


collect = _load_module()


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8')


def _usage_line(
    *,
    request_id: str,
    meta: tuple[str, str, str],  # (model, effort, version)
    ts: str,
    usage: dict,  # input_tok, read_tok, write_1h=0, write_5m=0
) -> dict:
    model, effort, version = meta
    return {
        'type': 'assistant',
        'isSidechain': False,
        'requestId': request_id,
        'effort': effort,
        'version': version,
        'timestamp': ts,
        'message': {
            'model': model,
            'content': [],
            'usage': {
                'input_tokens': usage['input_tok'],
                'cache_read_input_tokens': usage['read_tok'],
                'cache_creation': {
                    'ephemeral_1h_input_tokens': usage.get('write_1h', 0),
                    'ephemeral_5m_input_tokens': usage.get('write_5m', 0),
                },
            },
        },
    }


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_home = tmp_path / 'home'
    fake_home.mkdir()
    monkeypatch.setenv('HOME', str(fake_home))
    monkeypatch.setattr(collect.shutil, 'which', lambda _name: None)
    return fake_home


def test_empty_home_reports_no_harness_and_does_not_crash(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = collect.run(home, home, 14)
    assert report.detected == []
    assert report.findings == []

    collect.render_text(report, show_all=True)
    out = capsys.readouterr().out
    assert 'no harness detected' in out


def test_claude_code_transcript_dedupe_rebuilds_dup_and_startup(home: Path) -> None:
    project_dir = home / '.claude' / 'projects' / 'testproj'

    # Session A: duplicated usage line for the startup request (must dedupe by
    # requestId), then a model-switch rebuild.
    session_a = [
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'skill_listing',
                'content': '- x\n- plugin:x\n- y',
                'names': ['x', 'plugin:x', 'y'],
            },
        },
        _usage_line(
            request_id='req-1',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T10:00:00Z',
            usage={'input_tok': 100, 'write_1h': 25000, 'read_tok': 5000},
        ),
        # Exact duplicate of the request above: same requestId, must not double count.
        _usage_line(
            request_id='req-1',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T10:00:00Z',
            usage={'input_tok': 100, 'write_1h': 25000, 'read_tok': 5000},
        ),
        _usage_line(
            request_id='req-2',
            meta=('claude-sonnet-5', 'high', '2.1.280'),  # model switch -> 'model'
            ts='2026-09-01T10:00:10Z',
            usage={'input_tok': 100, 'write_1h': 20000, 'read_tok': 100},
        ),
    ]
    _write_jsonl(project_dir / 'session-a.jsonl', session_a)

    # Session B: idle-gap rebuild (same model/effort/version, gap > 300s TTL).
    session_b = [
        _usage_line(
            request_id='req-3',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T12:00:00Z',
            usage={'input_tok': 100, 'write_5m': 5000, 'read_tok': 0},
        ),
        _usage_line(
            request_id='req-4',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T12:06:40Z',  # 400s later, > 300s TTL for a 5m write
            usage={'input_tok': 100, 'write_5m': 25000, 'read_tok': 100},
        ),
    ]
    _write_jsonl(project_dir / 'session-b.jsonl', session_b)

    sessions, _sampled = collect.load_all_sessions(home / '.claude', 14)
    assert len(sessions) == EXPECTED_TWO

    parsed_a = collect.parse_transcript(project_dir / 'session-a.jsonl')
    assert len(parsed_a.requests) == EXPECTED_TWO  # dup usage line deduped by requestId

    findings, metrics = collect.check_rebuilds(sessions)
    causes = metrics['causes']
    assert causes.get('model') == 1
    assert causes.get('idle>ttl') == 1
    assert metrics['rebuilds'] == EXPECTED_TWO

    dup_findings, dup_metrics = collect.check_skill_dup_and_unused(sessions)
    dup_finding = next(f for f in dup_findings if f.id == 'CC-SKILL-DUP')
    assert dup_finding.names == ['x']  # names carries the real duplicate, not '<name>'
    assert dup_metrics['skills_listed'] == 3  # noqa: PLR2004 - x, plugin:x, y

    startup_findings, startup_metrics = collect.check_startup(sessions)
    expected_median = collect.median([10100, 5100])
    assert startup_metrics['startup_median_tok'] == int(expected_median)
    assert isinstance(startup_findings, list)


def test_claude_md_250_lines_triggers_memory_finding_import_counted_once(
    home: Path,
) -> None:
    claude_dir = home / '.claude'
    claude_dir.mkdir(parents=True, exist_ok=True)
    imported_text = 'Shared workflow rules.\n' * 20
    (claude_dir / 'extra-memory.md').write_text(imported_text, encoding='utf-8')

    body_lines = [f'line {i}' for i in range(245)]
    claude_md_text = (
        '# Memory\n\n@extra-memory.md\n\nSee also @extra-memory.md again.\n'
        + '\n'.join(body_lines)
        + '\n'
    )
    (claude_dir / 'CLAUDE.md').write_text(claude_md_text, encoding='utf-8')
    expected_line_count = claude_md_text.count('\n') + 1
    assert expected_line_count > collect.MEMORY_FILE_LINE_LIMIT

    project = home / 'project'
    project.mkdir()

    findings, metrics, _texts = collect.check_memory(home, project)
    assert any(
        f.id == 'CC-MEMORY' and f'{expected_line_count} lines' in f.evidence
        for f in findings
    )

    expected_tokens = collect.chars_to_tokens(len(claude_md_text) + len(imported_text))
    assert metrics['always_loaded_tok'] == expected_tokens
    # CLAUDE.md + extra-memory.md, imported only once despite two @-references.
    assert metrics['files'] == EXPECTED_TWO


def test_memory_walk_reaches_claude_md_above_git_root(tmp_path: Path) -> None:
    home = tmp_path / 'home'
    home.mkdir()

    root_area = tmp_path / 'workspace'
    root_area.mkdir()
    (root_area / 'CLAUDE.md').write_text('Root-level memory.\n', encoding='utf-8')

    repo = root_area / 'repo'
    (repo / '.git').mkdir(parents=True)
    project = repo / 'nested' / 'project'
    project.mkdir(parents=True)

    files = collect.collect_memory_files(home, project)
    assert files[root_area / 'CLAUDE.md'] == 'Root-level memory.\n'


def test_codex_agents_md_cap_and_cache_metric(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    (codex_dir / 'config.toml').write_text('model = "gpt-6"\n', encoding='utf-8')
    (codex_dir / 'AGENTS.md').write_text('x' * 33_000, encoding='utf-8')

    today = datetime.now(tz=UTC)
    session_dir = (
        codex_dir
        / 'sessions'
        / f'{today.year:04d}'
        / f'{today.month:02d}'
        / f'{today.day:02d}'
    )
    session_dir.mkdir(parents=True)
    token_count_line = {
        'timestamp': today.isoformat(),
        'type': 'event_msg',
        'payload': {
            'type': 'token_count',
            'info': {
                'total_token_usage': {
                    'input_tokens': 10000,
                    'cached_input_tokens': 9000,
                    'cache_write_input_tokens': 0,
                    'output_tokens': 100,
                },
                'last_token_usage': {'input_tokens': 5000},
                'model_context_window': 200000,
            },
        },
    }
    _write_jsonl(session_dir / 'rollout-test.jsonl', [token_count_line])

    project = home / 'project'
    project.mkdir()

    assert collect.detect_codex(home, project) is True
    findings, metrics, _sampled = collect.collect_codex(home, project, 14)

    assert any(f.id == 'CX-AGENTSMD-CAP' for f in findings)
    assert metrics['cache_hit_pct'] == pytest.approx(90.0, abs=0.1)


def _write_codex_window_session(home: Path, window: int) -> None:
    today = datetime.now(tz=UTC)
    session_dir = (
        home
        / '.codex'
        / 'sessions'
        / f'{today.year:04d}'
        / f'{today.month:02d}'
        / f'{today.day:02d}'
    )
    session_dir.mkdir(parents=True, exist_ok=True)
    token_count_line = {
        'timestamp': today.isoformat(),
        'type': 'event_msg',
        'payload': {
            'type': 'token_count',
            'info': {
                'total_token_usage': {'input_tokens': 100, 'cached_input_tokens': 0},
                'last_token_usage': {'input_tokens': 100},
                'model_context_window': window,
            },
        },
    }
    _write_jsonl(session_dir / 'rollout-window.jsonl', [token_count_line])


def test_cx_skills_budget_from_config_max_context_tokens(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    (codex_dir / 'config.toml').write_text(
        '[skills]\nmax_context_tokens = 5000\n', encoding='utf-8'
    )
    config, config_ok = collect.read_codex_config(home)
    assert config_ok

    budget = collect.codex_skills_budget_chars(home, config, 14)
    assert budget == 5000 * collect.CHARS_PER_TOKEN


def test_cx_skills_budget_is_2pct_of_latest_session_context_window(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    (codex_dir / 'config.toml').write_text('model = "gpt-6"\n', encoding='utf-8')
    _write_codex_window_session(home, 258_400)  # a real observed Codex window

    config, config_ok = collect.read_codex_config(home)
    assert config_ok

    budget = collect.codex_skills_budget_chars(home, config, 14)
    expected = collect.tokens_to_chars(258_400 * collect.CX_SKILLS_BUDGET_TOKEN_FRACTION)
    assert budget == expected
    assert 19_000 < budget < 21_000  # noqa: PLR2004 - ~20K chars, per the task description


def test_cx_skills_budget_falls_back_to_8000_chars_with_no_data(home: Path) -> None:
    budget = collect.codex_skills_budget_chars(home, {}, 14)
    assert budget == collect.CX_SKILLS_CHAR_LIMIT


def test_codex_skills_excludes_disabled_config_entries(home: Path) -> None:
    skills_dir = home / '.agents' / 'skills'
    long_desc = 'Description long enough to matter for the char budget in this test.'
    for skill_name in ('foo', 'bar', 'baz'):
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / 'SKILL.md').write_text(
            f'---\nname: {skill_name}\ndescription: {long_desc}\n---\nBody.\n',
            encoding='utf-8',
        )

    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    # foo is disabled by its exact SKILL.md path; baz by its folder, given as
    # a ~-relative path -- both forms the collector must accept.
    foo_skill_md = skills_dir / 'foo' / 'SKILL.md'
    (codex_dir / 'config.toml').write_text(
        f"""
[skills]
max_context_tokens = 1

[[skills.config]]
path = "{foo_skill_md}"
enabled = false

[[skills.config]]
path = "~/.agents/skills/baz"
enabled = false
""",
        encoding='utf-8',
    )

    config, config_ok = collect.read_codex_config(home)
    assert config_ok

    findings, metrics = collect.check_codex_skills(home, config, 14)
    assert metrics['skills'] == 1
    cx_finding = next(f for f in findings if f.id == 'CX-SKILLS')
    assert cx_finding.names == ['bar']


def test_secrets_never_leak_and_inline_secret_finding_fires(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = home / 'project'
    project.mkdir()
    mcp_config = {
        'mcpServers': {
            'myserver': {
                'env': {'API_KEY': 'sk-ant-SECRET123'},
                'headers': {'Authorization': 'Bearer SECRET456'},
            }
        }
    }
    (project / '.mcp.json').write_text(json.dumps(mcp_config), encoding='utf-8')

    # ~/.claude.json mcpServers env: only server *names* may ever be read, never
    # the env values, so this secret must never surface either.
    claude_json = {
        'mcpServers': {'homeserver': {'env': {'API_KEY': 'sk-ant-HOMESECRET111'}}}
    }
    (home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')

    # ~/.cursor/mcp.json headers: same rule, at a different config path/harness.
    cursor_dir = home / '.cursor'
    cursor_dir.mkdir()
    cursor_mcp = {
        'mcpServers': {
            'cursorserver': {'headers': {'Authorization': 'Bearer CURSORSECRET222'}}
        }
    }
    (cursor_dir / 'mcp.json').write_text(json.dumps(cursor_mcp), encoding='utf-8')

    transcript_dir = home / '.claude' / 'projects' / 'testproj'
    _write_jsonl(
        transcript_dir / 'session-secret.jsonl',
        [
            {
                'type': 'user',
                'isSidechain': False,
                'timestamp': '2026-09-01T10:00:00Z',
                'message': {
                    'role': 'user',
                    'content': [{'type': 'text', 'text': 'here is PRIVATE_TEXT_789'}],
                },
            },
            _usage_line(
                request_id='req-1',
                meta=OPUS_HIGH_2280,
                ts='2026-09-01T10:00:05Z',
                usage={'input_tok': 100, 'write_1h': 1000, 'read_tok': 100},
            ),
        ],
    )

    report = collect.run(home, project, 14)
    assert any(f.id == 'X-MCP-INLINE-SECRET' for f in report.findings)

    collect.render_text(report, show_all=True)
    text_out = capsys.readouterr().out
    collect.render_json(report)
    json_out = capsys.readouterr().out

    for secret in (
        'sk-ant-SECRET123',
        'SECRET456',
        'PRIVATE_TEXT_789',
        'sk-ant-HOMESECRET111',
        'CURSORSECRET222',
    ):
        assert secret not in text_out
        assert secret not in json_out


def test_startup_attribution_excludes_attachments_after_first_request(
    home: Path,
) -> None:
    project_dir = home / '.claude' / 'projects' / 'testproj'
    pre_line_chars = 400
    post_line_chars = 4000
    session = [
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'deferred_tools_delta',
                'addedNames': ['mcp__foo__bar'],
                'addedLines': ['x' * pre_line_chars],
            },
        },
        _usage_line(
            request_id='req-1',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T10:00:00Z',
            usage={'input_tok': 100, 'write_1h': 1000, 'read_tok': 100},
        ),
        # This delta happens AFTER the session's first main-thread request, so
        # it must not be attributed to startup context.
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'deferred_tools_delta',
                'addedNames': ['mcp__foo__baz'],
                'addedLines': ['y' * post_line_chars],
            },
        },
        _usage_line(
            request_id='req-2',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T10:01:00Z',
            usage={'input_tok': 100, 'write_1h': 100, 'read_tok': 100},
        ),
    ]
    _write_jsonl(project_dir / 'session.jsonl', session)

    parsed = collect.parse_transcript(project_dir / 'session.jsonl')
    assert parsed.deferred_chars_by_server == {'foo': pre_line_chars}

    _findings, metrics = collect.check_startup([parsed])
    assert metrics['mcp_tool_names_tok'] == collect.chars_to_tokens(pre_line_chars)


def test_hook_stdout_fallback_does_not_overcount_sessionstart(home: Path) -> None:
    # Reproduces a real overcount: two hooks fire on the same SessionStart
    # event. Hook A (e.g. ponytail) prints its real ~5.2K-char context
    # straight into `content`. Hook B's real output is oversized, so Claude
    # Code empties its `content` and reports the actual injected text (a
    # small persisted-output placeholder) as a separate hook_additional_context
    # attachment -- but hook B's own `stdout` still holds its full, un-injected
    # raw process output. Falling back to `stdout` when `content` is empty
    # counted that raw output as if it were injected context.
    project_dir = home / '.claude' / 'projects' / 'testproj'
    ponytail_chars = 5200
    raw_stdout_chars = 120_000
    placeholder_chars = 40
    session = [
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'hook_success',
                'hookName': 'SessionStart:startup',
                'toolUseID': 'tool-1',
                'hookEvent': 'SessionStart',
                'content': 'x' * ponytail_chars,
                'stdout': 'x' * ponytail_chars,
            },
        },
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'hook_success',
                'hookName': 'SessionStart:startup',
                'toolUseID': 'tool-1',
                'hookEvent': 'SessionStart',
                'content': '',
                'stdout': 'y' * raw_stdout_chars,
            },
        },
        {
            'type': 'attachment',
            'isSidechain': False,
            'attachment': {
                'type': 'hook_additional_context',
                'hookName': 'SessionStart',
                'toolUseID': 'SessionStart',
                'hookEvent': 'SessionStart',
                'content': ['z' * placeholder_chars],
            },
        },
        _usage_line(
            request_id='req-1',
            meta=OPUS_HIGH_2280,
            ts='2026-09-01T10:00:00Z',
            usage={'input_tok': 100, 'write_1h': 1000, 'read_tok': 100},
        ),
    ]
    _write_jsonl(project_dir / 'session.jsonl', session)

    sessions, _sampled = collect.load_all_sessions(home / '.claude', 14)
    _findings, metrics = collect.check_hooks(sessions)

    expected_tok = collect.chars_to_tokens(ponytail_chars + placeholder_chars)
    assert metrics['session_start_hook_tok'] == expected_tok


def test_mcp_unused_includes_deferred_tool_names_from_latest_session(home: Path) -> None:
    project_dir = home / '.claude' / 'projects' / 'testproj'
    for i in range(4):
        _write_jsonl(
            project_dir / f'session-{i}.jsonl',
            [
                _usage_line(
                    request_id=f'req-{i}',
                    meta=OPUS_HIGH_2280,
                    ts=f'2026-09-0{i + 1}T10:00:00Z',
                    usage={'input_tok': 100, 'write_1h': 100, 'read_tok': 100},
                )
            ],
        )
    _write_jsonl(
        project_dir / 'session-latest.jsonl',
        [
            {
                'type': 'attachment',
                'isSidechain': False,
                'attachment': {
                    'type': 'deferred_tools_delta',
                    'addedNames': ['mcp__claude_ai_Vercel__deploy'],
                    'addedLines': ['tool spec'],
                },
            },
            _usage_line(
                request_id='req-latest',
                meta=OPUS_HIGH_2280,
                ts='2026-09-10T10:00:00Z',
                usage={'input_tok': 100, 'write_1h': 100, 'read_tok': 100},
            ),
        ],
    )

    project = home / 'project'
    project.mkdir()

    sessions, _sampled = collect.load_all_sessions(home / '.claude', 14)
    assert len(sessions) == collect.UNUSED_MIN_SESSIONS

    findings, metrics = collect.check_mcp_unused(home, project, sessions)
    mcp_finding = next(f for f in findings if f.id == 'CC-MCP-UNUSED')
    assert mcp_finding.names == ['claude_ai_Vercel']
    assert metrics['mcp_servers_configured'] >= 1


def test_effort_high_at_100pct_does_not_fire() -> None:
    session = collect.SessionData()
    for i in range(10):
        session.requests.append(
            collect.SessionRequest(
                ts=float(i),
                model='claude-opus-5-5',
                effort='high',
                version='2.1.280',
                is_sidechain=False,
                input_tok=10,
                write_1h=0,
                write_5m=0,
                read_tok=10,
            )
        )
    findings, metrics = collect.check_effort([session])
    assert not any(f.id == 'CC-EFFORT' for f in findings)
    assert metrics['effort_share_pct'] == {'high': 100.0}


def test_effort_max_at_80pct_fires_cc_effort() -> None:
    session = collect.SessionData()
    for i, effort in enumerate(['max'] * 8 + ['medium'] * 2):
        session.requests.append(
            collect.SessionRequest(
                ts=float(i),
                model='claude-opus-5-5',
                effort=effort,
                version='2.1.280',
                is_sidechain=False,
                input_tok=10,
                write_1h=0,
                write_5m=0,
                read_tok=10,
            )
        )
    findings, _metrics = collect.check_effort([session])
    matches = [f for f in findings if f.id == 'CC-EFFORT']
    assert len(matches) == 1
    assert 'xhigh/max effort on 80%' in matches[0].evidence


def test_bare_cursor_and_gemini_config_are_not_detected(home: Path) -> None:
    project = home / 'project'
    project.mkdir()

    cursor_dir = home / '.cursor'
    cursor_dir.mkdir()
    (cursor_dir / 'argv.json').write_text('{}', encoding='utf-8')

    gemini_dir = home / '.gemini'
    gemini_dir.mkdir()
    (gemini_dir / 'settings.json').write_text('{}', encoding='utf-8')

    assert collect.detect_cursor(home, project) is False
    assert collect.detect_gemini(home, project) is False


def test_every_emitted_check_id_has_a_checks_md_entry_and_vice_versa() -> None:
    source = MODULE_PATH.read_text(encoding='utf-8')
    emitted_ids = set(re.findall(r"make_finding\(\s*'([A-Z][A-Z0-9-]+)'", source))
    assert emitted_ids, 'expected to find at least one make_finding(...) call'

    checks_text = CHECKS_MD_PATH.read_text(encoding='utf-8')
    heading_ids = {
        name
        for name in re.findall(r'^## ([A-Z][A-Z0-9-]+)$', checks_text, re.MULTILINE)
        if name != 'HABITS'
    }

    assert emitted_ids == heading_ids
