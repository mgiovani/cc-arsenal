"""Claude Code transcript parsing: turns raw session .jsonl lines into the
per-session usage/attachment/tool-use data every claude-code check reads."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from optimize_ai_setup.constants import MAX_SKILL_FILES
from optimize_ai_setup.io import (
    WindowedFiles,
    get_dict,
    iter_filtered_lines,
    select_in_window,
)

if TYPE_CHECKING:
    from pathlib import Path

TRANSCRIPT_NEEDLES = ('"usage"', '"attachment"', '"tool_use"', '<command-name>')
SLASH_RE = re.compile(r'<command-name>([^<]+)</command-name>')
MCP_TOOL_NAME_PARTS = 2


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
    message = get_dict(obj, 'message')
    usage = message.get('usage')
    if not usage or not isinstance(usage, dict):
        return
    request_id = obj.get('requestId') or message.get('id')
    if not request_id or request_id in seen:
        return
    seen.add(request_id)
    cache_creation = get_dict(usage, 'cache_creation')
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
    attachment = get_dict(obj, 'attachment')
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
    content = get_dict(obj, 'message').get('content')
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get('type') != 'tool_use':
            continue
        name = block.get('name') or ''
        if name == 'Skill':
            skill = get_dict(block, 'input').get('skill')
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
                message = get_dict(obj, 'message')
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
    windowed: WindowedFiles = select_in_window(projects_dir.glob('*/*.jsonl'), days)
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
