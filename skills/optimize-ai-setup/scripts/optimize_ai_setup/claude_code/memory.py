"""CC-MEMORY: the CLAUDE.md/.claude/rules chain Claude Code always loads,
walked the same way the harness itself resolves it (including @-imports)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from optimize_ai_setup.constants import (
    MAX_BYTES_PER_FILE,
    MEMORY_TOTAL_TOKENS_HIGH,
    MEMORY_TOTAL_TOKENS_MED,
)
from optimize_ai_setup.io import chars_to_tokens, compact_path, fmt_num, read_text_capped
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path

MEMORY_FILE_LINE_LIMIT = 200

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
