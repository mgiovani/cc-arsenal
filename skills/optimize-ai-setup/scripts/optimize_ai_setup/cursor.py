"""Cursor: config- and rules-based checks (no readable per-session token log)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE, MEMORY_TOTAL_TOKENS_MED
from optimize_ai_setup.io import (
    chars_to_tokens,
    fmt_num,
    mcp_server_names,
    read_json,
    read_text_capped,
)
from optimize_ai_setup.model import Finding, make_finding


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
