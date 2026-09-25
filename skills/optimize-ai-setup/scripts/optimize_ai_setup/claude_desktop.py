"""Claude Desktop: MCP servers configured versus what their own logs show
was actually called (Desktop keeps no per-session token data)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from optimize_ai_setup.io import mcp_server_names, read_json
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path

MAX_LOG_TAIL_BYTES = 2 * 1024 * 1024


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
