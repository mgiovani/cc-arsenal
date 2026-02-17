#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import re
import sys
from pathlib import Path

EXPECTED_ARGS = 2


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Validate SKILL.md and extract frontmatter
    error = _validate_file_structure(skill_path)
    if error:
        return False, error

    # Extract and validate frontmatter content
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text()
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    frontmatter = match.group(1)  # Safe because _validate_file_structure checked this

    # Run all field validations
    error = _validate_frontmatter_fields(frontmatter)
    if error:
        return False, error

    return True, 'Skill is valid!'


def _validate_file_structure(skill_path: Path) -> str | None:
    """Validate SKILL.md exists and has valid frontmatter structure."""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return 'SKILL.md not found'

    content = skill_md.read_text()
    if not content.startswith('---'):
        return 'No YAML frontmatter found'

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return 'Invalid frontmatter format'

    return None


def _validate_frontmatter_fields(frontmatter: str) -> str | None:
    """Validate all required frontmatter fields."""
    # Check required fields exist
    if 'name:' not in frontmatter:
        return "Missing 'name' in frontmatter"
    if 'description:' not in frontmatter:
        return "Missing 'description' in frontmatter"

    # Validate name format
    error = _validate_name(frontmatter)
    if error:
        return error

    # Validate description format
    return _validate_description(frontmatter)


def _validate_name(frontmatter: str) -> str | None:
    """Validate skill name format. Returns error message or None."""
    name_match = re.search(r'name:\s*(.+)', frontmatter)
    if not name_match:
        return None

    name = name_match.group(1).strip()

    # Check naming convention (hyphen-case: lowercase with hyphens)
    if not re.match(r'^[a-z0-9-]+$', name):
        return (
            f"Name '{name}' should be hyphen-case "
            '(lowercase letters, digits, and hyphens only)'
        )

    # Check for invalid hyphen positions
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return (
            f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        )

    return None


def _validate_description(frontmatter: str) -> str | None:
    """Validate description format. Returns error message or None."""
    desc_match = re.search(r'description:\s*(.+)', frontmatter)
    if not desc_match:
        return None

    description = desc_match.group(1).strip()
    if '<' in description or '>' in description:
        return 'Description cannot contain angle brackets (< or >)'

    return None


if __name__ == '__main__':
    if len(sys.argv) != EXPECTED_ARGS:
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    sys.exit(0 if valid else 1)
