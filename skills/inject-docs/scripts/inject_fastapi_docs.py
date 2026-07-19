#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
FastAPI documentation injector for CLAUDE.md files.

This script injects best practices from zhanymkanov/fastapi-best-practices
into the project's CLAUDE.md or AGENTS.md file.
"""

import re
import sys
from pathlib import Path


def detect_target_file(project_root: Path) -> Path:
    """
    Detect the target file for documentation injection.

    Priority: CLAUDE.md > AGENTS.md > CLAUDE.md (create new)
    """
    claude_md = project_root / 'CLAUDE.md'
    agents_md = project_root / 'AGENTS.md'

    if claude_md.exists():
        return claude_md
    if agents_md.exists():
        return agents_md
    return claude_md  # Will be created


def read_fastapi_best_practices() -> str:
    """
    Read the FastAPI best practices reference content.

    Assumes this script is in skills/inject-docs/scripts/ and the reference
    is at skills/inject-docs/references/fastapi-best-practices.md
    """
    script_dir = Path(__file__).parent
    reference_path = script_dir.parent / 'references' / 'fastapi-best-practices.md'

    if not reference_path.exists():
        raise FileNotFoundError(
            f'FastAPI best practices reference not found at {reference_path}'
        )

    content = reference_path.read_text(encoding='utf-8')

    # Extract only the template section (after "## Full Content Template")
    match = re.search(r'## Full Content Template\n\n---\n\n(.*)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: return everything after the header
    return content.split('---\n\n', 1)[1] if '---\n\n' in content else content


def inject_or_update_section(
    existing_content: str,
    new_section: str,
    section_header: str = '## FastAPI Best Practices',
) -> tuple[str, bool]:
    """
    Inject or update the FastAPI best practices section in the content.

    Returns:
        tuple[str, bool]: (updated_content, was_updated)
    """
    # Check if section already exists
    section_pattern = re.compile(
        rf'^{re.escape(section_header)}$.*?(?=^## |\Z)', re.MULTILINE | re.DOTALL
    )

    if section_pattern.search(existing_content):
        # Update existing section
        updated_content = section_pattern.sub(new_section, existing_content)
        return updated_content, True
    # Append new section
    if existing_content and not existing_content.endswith('\n\n'):
        separator = '\n\n'
    else:
        separator = ''

    updated_content = existing_content + separator + new_section
    return updated_content, False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    kb = 1024
    mb = kb * 1024

    if size_bytes < kb:
        return f'{size_bytes} B'
    if size_bytes < mb:
        return f'{size_bytes / kb:.1f} KB'
    return f'{size_bytes / mb:.1f} MB'


def main() -> int:
    """Main execution function."""
    # Detect project root (current working directory)
    project_root = Path.cwd()

    # Detect target file
    target_file = detect_target_file(project_root)
    file_existed = target_file.exists()

    # Read existing content or start with empty
    existing_content = target_file.read_text(encoding='utf-8') if file_existed else ''

    # Read FastAPI best practices content
    try:
        fastapi_section = read_fastapi_best_practices()
    except FileNotFoundError:
        return 1

    # Inject or update section
    updated_content, was_updated = inject_or_update_section(
        existing_content, fastapi_section
    )

    # Write updated content
    target_file.write_text(updated_content, encoding='utf-8')
    new_size = len(updated_content.encode('utf-8'))

    # Report results
    action = 'Created' if not file_existed else 'Updated'
    section_note = 'updated existing section' if was_updated else 'appended new section'
    print(  # noqa: T201 -- CLI script, stdlib-only by design
        f'{action} {target_file.name} ({format_file_size(new_size)}) - {section_note}'
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
