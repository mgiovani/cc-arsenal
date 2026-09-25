"""Codex CLI: config.toml-based checks plus its own session .jsonl format."""

from __future__ import annotations

import json
import shutil
import time
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE, UNUSED_MIN_SESSIONS
from optimize_ai_setup.io import (
    WindowedFiles,
    chars_to_tokens,
    find_git_root,
    get_dict,
    iter_filtered_lines,
    percentile,
    read_text_capped,
    select_in_window,
    tokens_to_chars,
)
from optimize_ai_setup.model import Finding, make_finding
from optimize_ai_setup.skillfiles import scan_skill_dir

CX_AGENTSMD_DEFAULT_CAP_BYTES = 32_768
CX_LONGCTX_FILL_THRESHOLD = 0.70
CX_CACHE_HIT_PCT_THRESHOLD = 80
CX_SKILLS_CHAR_LIMIT = 8_000
CX_SKILLS_BUDGET_TOKEN_FRACTION = 0.02


def detect_codex(home: Path, _project: Path) -> bool:
    return (home / '.codex' / 'config.toml').exists() or shutil.which('codex') is not None


def read_codex_config(home: Path) -> tuple[dict, bool]:
    """Returns (config, ok). ok is False only when the file exists but could
    not be parsed, so callers can report "config.toml unreadable" instead of
    silently looking like zero servers/settings configured."""
    config_path = home / '.codex' / 'config.toml'
    if not config_path.is_file():
        return {}, True
    try:
        with config_path.open('rb') as fh:
            return tomllib.load(fh), True
    except (OSError, tomllib.TOMLDecodeError):
        return {}, False


def codex_session_paths(home: Path, days: int) -> WindowedFiles:
    sessions_root = home / '.codex' / 'sessions'
    if not sessions_root.is_dir():
        return WindowedFiles([], 0)
    candidates: list[Path] = []
    cutoff_date = datetime.fromtimestamp(time.time() - days * 86400, tz=UTC)
    day = cutoff_date
    now = datetime.now(tz=UTC)
    while day <= now:
        day_dir = (
            sessions_root / f'{day.year:04d}' / f'{day.month:02d}' / f'{day.day:02d}'
        )
        if day_dir.is_dir():
            candidates.extend(day_dir.glob('*.jsonl'))
        day += timedelta(days=1)
    return select_in_window(candidates, days)


def latest_codex_context_window(windowed: WindowedFiles) -> int | None:
    # windowed.paths is sorted most-recent-first (select_in_window); within a
    # file, the last token_count event holds that session's final window size.
    for path in windowed.paths:
        window = None
        for line in iter_filtered_lines(path, ('"token_count"',)):
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(obj, dict):
                continue
            info = get_dict(get_dict(obj, 'payload'), 'info')
            candidate = info.get('model_context_window')
            if isinstance(candidate, int | float) and candidate > 0:
                window = int(candidate)
        if window:
            return window
    return None


def check_codex_sessions(
    windowed: WindowedFiles,
) -> tuple[list[Finding], dict[str, object], list[str]]:
    sampled = []
    if windowed.sampled:
        sampled.append(f'codex {len(windowed.paths)}/{windowed.total_in_window} sessions')

    input_totals: list[int] = []
    cached_totals: list[int] = []
    fills: list[float] = []
    for path in windowed.paths:
        last: dict | None = None
        for line in iter_filtered_lines(path, ('"token_count"',)):
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(obj, dict):
                continue
            info = get_dict(get_dict(obj, 'payload'), 'info')
            if info.get('total_token_usage'):
                last = info
        if not last:
            continue
        total = last['total_token_usage']
        if not isinstance(total, dict):
            continue
        input_totals.append(int(total.get('input_tokens') or 0))
        cached_totals.append(int(total.get('cached_input_tokens') or 0))
        window = last.get('model_context_window')
        last_usage = get_dict(last, 'last_token_usage')
        if isinstance(window, int | float) and window > 0:
            fills.append((last_usage.get('input_tokens') or 0) / window)

    findings: list[Finding] = []
    metrics: dict[str, object] = {'sessions': len(windowed.paths)}
    if input_totals:
        cache_pct = 100 * sum(cached_totals) / max(sum(input_totals), 1)
        metrics['cache_hit_pct'] = round(cache_pct, 1)
        if (
            len(input_totals) >= UNUSED_MIN_SESSIONS
            and cache_pct < CX_CACHE_HIT_PCT_THRESHOLD
        ):
            findings.append(
                make_finding(
                    'CX-CACHE',
                    'med',
                    f'cached/input {cache_pct:.0f}% across {len(input_totals)} sessions '
                    f'(<{CX_CACHE_HIT_PCT_THRESHOLD}%)',
                    'avoid mid-session model/effort switches; keep related work in one '
                    'session',
                    0,
                )
            )
    if fills:
        p90_fill = percentile(fills, 0.9)
        p90_fill_pct = round(100 * p90_fill, 1)
        metrics['longctx_p90_fill_pct'] = p90_fill_pct
        if p90_fill > CX_LONGCTX_FILL_THRESHOLD:
            findings.append(
                make_finding(
                    'CX-LONGCTX',
                    'med',
                    f'p90 context fill {p90_fill_pct:.1f}% of window '
                    f'(>{CX_LONGCTX_FILL_THRESHOLD * 100:.0f}%)',
                    'compact earlier; lower model_auto_compact_token_limit',
                    0,
                )
            )
    return findings, metrics, sampled


def check_codex_agents_md(
    home: Path, project: Path, config: dict
) -> tuple[list[Finding], dict[str, object]]:
    cap = int(config.get('project_doc_max_bytes') or CX_AGENTSMD_DEFAULT_CAP_BYTES)
    total = 0
    global_agents = home / '.codex' / 'AGENTS.md'
    if global_agents.is_file():
        total += len(read_text_capped(global_agents, MAX_BYTES_PER_FILE).encode('utf-8'))
    git_root = find_git_root(project) or project
    current = project
    while True:
        candidate = current / 'AGENTS.md'
        if candidate.is_file():
            total += len(read_text_capped(candidate, MAX_BYTES_PER_FILE).encode('utf-8'))
        if current == git_root:
            break
        if current.parent == current:
            break
        current = current.parent

    findings = []
    if total > cap:
        findings.append(
            make_finding(
                'CX-AGENTSMD-CAP',
                'med',
                f'combined AGENTS.md chain is {total} bytes (>{cap} '
                f'project_doc_max_bytes, truncated)',
                'trim AGENTS.md or raise project_doc_max_bytes',
                chars_to_tokens(total - cap),
            )
        )
    return findings, {'agents_md_bytes': total, 'agents_md_cap_bytes': cap}


def check_codex_mcp(config: dict) -> tuple[list[Finding], dict[str, object]]:
    servers = get_dict(config, 'mcp_servers')
    if not servers:
        return [], {}
    no_allowlist = [
        name
        for name, cfg in servers.items()
        if isinstance(cfg, dict)
        and cfg.get('enabled', True)
        and not cfg.get('enabled_tools')
        and not cfg.get('disabled_tools')
    ]
    findings = []
    if no_allowlist:
        findings.append(
            make_finding(
                'CX-MCP',
                'low',
                f'{len(no_allowlist)}/{len(servers)} MCP servers enabled with no tool '
                f'allowlist',
                'set enabled_tools to narrow each server',
                0,
                names=no_allowlist,
            )
        )
    return findings, {'mcp_servers': len(servers)}


def check_codex_effort(config: dict) -> tuple[list[Finding], dict[str, object]]:
    effort = config.get('model_reasoning_effort')
    findings = []
    if effort in ('high', 'xhigh', 'max'):
        findings.append(
            make_finding(
                'CX-EFFORT',
                'info',
                f'model_reasoning_effort={effort} globally',
                'use medium by default; raise per-task when it stalls',
                0,
            )
        )
    metrics = {'model_reasoning_effort': effort} if effort else {}
    return findings, metrics


def codex_skills_budget_chars(windowed: WindowedFiles, config: dict) -> int:
    """Codex's real skills-listing budget: skills.max_context_tokens from
    config.toml if set, else 2% of the latest session's model_context_window,
    else the illustrative 8,000-char fallback. Both token figures are
    converted to chars with the collector's chars-per-token ratio, since the
    finding compares against a char total."""
    skills_config = config.get('skills')
    max_tokens = (
        skills_config.get('max_context_tokens')
        if isinstance(skills_config, dict)
        else None
    )
    if isinstance(max_tokens, int | float) and max_tokens > 0:
        return tokens_to_chars(max_tokens)
    window = latest_codex_context_window(windowed)
    if window:
        return tokens_to_chars(window * CX_SKILLS_BUDGET_TOKEN_FRACTION)
    return CX_SKILLS_CHAR_LIMIT


def codex_disabled_skill_paths(config: dict) -> set[Path]:
    # [[skills.config]] entries name a skill by its SKILL.md path or its
    # folder; accept either form and resolve so ~ and relative bits match.
    skills_config = config.get('skills')
    entries = skills_config.get('config') if isinstance(skills_config, dict) else None
    if not isinstance(entries, list):
        return set()
    disabled: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('enabled', True):
            continue
        raw_path = entry.get('path')
        if isinstance(raw_path, str) and raw_path:
            disabled.add(Path(raw_path).expanduser().resolve())
    return disabled


def _codex_skill_disabled(skill_path: Path, disabled: set[Path]) -> bool:
    if not disabled:
        return False
    resolved = skill_path.resolve()
    return resolved in disabled or resolved.parent in disabled


def check_codex_skills(
    home: Path, config: dict, windowed: WindowedFiles
) -> tuple[list[Finding], dict[str, object]]:
    skill_files = scan_skill_dir(home / '.agents' / 'skills', 'codex') + scan_skill_dir(
        home / '.codex' / 'skills', 'codex'
    )
    disabled = codex_disabled_skill_paths(config)
    skill_files = [s for s in skill_files if not _codex_skill_disabled(s.path, disabled)]
    if not skill_files:
        return [], {}
    total_chars = sum(len(s.name) + s.description_len for s in skill_files)
    budget_chars = codex_skills_budget_chars(windowed, config)
    findings = []
    if total_chars > budget_chars:
        findings.append(
            make_finding(
                'CX-SKILLS',
                'low',
                f'{len(skill_files)} skill descriptions+names total {total_chars} chars '
                f'(>{budget_chars}, Codex truncates the listing)',
                'trim descriptions or consolidate skills exposed to Codex',
                0,
                names=[s.name for s in skill_files],
            )
        )
    return findings, {'skills': len(skill_files), 'skills_budget_chars': budget_chars}


def collect_codex(
    home: Path, project: Path, days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    config, config_ok = read_codex_config(home)
    windowed = codex_session_paths(home, days)
    findings: list[Finding] = []
    metrics: dict[str, object] = {}
    if not config_ok:
        metrics['config_note'] = 'config.toml unreadable'

    f, m, sampled = check_codex_sessions(windowed)
    findings.extend(f)
    metrics.update(m)

    f, m = check_codex_agents_md(home, project, config)
    findings.extend(f)
    metrics.update(m)

    f, m = check_codex_mcp(config)
    findings.extend(f)
    metrics.update(m)

    f, m = check_codex_effort(config)
    findings.extend(f)
    metrics.update(m)

    f, m = check_codex_skills(home, config, windowed)
    findings.extend(f)
    metrics.update(m)

    return findings, metrics, sampled
