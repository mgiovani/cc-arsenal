#!/usr/bin/env python3
"""
Package a skill into a distributable .skill zip file.

Creates a zip archive suitable for sharing or publishing to skills.sh.

Includes: SKILL.md, scripts/, references/, assets/
Excludes: evals/ (root level), __pycache__, .git, *.pyc, node_modules, .DS_Store

Usage:
    python package_skill.py <skill_path> [--output <output_dir>]

Exit codes:
    0 - success
    1 - failure
"""

import sys
import zipfile
from pathlib import Path

EXPECTED_MIN_ARGS = 2

# Files and directories to exclude from the package
EXCLUDE_DIRS = {'evals', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db', '.gitignore'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd'}

# Only these top-level subdirs are packaged
INCLUDE_SUBDIRS = {'scripts', 'references', 'assets'}


def package_skill(skill_path: str | Path, output_dir: str | Path | None = None) -> Path:
    """Package a skill into a .skill zip file.

    Args:
        skill_path: Path to the skill directory
        output_dir: Where to write the .skill file (defaults to parent of skill_path)

    Returns:
        Path to the created .skill file

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist
        ValueError: If validation fails
    """
    skill_path = Path(skill_path).resolve()
    skill_md = skill_path / 'SKILL.md'

    if not skill_md.exists():
        msg = f'SKILL.md not found in {skill_path}'
        raise FileNotFoundError(msg)

    # Run validation first
    _validate_before_packaging(skill_path)

    # Determine skill name from directory
    skill_name = skill_path.name

    # Determine output location
    if output_dir is None:
        output_dir = skill_path.parent
    output_path = Path(output_dir) / f'{skill_name}.skill'

    # Create zip archive
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Always include SKILL.md
        zf.write(skill_md, f'{skill_name}/SKILL.md')

        # Include allowed subdirectories
        for subdir_name in INCLUDE_SUBDIRS:
            subdir = skill_path / subdir_name
            if subdir.exists():
                _add_directory(zf, subdir, skill_name, subdir_name)

    return output_path


def _validate_before_packaging(skill_path: Path) -> None:
    """Run quick_validate.py before packaging. Raises ValueError on failure."""
    import subprocess  # noqa: PLC0415

    validator = Path(__file__).parent / 'quick_validate.py'
    if not validator.exists():
        # Try relative to skill directory
        validator = (
            skill_path.parent.parent / 'create-skill' / 'scripts' / 'quick_validate.py'
        )

    if validator.exists():
        result = subprocess.run(
            [sys.executable, str(validator), str(skill_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            output = result.stdout + result.stderr
            msg = f'Validation failed before packaging:\n{output}'
            raise ValueError(msg)
    else:
        pass


def _add_directory(
    zf: zipfile.ZipFile,
    directory: Path,
    skill_name: str,
    relative_base: str,
) -> None:
    """Recursively add a directory to the zip, respecting exclusions."""
    for item in sorted(directory.rglob('*')):
        # Check exclusions
        if _should_exclude(item):
            continue

        if item.is_file():
            arcname = f'{skill_name}/{relative_base}/{item.relative_to(directory)}'
            zf.write(item, arcname)


def _should_exclude(path: Path) -> bool:
    """Return True if this path should be excluded from the package."""
    # Check each component of the path
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True

    if path.is_file():
        if path.name in EXCLUDE_FILES:
            return True
        if path.suffix in EXCLUDE_EXTENSIONS:
            return True

    return False


def _parse_args() -> tuple[Path, Path | None]:
    """Parse command line arguments."""
    args = sys.argv[1:]

    if len(args) < 1:
        sys.exit(1)

    skill_path = Path(args[0])
    output_dir = None

    if '--output' in args:
        idx = args.index('--output')
        if idx + 1 < len(args):
            output_dir = Path(args[idx + 1])
        else:
            sys.exit(1)

    return skill_path, output_dir


if __name__ == '__main__':
    skill_path, output_dir = _parse_args()

    try:
        output_path = package_skill(skill_path, output_dir)
    except (FileNotFoundError, ValueError):
        sys.exit(1)
