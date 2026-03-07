#!/usr/bin/env python3
"""
Quick validation script for agent skills.

Validates a skill directory against the Agent Skills specification:
- YAML frontmatter structure and required fields
- Allowed frontmatter keys (rejects unknown keys)
- Name format: kebab-case, ≤64 chars, no invalid hyphens
- Description: 50-1024 chars, no angle brackets
- SKILL.md line count warning (>500 lines)
- Directory structure (only scripts/, references/, assets/ subdirs)
- Internal reference integrity (referenced files exist)
- evals/evals.json schema (if present)

Usage:
    uv run python skills/create-skill/scripts/quick_validate.py <skill_path>

Exit codes:
    0 - valid
    1 - invalid (errors found)
"""

import json
import re
import sys
from pathlib import Path

EXPECTED_ARGS = 2

# Keys allowed in SKILL.md frontmatter per the Agent Skills specification
ALLOWED_FRONTMATTER_KEYS = {
    'name',
    'description',
    'license',
    'allowed-tools',
    'metadata',
    'compatibility',
    'disable-model-invocation',
    'argument-hint',
}

# Allowed subdirectories in a skill directory
ALLOWED_SUBDIRS = {'scripts', 'references', 'assets', 'evals'}

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MIN_DESCRIPTION_LENGTH = 50
WARN_LINE_COUNT = 500


def validate_skill(skill_path: str | Path) -> tuple[bool, list[str], list[str]]:
    """Validate a skill directory.

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    skill_path = Path(skill_path)
    errors: list[str] = []
    warnings: list[str] = []

    # Validate SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, ['SKILL.md not found'], []

    # Read and parse content
    content = skill_md.read_text(encoding='utf-8')

    # Extract frontmatter
    frontmatter_str, parse_error = _extract_frontmatter(content)
    if parse_error:
        return False, [parse_error], []

    # Parse YAML (handling multiline indicators)
    frontmatter, yaml_error = _parse_yaml_frontmatter(frontmatter_str)
    if yaml_error:
        return False, [yaml_error], []

    # Validate frontmatter
    fm_errors = _validate_frontmatter(frontmatter)
    errors.extend(fm_errors)

    # Line count warning
    line_count = content.count('\n')
    if line_count > WARN_LINE_COUNT:
        warnings.append(
            f'SKILL.md has {line_count} lines (>{WARN_LINE_COUNT}). '
            'Consider moving detailed content to references/'
        )

    # Directory structure
    dir_errors = _validate_directory_structure(skill_path)
    errors.extend(dir_errors)

    # Internal reference integrity
    ref_errors = _validate_internal_references(skill_path, content)
    errors.extend(ref_errors)

    # evals/evals.json schema (if present)
    evals_file = skill_path / 'evals' / 'evals.json'
    if evals_file.exists():
        evals_errors = _validate_evals_schema(evals_file)
        errors.extend(evals_errors)

    return len(errors) == 0, errors, warnings


def _extract_frontmatter(content: str) -> tuple[str, str | None]:
    """Extract YAML frontmatter from content.

    Returns:
        Tuple of (frontmatter_string, error_message_or_None)
    """
    if not content.startswith('---'):
        return '', 'No YAML frontmatter found (file must start with ---)'

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return '', 'Invalid frontmatter format (missing closing ---)'

    return match.group(1), None


def _parse_yaml_frontmatter(frontmatter_str: str) -> tuple[dict, str | None]:
    """Parse YAML frontmatter, handling multiline indicators.

    Returns:
        Tuple of (parsed_dict, error_message_or_None)
    """
    try:
        import yaml  # noqa: PLC0415

        result = yaml.safe_load(frontmatter_str)
        if result is None:
            return {}, None
        if not isinstance(result, dict):
            return {}, 'Frontmatter must be a YAML mapping'
        return result, None
    except ImportError:
        # Fallback: simple regex parsing without yaml module
        return _parse_yaml_simple(frontmatter_str), None
    except Exception as e:  # noqa: BLE001
        return {}, f'YAML parse error: {e}'


def _parse_yaml_simple(frontmatter_str: str) -> dict:
    """Simple YAML key extraction fallback (no yaml module required).

    Handles basic key: value and multiline block scalars (|, >, |-, >-).
    """
    result: dict = {}
    lines = frontmatter_str.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match top-level keys (no leading spaces)
        match = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Handle multiline block scalars
            if value in ('|', '>', '|-', '>-', '|+', '>+'):
                block_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith('  ') or lines[i] == ''):
                    block_lines.append(lines[i])
                    i += 1
                result[key] = '\n'.join(block_lines).strip()
                continue
            result[key] = value
        i += 1
    return result


def _validate_frontmatter(frontmatter: dict) -> list[str]:
    """Validate all frontmatter fields. Returns list of error messages."""
    errors: list[str] = []

    # Required fields
    if 'name' not in frontmatter:
        errors.append("Missing required field: 'name'")
    if 'description' not in frontmatter:
        errors.append("Missing required field: 'description'")

    # Unknown keys
    unknown_keys = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_KEYS
    if unknown_keys:
        errors.append(
            f'Unknown frontmatter key(s): {", ".join(sorted(unknown_keys))}. '
            f'Allowed: {", ".join(sorted(ALLOWED_FRONTMATTER_KEYS))}'
        )

    # Validate name
    if 'name' in frontmatter:
        name_errors = _validate_name(str(frontmatter['name']))
        errors.extend(name_errors)

    # Validate description
    if 'description' in frontmatter:
        desc_errors = _validate_description(str(frontmatter['description']).strip('"\''))
        errors.extend(desc_errors)

    return errors


def _validate_name(name: str) -> list[str]:
    """Validate skill name format."""
    errors: list[str] = []
    name = name.strip()

    if len(name) > MAX_NAME_LENGTH:
        errors.append(f"Name '{name}' exceeds {MAX_NAME_LENGTH} characters ({len(name)})")

    if not re.match(r'^[a-z0-9-]+$', name):
        errors.append(
            f"Name '{name}' must be kebab-case (lowercase letters, digits, hyphens only)"
        )

    if name.startswith('-') or name.endswith('-'):
        errors.append(f"Name '{name}' cannot start or end with a hyphen")

    if '--' in name:
        errors.append(f"Name '{name}' cannot contain consecutive hyphens")

    return errors


def _validate_description(description: str) -> list[str]:
    """Validate description format."""
    errors: list[str] = []

    if len(description) < MIN_DESCRIPTION_LENGTH:
        errors.append(
            f'Description is too short ({len(description)} chars, minimum {MIN_DESCRIPTION_LENGTH})'
        )

    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f'Description exceeds {MAX_DESCRIPTION_LENGTH} characters ({len(description)})'
        )

    if '<' in description or '>' in description:
        errors.append('Description cannot contain angle brackets (< or >)')

    return errors


def _validate_directory_structure(skill_path: Path) -> list[str]:
    """Validate that only allowed subdirectories exist."""
    errors: list[str] = []

    for item in skill_path.iterdir():
        if (
            item.is_dir()
            and not item.name.startswith('.')
            and item.name not in ALLOWED_SUBDIRS
        ):
            errors.append(
                f"Unknown subdirectory: '{item.name}'. "
                f'Allowed: {", ".join(sorted(ALLOWED_SUBDIRS))}'
            )

    return errors


def _validate_internal_references(skill_path: Path, content: str) -> list[str]:
    """Check that files referenced in SKILL.md actually exist."""
    errors: list[str] = []

    # Find references to bundled files (e.g., references/foo.md, scripts/bar.py)
    ref_pattern = re.compile(r'(?:references|scripts|assets)/[\w\-./]+')
    referenced = ref_pattern.findall(content)

    for ref in referenced:
        ref_path = skill_path / ref.strip('`')
        if not ref_path.exists() and not ref_path.is_dir():
            base_dir = skill_path / ref.split('/')[0]
            if base_dir.exists():
                errors.append(f'Referenced file not found: {ref}')

    return errors


def _validate_evals_schema(evals_file: Path) -> list[str]:
    """Validate evals/evals.json structure."""
    errors: list[str] = []

    try:
        data = json.loads(evals_file.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [f'evals/evals.json is invalid JSON: {e}']

    if not isinstance(data, dict):
        return ['evals/evals.json must be a JSON object']

    if 'skill' not in data:
        errors.append("evals/evals.json missing required field: 'skill'")

    if 'evals' not in data:
        errors.append("evals/evals.json missing required field: 'evals'")
    elif not isinstance(data['evals'], list):
        errors.append("evals/evals.json: 'evals' must be an array")
    else:
        for i, eval_case in enumerate(data['evals']):
            if not isinstance(eval_case, dict):
                errors.append(f'evals/evals.json: eval[{i}] must be an object')
                continue
            if 'id' not in eval_case:
                errors.append(f"evals/evals.json: eval[{i}] missing required field 'id'")
            if 'prompt' not in eval_case:
                errors.append(
                    f"evals/evals.json: eval[{i}] missing required field 'prompt'"
                )
            if 'assertions' not in eval_case:
                errors.append(
                    f"evals/evals.json: eval[{i}] missing required field 'assertions'"
                )
            elif not isinstance(eval_case['assertions'], list):
                errors.append(f'evals/evals.json: eval[{i}].assertions must be an array')

    return errors


if __name__ == '__main__':
    if len(sys.argv) != EXPECTED_ARGS:
        sys.stderr.write(f'Usage: {sys.argv[0]} <skill_path>\n')
        sys.exit(1)

    valid, errors, warnings = validate_skill(sys.argv[1])

    for warning in warnings:
        sys.stderr.write(f'WARNING: {warning}\n')

    if valid:
        sys.stdout.write('OK: Skill is valid\n')
        if warnings:
            sys.stdout.write(f'({len(warnings)} warning(s))\n')
        sys.exit(0)
    else:
        for error in errors:
            sys.stderr.write(f'ERROR: {error}\n')
        sys.stderr.write(
            f'\nValidation failed: {len(errors)} error(s), {len(warnings)} warning(s)\n'
        )
        sys.exit(1)
