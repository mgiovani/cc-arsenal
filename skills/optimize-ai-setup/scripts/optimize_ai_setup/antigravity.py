"""Antigravity: global + workspace rule files, plus its MCP server count."""

from __future__ import annotations

from typing import TYPE_CHECKING

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE, MEMORY_TOTAL_TOKENS_MED
from optimize_ai_setup.io import (
    chars_to_tokens,
    fmt_num,
    mcp_server_names,
    read_json,
    read_text_capped,
)
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path


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
