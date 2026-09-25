"""Unit tests for the optimize-ai-setup evidence collector.

The collector lives in ``skills/optimize-ai-setup/scripts/optimize_ai_setup/``,
a real package one level under the hyphenated skill dir. Tests put its
``scripts/`` parent on ``sys.path`` and import it normally -- the hyphen only
blocks importing ``collect.py``'s directory itself, not a package nested
inside it.
"""

import json
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

EXPECTED_TWO = 2
OPUS_HIGH_2280 = ('claude-opus-5-5', 'high', '2.1.280')

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'optimize-ai-setup' / 'scripts'
)
PACKAGE_DIR = SCRIPTS_DIR / 'optimize_ai_setup'
CHECKS_MD_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'optimize-ai-setup'
    / 'references'
    / 'checks.md'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from optimize_ai_setup import (  # noqa: E402
    cli as cli_module,
    codex as codex_module,
)
from optimize_ai_setup.claude_code.memory import (  # noqa: E402
    MEMORY_FILE_LINE_LIMIT,
    check_memory,
    collect_memory_files,
)
from optimize_ai_setup.claude_code.settings import check_env_and_settings  # noqa: E402
from optimize_ai_setup.claude_code.skills_mcp import (  # noqa: E402
    check_mcp_unused,
    check_plugins,
    check_skill_descriptions,
    check_skill_dup_and_unused,
)
from optimize_ai_setup.claude_code.transcript import (  # noqa: E402
    SessionData,
    SessionRequest,
    load_all_sessions,
    parse_transcript,
)
from optimize_ai_setup.claude_code.usage_checks import (  # noqa: E402
    LONGCTX_P90_TOKENS,
    check_cache,
    check_effort,
    check_hooks,
    check_longctx,
    check_model_mix,
    check_rebuilds,
    check_startup,
)
from optimize_ai_setup.cli import run  # noqa: E402
from optimize_ai_setup.codex import (  # noqa: E402
    CX_SKILLS_BUDGET_TOKEN_FRACTION,
    CX_SKILLS_CHAR_LIMIT,
    check_codex_effort,
    check_codex_mcp,
    check_codex_sessions,
    check_codex_skills,
    codex_session_paths,
    codex_skills_budget_chars,
    collect_codex,
    detect_codex,
    latest_codex_context_window,
    read_codex_config,
)
from optimize_ai_setup.constants import UNUSED_MIN_SESSIONS  # noqa: E402
from optimize_ai_setup.cross_tool import collect_cross_tool  # noqa: E402
from optimize_ai_setup.cursor import detect_cursor  # noqa: E402
from optimize_ai_setup.gemini import collect_gemini, detect_gemini  # noqa: E402
from optimize_ai_setup.io import (  # noqa: E402
    CHARS_PER_TOKEN,
    WindowedFiles,
    chars_to_tokens,
    get_dict,
    median,
    read_json_checked,
    tokens_to_chars,
)
from optimize_ai_setup.report import render_json, render_text  # noqa: E402


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
    monkeypatch.setattr(shutil, 'which', lambda _name: None)
    return fake_home


def test_empty_home_reports_no_harness_and_does_not_crash(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = run(home, home, 14)
    assert report.detected == []
    assert report.findings == []

    render_text(report, show_all=True)
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

    sessions, _sampled = load_all_sessions(home / '.claude', 14)
    assert len(sessions) == EXPECTED_TWO

    parsed_a = parse_transcript(project_dir / 'session-a.jsonl')
    assert len(parsed_a.requests) == EXPECTED_TWO  # dup usage line deduped by requestId

    findings, metrics = check_rebuilds(sessions)
    causes = cast('dict[str, int]', metrics['causes'])
    assert causes.get('model') == 1
    assert causes.get('idle>ttl') == 1
    assert metrics['rebuilds'] == EXPECTED_TWO

    dup_findings, dup_metrics = check_skill_dup_and_unused(sessions)
    dup_finding = next(f for f in dup_findings if f.id == 'CC-SKILL-DUP')
    assert dup_finding.names == ['x']  # names carries the real duplicate, not '<name>'
    assert dup_metrics['skills_listed'] == 3  # noqa: PLR2004 - x, plugin:x, y

    startup_findings, startup_metrics = check_startup(sessions)
    expected_median = median([10100, 5100])
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
    assert expected_line_count > MEMORY_FILE_LINE_LIMIT

    project = home / 'project'
    project.mkdir()

    findings, metrics, _texts = check_memory(home, project)
    memory_findings = [f for f in findings if f.id == 'CC-MEMORY']
    assert len(memory_findings) == 1
    assert memory_findings[0].severity == 'med'
    assert f'{expected_line_count} lines' in memory_findings[0].evidence

    expected_tokens = chars_to_tokens(len(claude_md_text) + len(imported_text))
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

    files = collect_memory_files(home, project)
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

    assert detect_codex(home, project) is True
    findings, metrics, _sampled = collect_codex(home, project, 14)

    cap_findings = [f for f in findings if f.id == 'CX-AGENTSMD-CAP']
    assert len(cap_findings) == 1
    assert cap_findings[0].severity == 'med'
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
    config, config_ok = read_codex_config(home)
    assert config_ok

    budget = codex_skills_budget_chars(codex_session_paths(home, 14), config)
    assert budget == 5000 * CHARS_PER_TOKEN


def test_cx_skills_budget_is_2pct_of_latest_session_context_window(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    (codex_dir / 'config.toml').write_text('model = "gpt-6"\n', encoding='utf-8')
    _write_codex_window_session(home, 258_400)  # a real observed Codex window

    config, config_ok = read_codex_config(home)
    assert config_ok

    budget = codex_skills_budget_chars(codex_session_paths(home, 14), config)
    expected = tokens_to_chars(258_400 * CX_SKILLS_BUDGET_TOKEN_FRACTION)
    assert budget == expected
    assert 19_000 < budget < 21_000  # noqa: PLR2004 - ~20K chars, per the task description


def test_cx_skills_budget_falls_back_to_8000_chars_with_no_data(home: Path) -> None:
    budget = codex_skills_budget_chars(codex_session_paths(home, 14), {})
    assert budget == CX_SKILLS_CHAR_LIMIT


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

    config, config_ok = read_codex_config(home)
    assert config_ok

    findings, metrics = check_codex_skills(home, config, codex_session_paths(home, 14))
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

    report = run(home, project, 14)
    assert any(f.id == 'X-MCP-INLINE-SECRET' for f in report.findings)

    render_text(report, show_all=True)
    text_out = capsys.readouterr().out
    render_json(report)
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

    parsed = parse_transcript(project_dir / 'session.jsonl')
    assert parsed.deferred_chars_by_server == {'foo': pre_line_chars}

    _findings, metrics = check_startup([parsed])
    assert metrics['mcp_tool_names_tok'] == chars_to_tokens(pre_line_chars)


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

    sessions, _sampled = load_all_sessions(home / '.claude', 14)
    _findings, metrics = check_hooks(sessions)

    expected_tok = chars_to_tokens(ponytail_chars + placeholder_chars)
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

    sessions, _sampled = load_all_sessions(home / '.claude', 14)
    assert len(sessions) == UNUSED_MIN_SESSIONS

    findings, metrics = check_mcp_unused(home, project, sessions)
    mcp_finding = next(f for f in findings if f.id == 'CC-MCP-UNUSED')
    assert mcp_finding.names == ['claude_ai_Vercel']
    assert cast('int', metrics['mcp_servers_configured']) >= 1


def test_effort_high_at_100pct_does_not_fire() -> None:
    session = SessionData()
    for i in range(10):
        session.requests.append(
            SessionRequest(
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
    findings, metrics = check_effort([session])
    assert not any(f.id == 'CC-EFFORT' for f in findings)
    assert metrics['effort_share_pct'] == {'high': 100.0}


def test_effort_max_at_80pct_fires_cc_effort() -> None:
    session = SessionData()
    for i, effort in enumerate(['max'] * 8 + ['medium'] * 2):
        session.requests.append(
            SessionRequest(
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
    findings, _metrics = check_effort([session])
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

    assert detect_cursor(home, project) is False
    assert detect_gemini(home, project) is False


def test_read_json_checked_treats_non_dict_json_as_unparseable(tmp_path: Path) -> None:
    path = tmp_path / 'settings.json'
    path.write_text('[1, 2, 3]', encoding='utf-8')
    data, ok = read_json_checked(path)
    assert data == {}
    assert ok is False


def test_settings_as_json_array_does_not_crash_the_claude_code_harness(
    home: Path,
) -> None:
    claude_dir = home / '.claude'
    claude_dir.mkdir(parents=True)
    (claude_dir / 'settings.json').write_text('[]', encoding='utf-8')
    project = home / 'project'
    project.mkdir()

    report = run(home, project, 14)
    assert 'claude-code' in report.detected
    assert 'claude-code' not in report.errors


def test_check_codex_mcp_skips_non_dict_server_value() -> None:
    config = {'mcp_servers': {'good': {'enabled': True}, 'bad': 'x'}}
    findings, metrics = check_codex_mcp(config)
    assert metrics['mcp_servers'] == EXPECTED_TWO
    cx_finding = next(f for f in findings if f.id == 'CX-MCP')
    assert cx_finding.names == ['good']


def test_codex_sessions_skips_non_dict_json_lines(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    today = datetime.now(tz=UTC)
    session_dir = (
        codex_dir
        / 'sessions'
        / f'{today.year:04d}'
        / f'{today.month:02d}'
        / f'{today.day:02d}'
    )
    session_dir.mkdir(parents=True)
    lines = [
        json.dumps(['token_count', 'not a dict']),  # matches the needle, not a dict
        json.dumps(
            {
                'payload': {
                    'type': 'token_count',
                    'info': {
                        'total_token_usage': {
                            'input_tokens': 100,
                            'cached_input_tokens': 50,
                        },
                        'last_token_usage': {'input_tokens': 10},
                        'model_context_window': 1000,
                    },
                }
            }
        ),
    ]
    text = '\n'.join(lines) + '\n'
    (session_dir / 'rollout-x.jsonl').write_text(text, encoding='utf-8')

    windowed = codex_session_paths(home, 14)
    _findings, metrics, _sampled = check_codex_sessions(windowed)
    assert metrics['cache_hit_pct'] == pytest.approx(50.0)


def test_latest_codex_context_window_skips_non_dict_json_lines(home: Path) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    today = datetime.now(tz=UTC)
    session_dir = (
        codex_dir
        / 'sessions'
        / f'{today.year:04d}'
        / f'{today.month:02d}'
        / f'{today.day:02d}'
    )
    session_dir.mkdir(parents=True)
    lines = [
        json.dumps(['token_count', 'bogus']),
        json.dumps(
            {'payload': {'type': 'token_count', 'info': {'model_context_window': 12345}}}
        ),
    ]
    text = '\n'.join(lines) + '\n'
    (session_dir / 'rollout-y.jsonl').write_text(text, encoding='utf-8')

    window = latest_codex_context_window(codex_session_paths(home, 14))
    assert window == 12345  # noqa: PLR2004 - the value written above


def test_gemini_context_filename_falls_back_when_not_str_or_list(home: Path) -> None:
    gemini_dir = home / '.gemini'
    gemini_dir.mkdir(parents=True)
    (gemini_dir / 'settings.json').write_text(
        json.dumps({'context': {'fileName': 42}}), encoding='utf-8'
    )
    (gemini_dir / 'GEMINI.md').write_text('x' * 100, encoding='utf-8')
    project = home / 'project'
    project.mkdir()

    _findings, metrics, _sampled = collect_gemini(home, project, 14)
    assert metrics['context_tok'] == chars_to_tokens(100)


def test_codex_session_paths_computed_once_per_collect(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    codex_dir = home / '.codex'
    codex_dir.mkdir(parents=True)
    (codex_dir / 'config.toml').write_text('model = "gpt-6"\n', encoding='utf-8')
    project = home / 'project'
    project.mkdir()

    original = codex_module.codex_session_paths
    calls: list[int] = []

    def counting(home_arg: Path, days_arg: int) -> WindowedFiles:
        calls.append(days_arg)
        return original(home_arg, days_arg)

    monkeypatch.setattr(codex_module, 'codex_session_paths', counting)
    collect_codex(home, project, 14)
    assert len(calls) == 1


def test_cross_tool_dup_instructions_fires_without_agents_import(
    tmp_path: Path,
) -> None:
    project = tmp_path / 'project'
    project.mkdir()
    shared = '\n'.join(f'rule {i}' for i in range(10))
    (project / 'CLAUDE.md').write_text(shared, encoding='utf-8')
    (project / 'AGENTS.md').write_text(shared, encoding='utf-8')

    findings, _sampled = collect_cross_tool(project)
    dup = [f for f in findings if f.id == 'X-DUP-INSTR']
    assert len(dup) == 1
    assert dup[0].severity == 'low'


def test_cross_tool_dup_instructions_skips_when_claude_md_imports_agents(
    tmp_path: Path,
) -> None:
    project = tmp_path / 'project'
    project.mkdir()
    shared = '\n'.join(f'rule {i}' for i in range(10))
    (project / 'CLAUDE.md').write_text(f'@AGENTS.md\n{shared}', encoding='utf-8')
    (project / 'AGENTS.md').write_text(shared, encoding='utf-8')

    findings, _sampled = collect_cross_tool(project)
    assert not any(f.id == 'X-DUP-INSTR' for f in findings)


def test_check_longctx_fires_above_threshold() -> None:
    session = SessionData()
    session.requests.append(
        SessionRequest(
            ts=0.0,
            model='claude-opus-5-5',
            effort='high',
            version='2.1.280',
            is_sidechain=False,
            input_tok=1000,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    session.requests.append(
        SessionRequest(
            ts=1.0,
            model='claude-opus-5-5',
            effort='high',
            version='2.1.280',
            is_sidechain=False,
            input_tok=LONGCTX_P90_TOKENS + 50_000,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    findings, metrics = check_longctx([session])
    matches = [f for f in findings if f.id == 'CC-LONGCTX']
    assert len(matches) == 1
    assert metrics['peak_p90_tok'] == LONGCTX_P90_TOKENS + 50_000


def test_check_model_mix_fires_fable_and_subagent_opus() -> None:
    session = SessionData()
    session.requests.append(
        SessionRequest(
            ts=0.0,
            model='claude-fable-5-1',
            effort='high',
            version='v',
            is_sidechain=False,
            input_tok=1000,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    session.requests.append(
        SessionRequest(
            ts=1.0,
            model='claude-sonnet-5',
            effort='high',
            version='v',
            is_sidechain=False,
            input_tok=100,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    session.requests.append(
        SessionRequest(
            ts=2.0,
            model='claude-opus-5-5',
            effort='high',
            version='v',
            is_sidechain=True,
            input_tok=1000,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    findings, metrics = check_model_mix([session])
    assert any(f.id == 'CC-MODEL-MIX' for f in findings)
    assert any(f.id == 'CC-SUBAGENT-MODEL' for f in findings)
    model_share = cast('dict[str, float]', metrics['model_share_pct'])
    assert model_share['claude-fable-5-1'] == pytest.approx(90.9, abs=0.1)


def test_check_plugins_fires_for_unused_and_not_for_used(home: Path) -> None:
    claude_dir = home / '.claude'
    claude_dir.mkdir(parents=True)
    (claude_dir / 'settings.json').write_text(
        json.dumps(
            {'enabledPlugins': ['used-plugin@marketplace', 'unused-plugin@marketplace']}
        ),
        encoding='utf-8',
    )
    sessions = []
    for _ in range(UNUSED_MIN_SESSIONS):
        session = SessionData()
        session.skill_uses['used-plugin:some-skill'] += 1
        sessions.append(session)

    findings, metrics = check_plugins(home, sessions)
    unused = next(f for f in findings if f.id == 'CC-PLUGIN-UNUSED')
    assert unused.names == ['unused-plugin']
    assert metrics['plugins_enabled'] == EXPECTED_TWO


def test_check_plugins_does_not_fire_when_all_used(home: Path) -> None:
    claude_dir = home / '.claude'
    claude_dir.mkdir(parents=True)
    (claude_dir / 'settings.json').write_text(
        json.dumps({'enabledPlugins': ['used-plugin@marketplace']}), encoding='utf-8'
    )
    sessions = []
    for _ in range(UNUSED_MIN_SESSIONS):
        session = SessionData()
        session.skill_uses['used-plugin:some-skill'] += 1
        sessions.append(session)

    findings, _metrics = check_plugins(home, sessions)
    assert not any(f.id == 'CC-PLUGIN-UNUSED' for f in findings)


def test_check_env_and_settings_fires_for_stale_disable_caching(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(os, 'environ', {'DISABLE_PROMPT_CACHING': '1'})
    (home / '.claude').mkdir(parents=True)

    findings, _metrics = check_env_and_settings(home)
    assert any(f.id == 'CC-STALE-ENV' and f.severity == 'high' for f in findings)


def test_check_env_and_settings_does_not_fire_with_clean_env(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(os, 'environ', {})
    claude_dir = home / '.claude'
    claude_dir.mkdir(parents=True)
    (claude_dir / 'settings.json').write_text(
        json.dumps({'statusLine': {'type': 'command', 'command': 'true'}}),
        encoding='utf-8',
    )

    findings, _metrics = check_env_and_settings(home)
    assert findings == []


def test_parse_transcript_skips_malformed_and_non_dict_json_lines(
    tmp_path: Path,
) -> None:
    path = tmp_path / 'session.jsonl'
    lines = [
        '{"usage": invalid json here',  # contains the needle, fails json.loads
        '["usage", 1, 2]',  # valid JSON, but not a dict
        json.dumps(
            _usage_line(
                request_id='req-1',
                meta=OPUS_HIGH_2280,
                ts='2026-09-01T10:00:00Z',
                usage={'input_tok': 100, 'read_tok': 0},
            )
        ),
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    session = parse_transcript(path)
    assert len(session.requests) == 1


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ({'k': {'a': 1}}, {'a': 1}),
        ({'k': 'a string'}, {}),
        ({'k': ['a', 'list']}, {}),
        ({'k': 42}, {}),
        ({}, {}),
        ('not a dict', {}),
        (['not', 'a', 'dict'], {}),
        (42, {}),
    ],
)
def test_get_dict_returns_empty_unless_source_and_value_are_both_dicts(
    source: object, expected: dict
) -> None:
    assert get_dict(source, 'k') == expected


@pytest.mark.parametrize('bad', ['a string', ['a', 'list'], 42])
def test_nested_dict_walks_tolerate_non_dict_intermediates(
    bad: object, tmp_path: Path
) -> None:
    home = tmp_path / 'home'
    home.mkdir()
    project = tmp_path / 'project'
    project.mkdir()

    # codex.py: the payload/info chain in two JSONL walkers, and mcp_servers
    # in check_codex_mcp.
    codex_dir = home / '.codex'
    today = datetime.now(tz=UTC)
    session_dir = (
        codex_dir
        / 'sessions'
        / f'{today.year:04d}'
        / f'{today.month:02d}'
        / f'{today.day:02d}'
    )
    session_dir.mkdir(parents=True)
    line = json.dumps({'payload': bad, 'token_count': 'x'})
    (session_dir / 'rollout-bad.jsonl').write_text(line + '\n', encoding='utf-8')
    windowed = codex_session_paths(home, 14)
    latest_codex_context_window(windowed)  # must not raise
    check_codex_sessions(windowed)  # must not raise
    check_codex_mcp({'mcp_servers': bad})  # must not raise

    # gemini.py: get_dict(settings, 'context').get('fileName').
    gemini_dir = home / '.gemini'
    gemini_dir.mkdir(parents=True)
    (gemini_dir / 'settings.json').write_text(
        json.dumps({'context': bad}), encoding='utf-8'
    )
    collect_gemini(home, project, 14)  # must not raise

    # cross_tool.py: get_dict(config, 'mcpServers').items().
    (project / '.mcp.json').write_text(json.dumps({'mcpServers': bad}), encoding='utf-8')
    collect_cross_tool(project)  # must not raise

    # claude_code/skills_mcp.py: claude_json['projects'][str(project)].
    (home / '.claude.json').write_text(json.dumps({'projects': bad}), encoding='utf-8')
    check_mcp_unused(home, project, [])  # must not raise

    # claude_code/transcript.py: message/attachment/tool_use-input chains.
    transcript_dir = home / '.claude' / 'projects' / 'testproj'
    transcript_dir.mkdir(parents=True)
    lines = [
        json.dumps({'type': 'assistant', 'message': bad, 'usage': 'x'}),
        json.dumps({'type': 'attachment', 'attachment': bad}),
        json.dumps(
            {
                'type': 'assistant',
                'message': {
                    'content': [{'type': 'tool_use', 'name': 'Skill', 'input': bad}]
                },
            }
        ),
    ]
    text = '\n'.join(lines) + '\n'
    (transcript_dir / 'session-bad.jsonl').write_text(text, encoding='utf-8')
    parse_transcript(transcript_dir / 'session-bad.jsonl')  # must not raise


def test_run_wraps_cross_tool_crash_into_an_error_entry(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = home / 'project'
    project.mkdir()

    def boom(_project: Path) -> tuple[list, list]:
        raise ValueError('boom')

    monkeypatch.setattr(cli_module, 'collect_cross_tool', boom)
    report = run(home, project, 14)
    assert report.errors.get('cross-tool') == 'ValueError'


def test_check_skill_descriptions_fires_over_1536_chars(home: Path) -> None:
    skill_dir = home / '.claude' / 'skills' / 'big-skill'
    skill_dir.mkdir(parents=True)
    long_desc = 'x' * 1600
    (skill_dir / 'SKILL.md').write_text(
        f'---\nname: big-skill\ndescription: {long_desc}\n---\nBody.\n',
        encoding='utf-8',
    )
    project = home / 'project'
    project.mkdir()

    findings, _texts = check_skill_descriptions(home, project)
    matches = [f for f in findings if f.id == 'CC-SKILL-LISTING']
    assert len(matches) == 1
    assert 'big-skill' in matches[0].evidence


def test_check_skill_descriptions_does_not_fire_under_the_limit(home: Path) -> None:
    skill_dir = home / '.claude' / 'skills' / 'small-skill'
    skill_dir.mkdir(parents=True)
    (skill_dir / 'SKILL.md').write_text(
        '---\nname: small-skill\ndescription: short.\n---\nBody.\n', encoding='utf-8'
    )
    project = home / 'project'
    project.mkdir()

    findings, _texts = check_skill_descriptions(home, project)
    assert findings == []


def test_check_cache_fires_when_disable_prompt_caching_set_with_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, 'environ', {'DISABLE_PROMPT_CACHING': '1'})
    session = SessionData()
    session.requests.append(
        SessionRequest(
            ts=0.0,
            model='m',
            effort='high',
            version='v',
            is_sidechain=False,
            input_tok=100,
            write_1h=1000,
            write_5m=0,
            read_tok=100,
        )
    )
    findings, metrics = check_cache([session])
    assert any(f.id == 'CC-CACHE' and f.severity == 'high' for f in findings)
    assert cast('float', metrics['hit_pct']) > 0


def test_check_cache_zero_cost_edge_case_does_not_divide_by_zero() -> None:
    session = SessionData()
    session.requests.append(
        SessionRequest(
            ts=0.0,
            model='m',
            effort='high',
            version='v',
            is_sidechain=False,
            input_tok=0,
            write_1h=0,
            write_5m=0,
            read_tok=0,
        )
    )
    findings, metrics = check_cache([session])
    assert findings == []
    assert metrics['write_cost_share_pct'] == 0.0


def test_check_codex_effort_fires_for_high_not_for_medium_or_unset() -> None:
    findings, metrics = check_codex_effort({'model_reasoning_effort': 'high'})
    assert any(f.id == 'CX-EFFORT' and f.severity == 'info' for f in findings)
    assert metrics['model_reasoning_effort'] == 'high'

    findings, metrics = check_codex_effort({'model_reasoning_effort': 'medium'})
    assert findings == []
    assert metrics['model_reasoning_effort'] == 'medium'

    findings, metrics = check_codex_effort({})
    assert findings == []
    assert metrics == {}


def test_every_emitted_check_id_has_a_checks_md_entry_and_vice_versa() -> None:
    source = '\n'.join(
        p.read_text(encoding='utf-8') for p in sorted(PACKAGE_DIR.rglob('*.py'))
    )
    emitted_ids = set(re.findall(r"make_finding\(\s*'([A-Z][A-Z0-9-]+)'", source))
    assert emitted_ids, 'expected to find at least one make_finding(...) call'

    checks_text = CHECKS_MD_PATH.read_text(encoding='utf-8')
    heading_ids = {
        name
        for name in re.findall(r'^## ([A-Z][A-Z0-9-]+)$', checks_text, re.MULTILINE)
        if name != 'HABITS'
    }

    assert emitted_ids == heading_ids
