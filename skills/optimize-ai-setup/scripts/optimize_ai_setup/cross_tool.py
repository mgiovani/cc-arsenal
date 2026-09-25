"""Checks that span more than one harness: duplicated memory instructions and
a literal secret sitting in a committed MCP config."""

from __future__ import annotations

from typing import TYPE_CHECKING

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE
from optimize_ai_setup.io import (
    get_dict,
    looks_like_placeholder,
    read_json,
    read_text_capped,
)
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path

DUP_INSTR_OVERLAP = 0.6
MIN_MEMORY_FILES_TO_COMPARE = 2


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
        line_sets = {
            name: {line.strip() for line in text.splitlines() if line.strip()}
            for name, text in texts.items()
        }
        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                lines_a = line_sets[name_a]
                lines_b = line_sets[name_b]
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
        for server_name, server_cfg in get_dict(config, 'mcpServers').items():
            if not isinstance(server_cfg, dict):
                continue
            values = list(get_dict(server_cfg, 'env').values()) + list(
                get_dict(server_cfg, 'headers').values()
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
