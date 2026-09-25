#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Deterministic, stdlib-only evidence collector for the optimize-ai-setup skill.

Reads configs and session logs for every installed AI coding harness on this
machine and prints a compact, secret-free evidence report. No LLM reads raw
logs or configs directly: it only reads this report.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import shutil
import sys
import time
import tomllib
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

# --- Tunables (module constants so a check's ceiling is grep-able) ---

DEFAULT_DAYS = 14
MAX_FILES_PER_HARNESS = 2000
MAX_BYTES_PER_FILE = 50 * 1024 * 1024
MAX_LOG_TAIL_BYTES = 2 * 1024 * 1024
MAX_SKILL_FILES = 400
TOP_FINDINGS_DEFAULT = 15

STARTUP_MED_TOKENS = 30_000
STARTUP_HIGH_TOKENS = 50_000
LONGCTX_P90_TOKENS = 400_000
UNUSED_MIN_SESSIONS = 5
SKILL_LISTING_TOKEN_LIMIT = 8_000
SKILL_DESC_CHAR_LIMIT = 1_536
HOOK_SESSIONSTART_TOKEN_LIMIT = 500
HOOK_SESSIONSTART_TOKEN_MED = 2_000
HOOK_USERPROMPT_TOKEN_LIMIT = 125
MEMORY_FILE_LINE_LIMIT = 200
MEMORY_TOTAL_TOKENS_MED = 5_000
MEMORY_TOTAL_TOKENS_HIGH = 10_000
REBUILD_MIN_PROMPT_TOKENS = 20_000
TTL_1H_SECONDS = 3600
TTL_5M_SECONDS = 300
MCP_OUTPUT_TOKEN_LIMIT = 25_000
CX_AGENTSMD_DEFAULT_CAP_BYTES = 32_768
CX_LONGCTX_FILL_THRESHOLD = 0.70
CX_CACHE_HIT_PCT_THRESHOLD = 80
CX_SKILLS_CHAR_LIMIT = 8_000
CX_SKILLS_BUDGET_TOKEN_FRACTION = 0.02
CRUFT_HITS_PER_1K_CHARS = 2.0

FMT_MILLION = 1_000_000
FMT_THOUSAND = 1_000
CHARS_PER_TOKEN = 4
MCP_TOOL_NAME_PARTS = 2
REBUILD_HIGH_IDLE_COUNT = 20
REBUILD_WRITE_SHARE = 0.5
REBUILD_READ_SHARE = 0.5
EFFORT_HIGH_SHARE_PCT = 70
DUP_INSTR_OVERLAP = 0.6
MODEL_MAJORITY_SHARE = 0.5
MODEL_SHARE_DISPLAY_MIN_PCT = 0.5
SYNTHETIC_MODEL_NAME = '<synthetic>'
MIN_MEMORY_FILES_TO_COMPARE = 2

SEVERITY_ORDER = {'high': 0, 'med': 1, 'low': 2, 'info': 3}


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    evidence: str
    fix: str
    impact_tokens: int
    harness: str = ''
    names: list[str] = field(default_factory=list)


def make_finding(  # noqa: PLR0913 -- names is an optional 6th arg on an established 5-arg helper
    check_id: str,
    severity: str,
    evidence: str,
    fix: str,
    impact_tokens: float,
    names: list[str] | None = None,
) -> Finding:
    # harness is filled in by run() once a collector's findings come back,
    # since every finding from one collector shares the same harness.
    # names holds the finding's concrete items, for a render step to cite.
    return Finding(
        id=check_id,
        severity=severity,
        evidence=evidence[:160],
        fix=fix[:80],
        impact_tokens=int(impact_tokens),
        names=list(names) if names else [],
    )


# --- Generic, safety-first utilities shared by every collector ---


def fmt_num(value: float) -> str:
    value = float(value)
    if abs(value) >= FMT_MILLION:
        return f'{value / FMT_MILLION:.1f}M'
    if abs(value) >= FMT_THOUSAND:
        return f'{value / FMT_THOUSAND:.1f}K'
    return f'{value:.0f}'


def chars_to_tokens(chars: int) -> int:
    # ponytail: chars/4 token estimate, real tokenizer would be +/-20%
    return chars // CHARS_PER_TOKEN


def tokens_to_chars(tokens: float) -> int:
    return int(tokens) * CHARS_PER_TOKEN


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(pct * (len(ordered) - 1))))
    return ordered[idx]


def median(values: list[float]) -> float:
    return percentile(values, 0.5)


FORBIDDEN_EXACT_NAMES = {'auth.json', 'oauth_creds.json', 'google_accounts.json'}
FORBIDDEN_NAME_RE = re.compile(r'(cred|oauth|token)', re.IGNORECASE)


def is_forbidden_path(path: Path) -> bool:
    name = path.name
    if name in FORBIDDEN_EXACT_NAMES or name.endswith('.env'):
        return True
    return bool(name.endswith('.json') and FORBIDDEN_NAME_RE.search(name))


PLACEHOLDER_RE = re.compile(r'^\$\{[A-Za-z_][A-Za-z0-9_]*\}$')


def looks_like_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.match(value.strip()))


def compact_path(path: Path, home: Path) -> str:
    try:
        return f'~/{path.relative_to(home)}'
    except ValueError:
        return path.name


def read_json_checked(path: Path) -> tuple[dict, bool]:
    """Returns (data, ok). ok is False only when the file exists but could not
    be parsed, so callers can report it instead of silently looking empty."""
    if is_forbidden_path(path) or not path.is_file():
        return {}, True
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='ignore')), True
    except (OSError, json.JSONDecodeError, ValueError):
        return {}, False


def read_json(path: Path) -> dict:
    return read_json_checked(path)[0]


def mcp_server_names(config: dict) -> set[str]:
    return set((config.get('mcpServers') or {}).keys())


def read_text_capped(path: Path, max_bytes: int) -> str:
    if is_forbidden_path(path):
        return ''
    try:
        with path.open(encoding='utf-8', errors='ignore') as fh:
            return fh.read(max_bytes)
    except OSError:
        return ''


@dataclass(frozen=True)
class WindowedFiles:
    paths: list[Path]
    total_in_window: int

    @property
    def sampled(self) -> bool:
        return len(self.paths) < self.total_in_window


def select_in_window(
    candidates: Iterable[Path], days: int, cap: int = MAX_FILES_PER_HARNESS
) -> WindowedFiles:
    cutoff = time.time() - days * 86400
    dated: list[tuple[float, Path]] = []
    for candidate in candidates:
        if is_forbidden_path(candidate):
            continue
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            dated.append((mtime, candidate))
    dated.sort(key=lambda pair: pair[0], reverse=True)
    return WindowedFiles([p for _, p in dated[:cap]], len(dated))


def iter_filtered_lines(
    path: Path, needles: tuple[str, ...], max_bytes: int = MAX_BYTES_PER_FILE
) -> Iterator[str]:
    if is_forbidden_path(path):
        return
    read = 0
    try:
        with path.open(encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                read += len(line)
                if read > max_bytes:
                    return
                if any(needle in line for needle in needles):
                    yield line
    except OSError:
        return


def find_git_root(start: Path) -> Path | None:
    current = start
    while True:
        if (current / '.git').exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


CODE_FENCE_RE = re.compile(r'```.*?```', re.DOTALL)
INLINE_CODE_RE = re.compile(r'`[^`]*`')
IMPORT_RE = re.compile(r'@([\w./~-]+\.md)')


def find_imports(text: str) -> list[str]:
    stripped = CODE_FENCE_RE.sub('', text)
    lines = [INLINE_CODE_RE.sub('', line) for line in stripped.splitlines()]
    return IMPORT_RE.findall('\n'.join(lines))


def resolve_import_path(ref: str, base_dir: Path, home: Path) -> Path:
    if ref.startswith('~/'):
        return (home / ref[2:]).resolve()
    return (base_dir / ref).resolve()


def has_paths_frontmatter(text: str) -> bool:
    if not text.startswith('---'):
        return False
    end = text.find('\n---', 3)
    if end == -1:
        return False
    return bool(re.search(r'^paths\s*:', text[3:end], re.MULTILINE))


def extract_frontmatter_field_len(text: str, field_name: str) -> int:
    if not text.startswith('---'):
        return 0
    end = text.find('\n---', 3)
    if end == -1:
        return 0
    frontmatter = text[3:end]
    match = re.search(rf'^{field_name}:\s*(.*)$', frontmatter, re.MULTILINE)
    if not match:
        return 0
    lines = frontmatter[match.start() :].splitlines()
    collected = [lines[0].split(':', 1)[1]]
    for line in lines[1:]:
        if re.match(r'^[A-Za-z_][\w-]*:', line):
            break
        collected.append(line)
    return len('\n'.join(collected))


CRUFT_PHRASE_RE = re.compile(
    r'double-check|verify twice|be maximally thorough|CRITICAL: YOU MUST|think step by '
    r'step',
    re.IGNORECASE,
)
CAPS_WORD_RE = re.compile(r'\b(?:MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL)\b')


def prompt_cruft_hits(texts: list[str]) -> tuple[int, int]:
    phrase_hits = sum(len(CRUFT_PHRASE_RE.findall(t)) for t in texts)
    caps_hits = sum(len(CAPS_WORD_RE.findall(t)) for t in texts)
    return phrase_hits, caps_hits


# --- Claude Code memory chain (shared by CC-MEMORY and CC-PROMPT-CRUFT) ---


def collect_memory_files(home: Path, project: Path) -> dict[Path, str]:
    files: dict[Path, str] = {}
    candidates: list[Path] = [home / '.claude' / 'CLAUDE.md']
    rules_dir = home / '.claude' / 'rules'
    if rules_dir.is_dir():
        candidates.extend(sorted(rules_dir.glob('*.md')))

    # Claude Code loads CLAUDE.md walking every ancestor directory up to (not
    # including) the filesystem root, not just up to the project's git root,
    # so ~/CLAUDE.md loads for any project under the home dir.
    walked: list[Path] = []
    current = project
    while True:
        walked.append(current)
        if current.parent == current:
            break
        current = current.parent
    if walked and walked[-1].parent == walked[-1]:
        walked.pop()

    for directory in reversed(walked):
        candidates.append(directory / 'CLAUDE.md')
        candidates.append(directory / '.claude' / 'CLAUDE.md')
        candidates.append(directory / 'CLAUDE.local.md')
        project_rules = directory / '.claude' / 'rules'
        if project_rules.is_dir():
            candidates.extend(sorted(project_rules.glob('*.md')))

    for path in candidates:
        if path in files or not path.is_file():
            continue
        text = read_text_capped(path, MAX_BYTES_PER_FILE)
        if text:
            files[path] = text
    return files


def resolve_memory_imports(
    always_loaded: dict[Path, str], home: Path, max_hops: int = 4
) -> dict[Path, str]:
    imported: dict[Path, str] = {}
    seen = set(always_loaded)
    frontier = list(always_loaded.items())
    hop = 1
    while frontier and hop <= max_hops:
        next_frontier: list[tuple[Path, str]] = []
        for path, text in frontier:
            for ref in find_imports(text):
                target = resolve_import_path(ref, path.parent, home)
                if target in seen or not target.is_file():
                    continue
                target_text = read_text_capped(target, MAX_BYTES_PER_FILE)
                if not target_text:
                    continue
                seen.add(target)
                imported[target] = target_text
                next_frontier.append((target, target_text))
        frontier = next_frontier
        hop += 1
    return imported


def check_memory(
    home: Path, project: Path
) -> tuple[list[Finding], dict[str, object], list[str]]:
    files = collect_memory_files(home, project)
    always_loaded = {p: t for p, t in files.items() if not has_paths_frontmatter(t)}
    imported = resolve_memory_imports(always_loaded, home)

    findings: list[Finding] = []
    for path, text in always_loaded.items():
        line_count = text.count('\n') + 1
        if line_count > MEMORY_FILE_LINE_LIMIT:
            findings.append(
                make_finding(
                    'CC-MEMORY',
                    'med',
                    f'{compact_path(path, home)} is {line_count} lines (>200)',
                    'split into skills or path-scoped .claude/rules',
                    chars_to_tokens(len(text)),
                )
            )

    total_tokens = chars_to_tokens(
        sum(len(t) for t in always_loaded.values())
        + sum(len(t) for t in imported.values())
    )
    if total_tokens > MEMORY_TOTAL_TOKENS_HIGH:
        findings.append(
            make_finding(
                'CC-MEMORY',
                'high',
                f'always-loaded memory {fmt_num(total_tokens)} tok (>10K) across '
                f'{len(always_loaded) + len(imported)} files',
                'move workflows into skills or path-scoped rules',
                total_tokens,
            )
        )
    elif total_tokens > MEMORY_TOTAL_TOKENS_MED:
        findings.append(
            make_finding(
                'CC-MEMORY',
                'med',
                f'always-loaded memory {fmt_num(total_tokens)} tok (>5K) across '
                f'{len(always_loaded) + len(imported)} files',
                'move workflows into skills or path-scoped rules',
                total_tokens,
            )
        )

    metrics = {
        'always_loaded_tok': total_tokens,
        'files': len(always_loaded) + len(imported),
    }
    memory_texts = list(always_loaded.values()) + list(imported.values())
    return findings, metrics, memory_texts


# --- Claude Code skills (listing size, duplicates, description length, unused) ---


@dataclass(frozen=True)
class SkillFile:
    name: str
    source: str
    description_len: int
    text: str
    path: Path = Path()


def scan_skill_dir(root: Path, source: str) -> list[SkillFile]:
    if not root.is_dir():
        return []
    out: list[SkillFile] = []
    for md_path in sorted(root.glob('*/SKILL.md'))[:MAX_SKILL_FILES]:
        text = read_text_capped(md_path, MAX_BYTES_PER_FILE)
        if not text:
            continue
        name_match = re.search(r'^name:\s*(\S+)', text, re.MULTILINE)
        name = name_match.group(1) if name_match else md_path.parent.name
        desc_len = extract_frontmatter_field_len(text, 'description')
        out.append(SkillFile(name, source, desc_len, text, md_path))
    return out


def check_skill_descriptions(
    home: Path, project: Path
) -> tuple[list[Finding], list[str]]:
    skill_files = scan_skill_dir(home / '.claude' / 'skills', 'user') + scan_skill_dir(
        project / '.claude' / 'skills', 'project'
    )
    findings: list[Finding] = []
    for skill in skill_files:
        if skill.description_len > SKILL_DESC_CHAR_LIMIT:
            findings.append(
                make_finding(
                    'CC-SKILL-LISTING',
                    'low',
                    f'{skill.name} ({skill.source}) description {skill.description_len} '
                    f'chars (>1536, truncated)',
                    'trim the description below 1536 chars',
                    0,
                )
            )
    return findings, [s.text for s in skill_files]


# --- Claude Code transcript parsing ---

TRANSCRIPT_NEEDLES = ('"usage"', '"attachment"', '"tool_use"', '<command-name>')
SLASH_RE = re.compile(r'<command-name>([^<]+)</command-name>')


def _parse_ts(value: object) -> float:
    if not isinstance(value, str):
        return 0.0
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except ValueError:
        return 0.0


def _mcp_server_of(tool_name: str) -> str | None:
    if not tool_name.startswith('mcp__'):
        return None
    parts = tool_name.split('__')
    return parts[1] if len(parts) >= MCP_TOOL_NAME_PARTS else None


def _attachment_chars(value: object) -> int:
    # A hook_additional_context attachment's `content` is a list of persisted-
    # output strings; hook_success/hook_non_blocking_error's is a plain string.
    if isinstance(value, list):
        return sum(len(str(v)) for v in value)
    return len(value) if isinstance(value, str) else 0


@dataclass
class SessionRequest:
    ts: float
    model: str | None
    effort: str | None
    version: str | None
    is_sidechain: bool
    input_tok: int
    write_1h: int
    write_5m: int
    read_tok: int

    @property
    def prompt_tok(self) -> int:
        return self.input_tok + self.write_1h + self.write_5m + self.read_tok

    @property
    def write_tok(self) -> int:
        return self.write_1h + self.write_5m


@dataclass
class SessionData:
    requests: list[SessionRequest] = field(default_factory=list)
    skill_listing_chars: int = 0  # size of the startup listing only, not summed
    startup_skill_names: list[str] = field(default_factory=list)
    deferred_tool_names: set[str] = field(default_factory=set)
    deferred_chars_by_server: Counter = field(default_factory=Counter)
    mcp_instr_chars_by_server: Counter = field(default_factory=Counter)
    hook_chars: dict[str, list[int]] = field(default_factory=dict)
    startup_hook_chars: int = 0  # hook chars seen before the first main-thread request
    skill_uses: Counter = field(default_factory=Counter)
    mcp_uses: Counter = field(default_factory=Counter)
    slash_uses: Counter = field(default_factory=Counter)


def _record_usage(session: SessionData, seen: set[str], obj: dict) -> None:
    message = obj.get('message') or {}
    usage = message.get('usage')
    if not usage:
        return
    request_id = obj.get('requestId') or message.get('id')
    if not request_id or request_id in seen:
        return
    seen.add(request_id)
    cache_creation = usage.get('cache_creation') or {}
    session.requests.append(
        SessionRequest(
            ts=_parse_ts(obj.get('timestamp')),
            model=message.get('model'),
            effort=obj.get('effort'),
            version=obj.get('version'),
            is_sidechain=bool(obj.get('isSidechain')),
            input_tok=int(usage.get('input_tokens') or 0),
            write_1h=int(cache_creation.get('ephemeral_1h_input_tokens') or 0),
            write_5m=int(cache_creation.get('ephemeral_5m_input_tokens') or 0),
            read_tok=int(usage.get('cache_read_input_tokens') or 0),
        )
    )


def _record_attachment(
    session: SessionData, obj: dict, *, count_for_startup: bool
) -> None:
    # Only attachments seen before a session's first main-thread usage line are
    # genuine startup-context bloat; later deltas/listings must not inflate the
    # startup breakdown (see check_startup). Skill names are still unioned
    # regardless, since CC-SKILL-DUP/UNUSED need every listing, not just the first.
    attachment = obj.get('attachment') or {}
    kind = attachment.get('type')
    if kind == 'skill_listing':
        content = attachment.get('content') or ''
        # The listing text wraps descriptions over several lines; `names` is the
        # authoritative list (plugin skills arrive qualified, e.g. `plugin:skill`).
        names = [n for n in attachment.get('names') or [] if isinstance(n, str)]
        if count_for_startup:
            session.startup_skill_names = names
            session.skill_listing_chars = len(content)
    elif kind == 'deferred_tools_delta':
        # Server names are unioned from every delta, startup or not: a
        # connector (claude.ai Vercel, a plugin MCP stub) can surface tools
        # mid-session, and CC-MCP-UNUSED needs it counted as configured either
        # way. Only the startup char accounting stays gated (see check_startup).
        names = attachment.get('addedNames') or []
        for name in names:
            server = _mcp_server_of(str(name))
            if server:
                session.deferred_tool_names.add(server)
        if not count_for_startup:
            return
        lines = attachment.get('addedLines') or names
        for name, line in zip(names, lines, strict=False):
            server = _mcp_server_of(str(name)) or 'builtin'
            session.deferred_chars_by_server[server] += len(str(line))
    elif kind == 'mcp_instructions_delta':
        if not count_for_startup:
            return
        names = attachment.get('addedNames') or []
        blocks = attachment.get('addedBlocks') or []
        for name, block in zip(names, blocks, strict=False):
            session.mcp_instr_chars_by_server[str(name)] += len(str(block))
    elif kind in ('hook_success', 'hook_non_blocking_error', 'hook_additional_context'):
        hook_name = attachment.get('hookName') or 'unknown'
        # `stdout` is the hook's raw, un-truncated process output, not what
        # enters context: an oversized additionalContext gets diverted to a
        # separate hook_additional_context attachment instead, leaving
        # `content` empty here. Falling back to stdout massively overcounts.
        chars = _attachment_chars(attachment.get('content'))
        session.hook_chars.setdefault(hook_name, []).append(chars)
        if count_for_startup:
            session.startup_hook_chars += chars


def _record_tool_use(session: SessionData, obj: dict) -> None:
    content = (obj.get('message') or {}).get('content')
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get('type') != 'tool_use':
            continue
        name = block.get('name') or ''
        if name == 'Skill':
            skill = (block.get('input') or {}).get('skill')
            if skill:
                session.skill_uses[skill] += 1
        else:
            server = _mcp_server_of(name)
            if server:
                session.mcp_uses[server] += 1


def parse_transcript(path: Path, *, is_sidechain_file: bool = False) -> SessionData:
    session = SessionData()
    seen: set[str] = set()
    # Subagent (sidechain) files never precede the parent session's first
    # main-thread request in real time, so nothing in them is "startup".
    startup_ended = is_sidechain_file
    for line in iter_filtered_lines(path, TRANSCRIPT_NEEDLES):
        for command in SLASH_RE.findall(line):
            session.slash_uses[command.strip()] += 1
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue
        if is_sidechain_file:
            obj['isSidechain'] = True
        if obj.get('type') == 'attachment':
            _record_attachment(session, obj, count_for_startup=not startup_ended)
        elif obj.get('type') == 'assistant':
            if not startup_ended and not obj.get('isSidechain'):
                message = obj.get('message') or {}
                if message.get('usage'):
                    startup_ended = True
            _record_usage(session, seen, obj)
            _record_tool_use(session, obj)
    return session


def merge_session(target: SessionData, source: SessionData) -> None:
    target.requests.extend(source.requests)
    target.deferred_tool_names.update(source.deferred_tool_names)
    target.deferred_chars_by_server.update(source.deferred_chars_by_server)
    target.mcp_instr_chars_by_server.update(source.mcp_instr_chars_by_server)
    for hook_name, lengths in source.hook_chars.items():
        target.hook_chars.setdefault(hook_name, []).extend(lengths)
    target.startup_hook_chars += source.startup_hook_chars
    target.skill_uses.update(source.skill_uses)
    target.mcp_uses.update(source.mcp_uses)
    target.slash_uses.update(source.slash_uses)


def load_all_sessions(
    claude_home: Path, days: int
) -> tuple[list[SessionData], list[str]]:
    projects_dir = claude_home / 'projects'
    if not projects_dir.is_dir():
        return [], []
    windowed = select_in_window(projects_dir.glob('*/*.jsonl'), days)
    sampled: list[str] = []
    if windowed.sampled:
        sampled.append(
            f'claude-code {len(windowed.paths)}/{windowed.total_in_window} sessions'
        )

    sessions: list[SessionData] = []
    for session_path in windowed.paths:
        session = parse_transcript(session_path)
        subagent_dir = session_path.with_suffix('') / 'subagents'
        if subagent_dir.is_dir():
            for sub_path in sorted(subagent_dir.glob('*.jsonl'))[:MAX_SKILL_FILES]:
                merge_session(session, parse_transcript(sub_path, is_sidechain_file=True))
        sessions.append(session)
    return sessions, sampled


# --- Claude Code: startup, cache, rebuilds, long context, model mix, effort ---


def check_startup(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    starts = [
        s.requests[0].prompt_tok
        for s in sessions
        if s.requests and not s.requests[0].is_sidechain
    ]
    if not starts:
        return [], {}
    med, p90 = median(starts), percentile(starts, 0.9)

    total_listing = sum(s.skill_listing_chars for s in sessions if s.skill_listing_chars)
    n_listing = sum(1 for s in sessions if s.skill_listing_chars) or 1
    avg_listing_tok = chars_to_tokens(total_listing // n_listing)

    deferred: Counter = Counter()
    mcp_instr: Counter = Counter()
    hook_total = 0
    n_deferred = 0
    n_mcp_instr = 0
    n_hook = 0
    for s in sessions:
        if s.deferred_chars_by_server:
            deferred.update(s.deferred_chars_by_server)
            n_deferred += 1
        if s.mcp_instr_chars_by_server:
            mcp_instr.update(s.mcp_instr_chars_by_server)
            n_mcp_instr += 1
        if s.startup_hook_chars:
            hook_total += s.startup_hook_chars
            n_hook += 1
    # ponytail: per-session average attribution, not a sum across every session
    deferred_tok = chars_to_tokens(sum(deferred.values()) // max(n_deferred, 1))
    mcp_instr_tok = chars_to_tokens(sum(mcp_instr.values()) // max(n_mcp_instr, 1))
    hook_tok = chars_to_tokens(hook_total // max(n_hook, 1))

    findings = []
    if med > STARTUP_MED_TOKENS:
        severity = 'high' if med > STARTUP_HIGH_TOKENS else 'med'
        parts = {
            'skill listing': avg_listing_tok,
            'hooks': hook_tok,
            'mcp tool names': deferred_tok,
            'mcp instructions': mcp_instr_tok,
        }
        measured = sum(parts.values())
        top_name, top_tok = max(parts.items(), key=lambda kv: kv[1])
        top_note = (
            f'; measured parts {fmt_num(measured)}, biggest {top_name} {fmt_num(top_tok)}'
            f'; rest is system prompt, tool schemas, memory'
        )
        findings.append(
            make_finding(
                'CC-STARTUP',
                severity,
                f'startup context {fmt_num(med)} tok median '
                f'(>{fmt_num(STARTUP_MED_TOKENS)}){top_note}',
                'prune MCP/skills listed at start; disable unused ones',
                med,
            )
        )
    metrics = {
        'startup_median_tok': int(med),
        'startup_p90_tok': int(p90),
        'skills_tok': avg_listing_tok,
        'mcp_tool_names_tok': deferred_tok,
        'mcp_instructions_tok': mcp_instr_tok,
        'hooks_tok': hook_tok,
    }
    return findings, metrics


def check_cache(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    reqs = [r for s in sessions for r in s.requests]
    if not reqs:
        return [], {}
    prompt_total = sum(r.prompt_tok for r in reqs) or 1
    write_1h = sum(r.write_1h for r in reqs)
    write_5m = sum(r.write_5m for r in reqs)
    reads = sum(r.read_tok for r in reqs)
    uncached = sum(r.input_tok for r in reqs)

    hit_pct = 100 * reads / prompt_total
    write_pct = 100 * (write_1h + write_5m) / prompt_total

    cost = write_1h * 2.0 + write_5m * 1.25 + reads * 0.1 + uncached * 1.0
    write_cost = write_1h * 2.0 + write_5m * 1.25
    write_cost_share = 100 * write_cost / cost if cost else 0.0

    findings = []
    if write_1h and 'DISABLE_PROMPT_CACHING' in os.environ:
        findings.append(
            make_finding(
                'CC-CACHE',
                'high',
                'DISABLE_PROMPT_CACHING is set while cache writes are still happening',
                'unset DISABLE_PROMPT_CACHING*',
                write_cost,
            )
        )
    metrics = {
        'hit_pct': round(hit_pct, 1),
        'write_pct': round(write_pct, 1),
        'write_cost_share_pct': round(write_cost_share, 1),
    }
    return findings, metrics


def _rebuild_ttl(prev: SessionRequest) -> int:
    return TTL_1H_SECONDS if prev.write_1h > 0 else TTL_5M_SECONDS


def _rebuild_cause(prev: SessionRequest, cur: SessionRequest) -> str:
    if prev.model != cur.model:
        return 'model'
    if prev.effort != cur.effort:
        return 'effort'
    if prev.version != cur.version:
        return 'upgrade'
    if prev.prompt_tok and cur.prompt_tok < 0.6 * prev.prompt_tok:
        return 'compaction'
    if cur.ts - prev.ts > _rebuild_ttl(prev):
        return 'idle>ttl'
    return 'unknown'


def check_rebuilds(
    sessions: list[SessionData],
) -> tuple[list[Finding], dict[str, object]]:
    causes: Counter = Counter()
    total_waste = 0
    count = 0
    for session in sessions:
        main = [r for r in session.requests if not r.is_sidechain]
        for prev, cur in itertools.pairwise(main):
            if cur.prompt_tok <= REBUILD_MIN_PROMPT_TOKENS:
                continue
            if cur.write_tok <= REBUILD_WRITE_SHARE * cur.prompt_tok:
                continue
            if cur.read_tok >= REBUILD_READ_SHARE * prev.prompt_tok:
                continue
            count += 1
            total_waste += cur.write_tok
            causes[_rebuild_cause(prev, cur)] += 1

    if count == 0:
        return [], {}

    idle_count = causes.get('idle>ttl', 0)
    findings = []
    severity = (
        'high'
        if idle_count >= REBUILD_HIGH_IDLE_COUNT
        else 'med'
        if idle_count
        else 'low'
    )
    causes_str = ' · '.join(f'{k} {v}' for k, v in causes.most_common())
    findings.append(
        make_finding(
            'CC-REBUILD',
            severity,
            f'{count} rebuilds, {fmt_num(total_waste)} tok rewritten ({causes_str})',
            '/compact before breaks; pin model+effort at session start',
            total_waste,
        )
    )
    metrics = {'rebuilds': count, 'rewritten_tok': total_waste, 'causes': dict(causes)}
    return findings, metrics


def check_longctx(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    peaks = []
    over_threshold = 0
    all_prompts = 0
    for session in sessions:
        main = [r for r in session.requests if not r.is_sidechain]
        if not main:
            continue
        peaks.append(max(r.prompt_tok for r in main))
        for r in main:
            all_prompts += 1
            if r.prompt_tok >= LONGCTX_P90_TOKENS:
                over_threshold += 1
    if not peaks:
        return [], {}

    p50, p90 = median(peaks), percentile(peaks, 0.9)
    pct_over = 100 * over_threshold / max(all_prompts, 1)
    findings = []
    if p90 > LONGCTX_P90_TOKENS:
        findings.append(
            make_finding(
                'CC-LONGCTX',
                'med',
                f'peak context p90 {fmt_num(p90)} tok, {pct_over:.0f}% of turns >= '
                f'{fmt_num(LONGCTX_P90_TOKENS)}',
                '/clear between tasks; /compact <focus>; lower autoCompactWindow',
                p90,
            )
        )
    metrics = {
        'peak_p50_tok': int(p50),
        'peak_p90_tok': int(p90),
        'pct_turns_over_400k': round(pct_over, 1),
    }
    return findings, metrics


def _display_share(counter: Counter, total: int) -> dict[str, float]:
    # <synthetic> is an internal placeholder, not a real model; below-0.5%
    # entries are noise that just clutters the report.
    return {
        m: pct
        for m, t in counter.most_common()
        if m != SYNTHETIC_MODEL_NAME
        and (pct := round(100 * t / total, 1)) >= MODEL_SHARE_DISPLAY_MIN_PCT
    }


def check_model_mix(
    sessions: list[SessionData],
) -> tuple[list[Finding], dict[str, object]]:
    main_tok: Counter = Counter()
    sub_tok: Counter = Counter()
    for session in sessions:
        for r in session.requests:
            bucket = sub_tok if r.is_sidechain else main_tok
            bucket[r.model or 'unknown'] += r.prompt_tok

    findings = []
    metrics: dict[str, object] = {}
    if main_tok:
        total = sum(main_tok.values()) or 1
        metrics['model_share_pct'] = _display_share(main_tok, total)
        top_model, top_tok = main_tok.most_common(1)[0]
        top_share = round(100 * top_tok / total, 1)
        if 'fable' in top_model.lower() and top_tok / total > MODEL_MAJORITY_SHARE:
            findings.append(
                make_finding(
                    'CC-MODEL-MIX',
                    'low',
                    f'{top_model} is {top_share}% of main-thread tokens (2.5x '
                    f'Opus input cost)',
                    'reserve Fable for results that need it; default to Opus/Sonnet',
                    top_tok,
                )
            )
    if sub_tok:
        total_sub = sum(sub_tok.values()) or 1
        metrics['subagent_model_share_pct'] = _display_share(sub_tok, total_sub)
        top_model, top_tok = sub_tok.most_common(1)[0]
        top_share = round(100 * top_tok / total_sub, 1)
        if 'opus' in top_model.lower() and top_tok / total_sub > MODEL_MAJORITY_SHARE:
            findings.append(
                make_finding(
                    'CC-SUBAGENT-MODEL',
                    'med',
                    f'subagents run {top_model} for {top_share}% of subagent tokens',
                    'set model: on the agent/Agent call or CLAUDE_CODE_SUBAGENT_MODEL',
                    top_tok,
                )
            )
    return findings, metrics


def check_effort(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    efforts: Counter = Counter()
    for session in sessions:
        for r in session.requests:
            if not r.is_sidechain and r.effort:
                efforts[r.effort] += 1
    if not efforts:
        return [], {}
    total = sum(efforts.values())
    share = {e: round(100 * c / total, 1) for e, c in efforts.most_common()}
    findings = []
    # "high" is the default effort on most models (Opus 5.5 defaults to medium),
    # so only xhigh/max represent a deliberate, costly elevation worth flagging.
    elevated_pct = share.get('xhigh', 0) + share.get('max', 0)
    if elevated_pct > EFFORT_HIGH_SHARE_PCT:
        findings.append(
            make_finding(
                'CC-EFFORT',
                'low',
                f'xhigh/max effort on {elevated_pct:.0f}% of main-thread turns',
                'default medium; raise only when it stalls',
                0,
            )
        )
    return findings, {'effort_share_pct': share}


def check_hooks(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    # SessionStart is charged per session (sum of that session's invocations);
    # UserPromptSubmit is charged per prompt (every invocation is one prompt).
    session_start_sums: list[int] = []
    user_prompt_chars: list[int] = []
    for session in sessions:
        session_start_total = 0
        has_session_start = False
        for hook_name, lengths in session.hook_chars.items():
            if hook_name.startswith('SessionStart'):
                session_start_total += sum(lengths)
                has_session_start = True
            elif hook_name.startswith('UserPromptSubmit'):
                user_prompt_chars.extend(lengths)
        if has_session_start:
            session_start_sums.append(session_start_total)

    findings = []
    metrics: dict[str, object] = {}
    if session_start_sums:
        avg_tok = chars_to_tokens(sum(session_start_sums) // len(session_start_sums))
        metrics['session_start_hook_tok'] = avg_tok
        if avg_tok > HOOK_SESSIONSTART_TOKEN_LIMIT:
            severity = 'med' if avg_tok > HOOK_SESSIONSTART_TOKEN_MED else 'low'
            findings.append(
                make_finding(
                    'CC-HOOK-INJECT',
                    severity,
                    f'SessionStart hooks inject {fmt_num(avg_tok)} tok avg per session '
                    f'(>{fmt_num(HOOK_SESSIONSTART_TOKEN_LIMIT)})',
                    'trim hook output; move detail into a skill',
                    avg_tok,
                )
            )
    if user_prompt_chars:
        avg_tok = chars_to_tokens(sum(user_prompt_chars) // len(user_prompt_chars))
        metrics['user_prompt_hook_tok'] = avg_tok
        if avg_tok > HOOK_USERPROMPT_TOKEN_LIMIT:
            findings.append(
                make_finding(
                    'CC-HOOK-INJECT',
                    'low',
                    f'UserPromptSubmit hooks inject {fmt_num(avg_tok)} tok avg per '
                    f'prompt (>{fmt_num(HOOK_USERPROMPT_TOKEN_LIMIT)})',
                    'trim hook output; move detail into a skill',
                    avg_tok,
                )
            )
    return findings, metrics


def _split_bare_qualified(names: Iterable[str]) -> tuple[set[str], set[str]]:
    bare = {n for n in names if ':' not in n}
    qualified = {n.split(':', 1)[1] for n in names if ':' in n}
    return bare, qualified


def _by_source(names: list[str]) -> str:
    counts = Counter(n.split(':', 1)[0] if ':' in n else '(user/project)' for n in names)
    return ' · '.join(f'{src} {n}' for src, n in counts.most_common(6))


def check_skill_dup_and_unused(
    sessions: list[SessionData],
) -> tuple[list[Finding], dict[str, object]]:
    # Judge the setup as it is now: the most recent session's startup listing.
    # A union over the window would flag skills since removed or renamed.
    latest = max(
        (s for s in sessions if s.startup_skill_names),
        key=lambda s: s.requests[-1].ts if s.requests else 0.0,
        default=None,
    )
    if latest is None:
        return [], {}
    bare, qualified = _split_bare_qualified(latest.startup_skill_names)
    dups = sorted(bare & qualified)

    skill_uses: Counter = Counter()
    for session in sessions:
        skill_uses.update(session.skill_uses)
    slash_uses: Counter = Counter()
    for session in sessions:
        slash_uses.update(session.slash_uses)

    def used(name: str) -> bool:
        return bool(
            skill_uses.get(name)
            or slash_uses.get(name)
            or any(k.endswith(f':{name}') for k in skill_uses)
        )

    findings = []
    if dups:
        findings.append(
            make_finding(
                'CC-SKILL-DUP',
                'low',
                f'{len(dups)} skills listed twice (bare + plugin-qualified): '
                f'{", ".join(dups[:5])}',
                'symlink or unload one source (user dir vs plugin)',
                0,
                names=dups,
            )
        )

    listing_tok = chars_to_tokens(
        max((s.skill_listing_chars for s in sessions), default=0)
    )
    if listing_tok > SKILL_LISTING_TOKEN_LIMIT:
        findings.append(
            make_finding(
                'CC-SKILL-LISTING',
                'med',
                f'skill listing is {fmt_num(listing_tok)} tok (>8K) across '
                f'{len(latest.startup_skill_names)} skills',
                'disable-model-invocation on rarely used skills',
                listing_tok,
            )
        )

    if len(sessions) >= UNUSED_MIN_SESSIONS:
        unused = sorted(n for n in latest.startup_skill_names if not used(n))
        if unused:
            findings.append(
                make_finding(
                    'CC-SKILL-UNUSED',
                    'low',
                    f'{len(unused)} of {len(latest.startup_skill_names)} listed skills '
                    f'with no uses in {len(sessions)} sessions: {_by_source(unused)}',
                    'skillOverrides: name-only or off (never delete)',
                    0,
                    names=unused,
                )
            )
    return findings, {'skills_listed': len(latest.startup_skill_names)}


def check_plugins(
    home: Path, sessions: list[SessionData]
) -> tuple[list[Finding], dict[str, object]]:
    settings = read_json(home / '.claude' / 'settings.json')
    enabled_plugins = settings.get('enabledPlugins') or []
    if not enabled_plugins or len(sessions) < UNUSED_MIN_SESSIONS:
        return [], {}

    skill_uses: set[str] = set()
    for session in sessions:
        skill_uses.update(session.skill_uses)

    unused = []
    for plugin in enabled_plugins:
        plugin_id = str(plugin).split('@', 1)[0]
        if not any(k.startswith(f'{plugin_id}:') for k in skill_uses):
            unused.append(plugin_id)

    findings = []
    if unused:
        findings.append(
            make_finding(
                'CC-PLUGIN-UNUSED',
                'low',
                f'{len(unused)} enabled plugins with no skill invocations: '
                f'{", ".join(unused[:5])}',
                '/plugin disable <name>',
                0,
                names=unused,
            )
        )
    return findings, {'plugins_enabled': len(enabled_plugins)}


def _configured_mcp_servers(home: Path, project: Path) -> tuple[set[str], bool]:
    servers: set[str] = set()
    claude_json = read_json(home / '.claude.json')
    servers.update(mcp_server_names(claude_json))
    project_entry = (claude_json.get('projects') or {}).get(str(project)) or {}
    servers.update(mcp_server_names(project_entry))
    project_mcp, project_mcp_ok = read_json_checked(project / '.mcp.json')
    servers.update(mcp_server_names(project_mcp))
    return servers, project_mcp_ok


def check_mcp_unused(
    home: Path, project: Path, sessions: list[SessionData]
) -> tuple[list[Finding], dict[str, object]]:
    servers, mcp_json_ok = _configured_mcp_servers(home, project)
    # A connector (claude.ai Vercel, a plugin MCP stub) may never appear in
    # .claude.json/.mcp.json, only in a session's deferred_tools_delta; judge
    # the setup as it is now, from the latest session, same as skill listing.
    latest = max(
        (s for s in sessions if s.deferred_tool_names),
        key=lambda s: s.requests[-1].ts if s.requests else 0.0,
        default=None,
    )
    if latest is not None:
        servers = servers | latest.deferred_tool_names
    metrics: dict[str, object] = {'mcp_servers_configured': len(servers)}
    if not mcp_json_ok:
        metrics['mcp_json_note'] = '.mcp.json unreadable'
    if not servers or len(sessions) < UNUSED_MIN_SESSIONS:
        return [], metrics

    used: set[str] = set()
    for session in sessions:
        used.update(session.mcp_uses)
    unused = sorted(servers - used)

    findings = []
    if unused:
        findings.append(
            make_finding(
                'CC-MCP-UNUSED',
                'low',
                f'{len(unused)}/{len(servers)} configured MCP servers with no calls: '
                f'{", ".join(unused[:5])}',
                '/mcp disable <name>; prefer a CLI tool',
                0,
                names=unused,
            )
        )
    metrics['mcp_servers_used'] = len(used)
    return findings, metrics


# --- Claude Code: settings-based checks (env, toolsearch, observability) ---


ENV_EXACT_KEYS = (
    'ENABLE_TOOL_SEARCH',
    'MAX_THINKING_TOKENS',
    'MAX_MCP_OUTPUT_TOKENS',
    'ANTHROPIC_BASE_URL',
    'CLAUDE_CODE_SUBAGENT_MODEL',
    'CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS',
    'FORCE_PROMPT_CACHING_5M',
    'ENABLE_PROMPT_CACHING_1H',
)
ENV_PREFIX_KEYS = ('DISABLE_PROMPT_CACHING',)


def collect_allowlisted_env(settings: dict) -> dict[str, str]:
    settings_env = settings.get('env') or {}
    found: dict[str, str] = {}
    for source in (settings_env, os.environ):
        for key in ENV_EXACT_KEYS:
            if key in source:
                found.setdefault(key, str(source[key]))
        for prefix in ENV_PREFIX_KEYS:
            for actual_key in source:
                if actual_key.startswith(prefix):
                    found.setdefault(actual_key, str(source[actual_key]))
    return found


def check_env_and_settings(home: Path) -> tuple[list[Finding], dict[str, object]]:
    settings = read_json(home / '.claude' / 'settings.json')
    settings.update(read_json(home / '.claude' / 'settings.local.json'))
    env = collect_allowlisted_env(settings)

    findings = []
    if any(k.startswith('DISABLE_PROMPT_CACHING') for k in env):
        findings.append(
            make_finding(
                'CC-STALE-ENV',
                'high',
                'DISABLE_PROMPT_CACHING* is set: every request re-writes the cache',
                'unset DISABLE_PROMPT_CACHING*',
                0,
            )
        )
    max_mcp_output = env.get('MAX_MCP_OUTPUT_TOKENS')
    if (
        max_mcp_output
        and max_mcp_output.isdigit()
        and int(max_mcp_output) > MCP_OUTPUT_TOKEN_LIMIT
    ):
        findings.append(
            make_finding(
                'CC-STALE-ENV',
                'med',
                f'MAX_MCP_OUTPUT_TOKENS={max_mcp_output} (>25K default cap)',
                'lower MAX_MCP_OUTPUT_TOKENS toward 25000',
                0,
            )
        )

    base_url = env.get('ANTHROPIC_BASE_URL', '')
    is_first_party = base_url == '' or 'anthropic.com' in base_url
    tool_search_off = env.get('ENABLE_TOOL_SEARCH') == 'false'
    betas_disabled = 'CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS' in env
    if (
        tool_search_off
        or betas_disabled
        or (not is_first_party and 'ENABLE_TOOL_SEARCH' not in env)
    ):
        findings.append(
            make_finding(
                'CC-TOOLSEARCH-OFF',
                'med',
                'tool search appears off: every MCP tool schema loads at startup',
                'unset the env forcing it off, or set ENABLE_TOOL_SEARCH=true',
                0,
            )
        )

    if not settings.get('statusLine'):
        findings.append(
            make_finding(
                'CC-OBSERVABILITY',
                'info',
                'no statusLine configured',
                'set statusLine; check /usage and /context each session',
                0,
            )
        )
    return findings, {}


def detect_claude_code(home: Path, _project: Path) -> bool:
    return (
        (home / '.claude' / 'projects').is_dir()
        or (home / '.claude.json').exists()
        or (home / '.claude' / 'settings.json').exists()
    )


def collect_claude_code(
    home: Path, project: Path, days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    sessions, sampled = load_all_sessions(home / '.claude', days)

    findings: list[Finding] = []
    metrics: dict[str, object] = {'sessions': len(sessions)}

    for check in (
        check_startup,
        check_cache,
        check_rebuilds,
        check_longctx,
        check_model_mix,
        check_effort,
        check_hooks,
    ):
        f, m = check(sessions)
        findings.extend(f)
        metrics.update(m)

    f, m = check_skill_dup_and_unused(sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_plugins(home, sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_mcp_unused(home, project, sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_env_and_settings(home)
    findings.extend(f)
    metrics.update(m)

    mem_findings, mem_metrics, memory_texts = check_memory(home, project)
    findings.extend(mem_findings)
    metrics.update(mem_metrics)

    desc_findings, skill_texts = check_skill_descriptions(home, project)
    findings.extend(desc_findings)

    phrase_hits, caps_hits = prompt_cruft_hits(memory_texts + skill_texts)
    corpus_chars = sum(len(t) for t in memory_texts + skill_texts) or 1
    density = (phrase_hits + caps_hits) / (corpus_chars / 1000)
    if phrase_hits or density > CRUFT_HITS_PER_1K_CHARS:
        findings.append(
            make_finding(
                'CC-PROMPT-CRUFT',
                'low',
                f'{phrase_hits} outdated prompt patterns, {caps_hits} '
                f'MUST/NEVER/ALWAYS/CRITICAL hits '
                'in memory + skills',
                'run /claude-api prompt-audit',
                0,
            )
        )

    return findings, metrics, sampled


# --- Codex ---


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
            info = ((obj.get('payload') or {}).get('info')) or {}
            candidate = info.get('model_context_window')
            if isinstance(candidate, int | float) and candidate > 0:
                window = int(candidate)
        if window:
            return window
    return None


def check_codex_sessions(
    home: Path, days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    windowed = codex_session_paths(home, days)
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
            info = ((obj.get('payload') or {}).get('info')) or {}
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
        last_usage = last.get('last_token_usage') or {}
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
    servers = config.get('mcp_servers') or {}
    if not servers:
        return [], {}
    no_allowlist = [
        name
        for name, cfg in servers.items()
        if cfg.get('enabled', True)
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


def codex_skills_budget_chars(home: Path, config: dict, days: int) -> int:
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
    window = latest_codex_context_window(codex_session_paths(home, days))
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
    home: Path, config: dict, days: int
) -> tuple[list[Finding], dict[str, object]]:
    skill_files = scan_skill_dir(home / '.agents' / 'skills', 'codex') + scan_skill_dir(
        home / '.codex' / 'skills', 'codex'
    )
    disabled = codex_disabled_skill_paths(config)
    skill_files = [s for s in skill_files if not _codex_skill_disabled(s.path, disabled)]
    if not skill_files:
        return [], {}
    total_chars = sum(len(s.name) + s.description_len for s in skill_files)
    budget_chars = codex_skills_budget_chars(home, config, days)
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
    findings: list[Finding] = []
    metrics: dict[str, object] = {}
    if not config_ok:
        metrics['config_note'] = 'config.toml unreadable'

    f, m, sampled = check_codex_sessions(home, days)
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

    f, m = check_codex_skills(home, config, days)
    findings.extend(f)
    metrics.update(m)

    return findings, metrics, sampled


# --- Cursor / Antigravity / Gemini CLI / Claude Desktop (config-first) ---


def detect_cursor(home: Path, project: Path) -> bool:
    # A bare ~/.cursor dir alone is not a reliable signal (many tools create
    # stray config dirs); require the app, the CLI, or a real config/project file.
    return (
        Path('/Applications/Cursor.app').exists()
        or (home / 'Applications' / 'Cursor.app').exists()
        or shutil.which('cursor-agent') is not None
        or (home / '.cursor' / 'mcp.json').exists()
        or (project / '.cursor').is_dir()
        or (project / '.cursorrules').exists()
    )


def collect_cursor(
    home: Path, project: Path, _days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    findings: list[Finding] = []
    always_apply_chars = 0
    rule_count = 0
    for rules_dir in (project / '.cursor' / 'rules',):
        if not rules_dir.is_dir():
            continue
        for md in rules_dir.glob('*.mdc'):
            text = read_text_capped(md, MAX_BYTES_PER_FILE)
            rule_count += 1
            if re.search(r'^alwaysApply:\s*true', text, re.MULTILINE):
                always_apply_chars += len(text)

    legacy = project / '.cursorrules'
    if legacy.is_file():
        always_apply_chars += len(read_text_capped(legacy, MAX_BYTES_PER_FILE))

    tok = chars_to_tokens(always_apply_chars)
    if tok > MEMORY_TOTAL_TOKENS_MED:
        findings.append(
            make_finding(
                'CU-RULES',
                'med',
                f'alwaysApply rules total {fmt_num(tok)} tok (>5K) across {rule_count} '
                f'.mdc files',
                'narrow globs or drop alwaysApply on rarely needed rules',
                tok,
            )
        )

    server_count = len(
        mcp_server_names(read_json(home / '.cursor' / 'mcp.json'))
        | mcp_server_names(read_json(project / '.cursor' / 'mcp.json'))
    )
    if server_count:
        metrics = {'mcp_servers': server_count, 'always_apply_rules_tok': tok}
    else:
        metrics = {'always_apply_rules_tok': tok}
    return findings, metrics, []


def detect_antigravity(home: Path, _project: Path) -> bool:
    return (home / '.gemini' / 'antigravity').is_dir()


def collect_antigravity(
    home: Path, project: Path, _days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    mcp_config = read_json(home / '.gemini' / 'antigravity' / 'mcp_config.json')
    server_count = len(mcp_server_names(mcp_config))

    rule_files = [home / '.gemini' / 'GEMINI.md', home / '.gemini' / 'AGENTS.md']
    rules_dir = home / '.gemini' / 'config' / 'rules'
    if rules_dir.is_dir():
        rule_files.extend(rules_dir.glob('*.md'))
    project_rules = project / '.agents' / 'rules'
    if project_rules.is_dir():
        rule_files.extend(project_rules.glob('*.md'))
    total_chars = sum(
        len(read_text_capped(p, MAX_BYTES_PER_FILE)) for p in rule_files if p.is_file()
    )
    tok = chars_to_tokens(total_chars)

    findings = []
    if tok > MEMORY_TOTAL_TOKENS_MED:
        findings.append(
            make_finding(
                'AG-RULES',
                'med',
                f'GEMINI.md/AGENTS.md/rules total {fmt_num(tok)} tok (>5K)',
                'trim to what every task needs; move the rest into skills',
                tok,
            )
        )
    metrics = {'mcp_servers': server_count, 'rules_tok': tok, 'token_data': 'unavailable'}
    return findings, metrics, []


def detect_gemini(_home: Path, _project: Path) -> bool:
    # ~/.gemini (settings.json, tmp/*/chats) is shared with Antigravity, so only
    # the CLI binary proves Gemini CLI is installed.
    return shutil.which('gemini') is not None


def collect_gemini(
    home: Path, project: Path, _days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    settings = read_json(home / '.gemini' / 'settings.json')
    server_count = len(mcp_server_names(settings))
    file_name = ((settings.get('context') or {}).get('fileName')) or 'GEMINI.md'
    if isinstance(file_name, list):
        file_name = file_name[0] if file_name else 'GEMINI.md'

    total_chars = 0
    for candidate in (home / '.gemini' / str(file_name), project / str(file_name)):
        if candidate.is_file():
            total_chars += len(read_text_capped(candidate, MAX_BYTES_PER_FILE))
    tok = chars_to_tokens(total_chars)

    findings = []
    if tok > MEMORY_TOTAL_TOKENS_MED:
        findings.append(
            make_finding(
                'GM-CONTEXT',
                'med',
                f'{file_name} chain is {fmt_num(tok)} tok (>5K)',
                'trim; consider splitting workflow-specific detail out',
                tok,
            )
        )
    metrics = {'mcp_servers': server_count, 'context_tok': tok}
    return findings, metrics, []


def detect_claude_desktop(home: Path, _project: Path) -> bool:
    return (
        home / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    ).exists()


def collect_claude_desktop(
    home: Path, _project: Path, _days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    app_dir = home / 'Library' / 'Application Support' / 'Claude'
    config = read_json(app_dir / 'claude_desktop_config.json')
    servers = sorted(mcp_server_names(config))

    log_dir = home / 'Library' / 'Logs' / 'Claude'
    unused = []
    for server in servers:
        log_path = log_dir / f'mcp-server-{server}.log'
        if not log_path.is_file():
            continue
        try:
            size = log_path.stat().st_size
            with log_path.open('rb') as fh:
                if size > MAX_LOG_TAIL_BYTES:
                    fh.seek(-MAX_LOG_TAIL_BYTES, os.SEEK_END)
                tail = fh.read().decode('utf-8', errors='ignore')
        except OSError:
            continue
        if 'tools/call' not in tail:
            unused.append(server)

    findings = []
    if unused:
        findings.append(
            make_finding(
                'CD-MCP-UNUSED',
                'low',
                f'{len(unused)}/{len(servers)} MCP servers with no tools/call in their '
                f'log: '
                f'{", ".join(unused[:5])}',
                'remove or disable the unused connector',
                0,
                names=unused,
            )
        )
    metrics = {'mcp_servers': len(servers)}
    return findings, metrics, []


# --- Cross-tool checks ---


def collect_cross_tool(project: Path) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []

    memory_names = ('CLAUDE.md', 'AGENTS.md', 'GEMINI.md')
    present = {
        name: project / name for name in memory_names if (project / name).is_file()
    }
    if len(present) >= MIN_MEMORY_FILES_TO_COMPARE:
        texts = {
            name: read_text_capped(path, MAX_BYTES_PER_FILE)
            for name, path in present.items()
        }
        claude_text = texts.get('CLAUDE.md', '')
        imports_agents = '@AGENTS.md' in claude_text
        names = list(present)
        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                lines_a = {
                    line.strip() for line in texts[name_a].splitlines() if line.strip()
                }
                lines_b = {
                    line.strip() for line in texts[name_b].splitlines() if line.strip()
                }
                if not lines_a or not lines_b:
                    continue
                overlap = len(lines_a & lines_b) / min(len(lines_a), len(lines_b))
                if overlap > DUP_INSTR_OVERLAP and not imports_agents:
                    findings.append(
                        make_finding(
                            'X-DUP-INSTR',
                            'low',
                            f'{name_a} and {name_b} overlap {overlap * 100:.0f}% with no '
                            f'@AGENTS.md import',
                            'keep AGENTS.md as source; add @AGENTS.md to CLAUDE.md',
                            0,
                        )
                    )

    for config_path in (project / '.mcp.json', project / '.cursor' / 'mcp.json'):
        config = read_json(config_path)
        for server_name, server_cfg in (config.get('mcpServers') or {}).items():
            if not isinstance(server_cfg, dict):
                continue
            values = list((server_cfg.get('env') or {}).values()) + list(
                (server_cfg.get('headers') or {}).values()
            )
            if any(
                isinstance(v, str) and v and not looks_like_placeholder(v) for v in values
            ):
                findings.append(
                    make_finding(
                        'X-MCP-INLINE-SECRET',
                        'high',
                        f'{server_name} in {config_path.name} has a literal value in '
                        f'env/headers',
                        'move to ${VAR} and rotate the secret',
                        0,
                        names=[server_name],
                    )
                )
    return findings, []


# --- Rendering ---


def render_metrics_block(harness: str, metrics: dict[str, object]) -> list[str]:
    lines = [f'[{harness}]']
    if not metrics or not any(metrics.values()):
        lines.append('  nothing to report')
        return lines

    if harness == 'claude-code':
        if 'startup_median_tok' in metrics:
            lines.append(
                f'startup    median {fmt_num(metrics["startup_median_tok"])} tok · '
                f'p90 {fmt_num(metrics["startup_p90_tok"])} tok | '
                f'skills {fmt_num(metrics.get("skills_tok", 0))} · '
                f'mcp tool names {fmt_num(metrics.get("mcp_tool_names_tok", 0))} · '
                f'mcp instructions {fmt_num(metrics.get("mcp_instructions_tok", 0))} · '
                f'hooks {fmt_num(metrics.get("hooks_tok", 0))}'
            )
        if 'hit_pct' in metrics:
            lines.append(
                f'cache      hit {metrics["hit_pct"]}% of prompt tok · '
                f'writes {metrics["write_pct"]}% '
                f'(≈{metrics.get("write_cost_share_pct", 0)}% of cost)'
            )
        if 'rebuilds' in metrics:
            causes = metrics.get('causes') or {}
            causes_str = ' · '.join(f'{k} {v}' for k, v in causes.items())
            lines.append(
                f'rebuilds   {metrics["rebuilds"]} · {fmt_num(metrics["rewritten_tok"])} '
                f'tok | {causes_str}'
            )
        if 'peak_p90_tok' in metrics:
            lines.append(
                f'context    peak p50 {fmt_num(metrics["peak_p50_tok"])} · '
                f'p90 {fmt_num(metrics["peak_p90_tok"])} · '
                f'{metrics.get("pct_turns_over_400k", 0)}% of turns >=400K'
            )
        if metrics.get('model_share_pct'):
            share = ' · '.join(f'{m} {p}%' for m, p in metrics['model_share_pct'].items())
            lines.append(f'{"models":<11}{share}')
        if metrics.get('subagent_model_share_pct'):
            share = ' · '.join(
                f'{m} {p}%' for m, p in metrics['subagent_model_share_pct'].items()
            )
            lines.append(f'{"subagents":<11}{share}')
        if 'always_loaded_tok' in metrics:
            lines.append(
                f'{"memory":<11}always-loaded '
                f'{fmt_num(metrics["always_loaded_tok"])} tok across '
                f'{metrics.get("files", 0)} files'
            )
        if metrics.get('mcp_json_note'):
            lines.append(f'{"note":<11}{metrics["mcp_json_note"]}')
    elif harness == 'codex':
        if 'sessions' in metrics:
            lines.append(f'{"sessions":<11}{metrics.get("sessions", 0)}')
        if 'cache_hit_pct' in metrics:
            lines.append(f'{"cache":<11}{metrics["cache_hit_pct"]}%')
        if 'longctx_p90_fill_pct' in metrics:
            lines.append(f'{"context":<11}p90 fill {metrics["longctx_p90_fill_pct"]}%')
        if 'agents_md_bytes' in metrics:
            lines.append(
                f'{"agents.md":<11}'
                f'{metrics["agents_md_bytes"]}B/{metrics["agents_md_cap_bytes"]}B cap'
            )
        if 'mcp_servers' in metrics:
            lines.append(f'{"mcp":<11}{metrics["mcp_servers"]} servers')
        if metrics.get('config_note'):
            lines.append(f'{"config":<11}{metrics["config_note"]}')
    else:
        for key, value in metrics.items():
            if value:
                lines.append(f'{key:<10} {value}')
    return lines


@dataclass(frozen=True)
class Report:
    project: Path
    days: int
    detected: list[str]
    sampled: list[str]
    metrics: dict[str, dict[str, object]]
    findings: list[Finding]
    errors: dict[str, str]


def render_text(report: Report, *, show_all: bool) -> None:
    lines: list[str] = [
        f'optimize-ai-setup evidence · window {report.days}d · project '
        f'{report.project.name}'
    ]

    detected_parts = []
    for name in report.detected:
        sessions = report.metrics.get(name, {}).get('sessions')
        detected_parts.append(
            f'{name} ({sessions} sessions)' if isinstance(sessions, int) else name
        )
    lines.append(
        'detected: ' + ' · '.join(detected_parts)
        if detected_parts
        else 'no harness detected'
    )

    if report.sampled:
        lines.append('sampled: ' + ' · '.join(report.sampled))

    for name in report.detected:
        lines.append('')
        if name in report.errors:
            lines.append(f'[{name}]')
            lines.append(f'  error: {report.errors[name]}')
            continue
        lines.extend(render_metrics_block(name, report.metrics.get(name, {})))

    lines.append('')
    findings = report.findings
    shown = findings if show_all else findings[:TOP_FINDINGS_DEFAULT]
    suffix = '' if show_all else f' (top {len(shown)} of {len(findings)}, --all for rest)'
    lines.append(f'findings{suffix}')
    for f in shown:
        lines.append(f'{f.severity.upper():<4} {f.id:<18} {f.evidence:<70} -> {f.fix}')

    print('\n'.join(lines))  # noqa: T201 -- this script's entire job is printing the report


def render_json(report: Report) -> None:
    payload = {
        'window_days': report.days,
        'project': report.project.name,
        'detected': report.detected,
        'sampled': report.sampled,
        'metrics': report.metrics,
        'findings': [asdict(f) for f in report.findings],
    }
    print(json.dumps(payload))  # noqa: T201 -- --json is the script's machine-readable mode


# --- Orchestration ---

HARNESSES: tuple[tuple[str, object, object], ...] = (
    ('claude-code', detect_claude_code, collect_claude_code),
    ('codex', detect_codex, collect_codex),
    ('cursor', detect_cursor, collect_cursor),
    ('antigravity', detect_antigravity, collect_antigravity),
    ('gemini-cli', detect_gemini, collect_gemini),
    ('claude-desktop', detect_claude_desktop, collect_claude_desktop),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Collect AI coding setup evidence.')
    parser.add_argument('--days', type=int, default=DEFAULT_DAYS)
    parser.add_argument('--project', type=str, default=str(Path.cwd()))
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--all', action='store_true')
    return parser.parse_args(argv)


def run(home: Path, project: Path, days: int) -> Report:
    detected: list[str] = []
    sampled: list[str] = []
    metrics: dict[str, dict[str, object]] = {}
    findings: list[Finding] = []
    errors: dict[str, str] = {}

    for name, detect, collect in HARNESSES:
        try:
            is_present = detect(home, project)
        except OSError:
            continue
        if not is_present:
            continue
        detected.append(name)
        try:
            harness_findings, harness_metrics, harness_sampled = collect(
                home, project, days
            )
        except Exception as exc:  # noqa: BLE001 -- one bad harness must not crash the whole report
            errors[name] = type(exc).__name__
            continue
        findings.extend(replace(f, harness=name) for f in harness_findings)
        metrics[name] = harness_metrics
        sampled.extend(harness_sampled)

    cross_findings, cross_sampled = collect_cross_tool(project)
    findings.extend(replace(f, harness='cross-tool') for f in cross_findings)
    sampled.extend(cross_sampled)

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -f.impact_tokens))
    return Report(project, days, detected, sampled, metrics, findings, errors)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    home = Path.home()
    project = Path(args.project).resolve()

    report = run(home, project, args.days)

    if args.json:
        render_json(report)
    else:
        render_text(report, show_all=args.all)
    return 0


if __name__ == '__main__':
    sys.exit(main())
