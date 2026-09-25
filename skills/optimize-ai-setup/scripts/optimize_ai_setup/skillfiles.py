"""Reading SKILL.md files: shared by the Claude Code and Codex skill checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE, MAX_SKILL_FILES
from optimize_ai_setup.io import read_text_capped


@dataclass(frozen=True)
class SkillFile:
    name: str
    source: str
    description_len: int
    text: str
    path: Path = Path()


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
