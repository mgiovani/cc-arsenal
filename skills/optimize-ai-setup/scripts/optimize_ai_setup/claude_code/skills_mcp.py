"""CC-SKILL-LISTING/DUP/UNUSED, CC-PLUGIN-UNUSED, CC-MCP-UNUSED: what's listed
at startup versus what a session's transcripts show actually got used."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from optimize_ai_setup.constants import UNUSED_MIN_SESSIONS
from optimize_ai_setup.io import (
    chars_to_tokens,
    fmt_num,
    get_dict,
    mcp_server_names,
    read_json,
    read_json_checked,
)
from optimize_ai_setup.model import Finding, make_finding
from optimize_ai_setup.skillfiles import scan_skill_dir

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from optimize_ai_setup.claude_code.transcript import SessionData

SKILL_LISTING_TOKEN_LIMIT = 8_000
SKILL_DESC_CHAR_LIMIT = 1_536


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
    project_entry = get_dict(get_dict(claude_json, 'projects'), str(project))
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
