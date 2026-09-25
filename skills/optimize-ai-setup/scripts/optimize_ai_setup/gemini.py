"""Gemini CLI: settings.json MCP servers plus the GEMINI.md context chain."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE, MEMORY_TOTAL_TOKENS_MED
from optimize_ai_setup.io import (
    chars_to_tokens,
    fmt_num,
    get_dict,
    mcp_server_names,
    read_json,
    read_text_capped,
)
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path


def detect_gemini(_home: Path, _project: Path) -> bool:
    # ~/.gemini (settings.json, tmp/*/chats) is shared with Antigravity, so only
    # the CLI binary proves Gemini CLI is installed.
    return shutil.which('gemini') is not None


def collect_gemini(
    home: Path, project: Path, _days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    settings = read_json(home / '.gemini' / 'settings.json')
    server_count = len(mcp_server_names(settings))
    file_name = get_dict(settings, 'context').get('fileName') or 'GEMINI.md'
    if isinstance(file_name, list):
        file_name = file_name[0] if file_name else 'GEMINI.md'
    if not isinstance(file_name, str):
        file_name = 'GEMINI.md'

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
