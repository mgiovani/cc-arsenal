"""Tests for the FastAPI documentation injection script."""

import re
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fastapi_reference_content() -> str:
    """Load the FastAPI best practices reference content."""
    script_dir = Path(__file__).parent.parent
    reference_path = script_dir / 'references' / 'fastapi-best-practices.md'

    if not reference_path.exists():
        pytest.skip('FastAPI reference file not found')

    content = reference_path.read_text(encoding='utf-8')

    # Extract template section
    match = re.search(r'## Full Content Template\n\n---\n\n(.*)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    return content.split('---\n\n', 1)[1] if '---\n\n' in content else content


def test_inject_to_new_claude_md(
    temp_project_dir: Path,
    fastapi_reference_content: str,
    monkeypatch: Any,  # noqa: ANN401
) -> None:
    """Test injecting FastAPI docs into a new CLAUDE.md file."""
    # Change to temp directory
    monkeypatch.chdir(temp_project_dir)

    # Import the script functions
    from skills.inject_docs.scripts.inject_fastapi_docs import (
        detect_target_file,
        inject_or_update_section,
    )

    # Test target file detection (should default to CLAUDE.md)
    target_file = detect_target_file(temp_project_dir)
    assert target_file.name == 'CLAUDE.md'
    assert not target_file.exists()

    # Test injection into empty content
    updated_content, was_updated = inject_or_update_section(
        '', fastapi_reference_content
    )
    assert not was_updated  # First time is append, not update
    assert '## FastAPI Best Practices' in updated_content
    assert (
        'Domain-Driven Project Organization' in updated_content
        or 'Project Structure' in updated_content
    )

    # Write to file
    target_file.write_text(updated_content, encoding='utf-8')
    assert target_file.exists()
    assert target_file.stat().st_size > 1000  # Should be several KB


def test_update_existing_section(
    temp_project_dir: Path,
    fastapi_reference_content: str,
    monkeypatch: Any,  # noqa: ANN401
) -> None:
    """Test updating an existing FastAPI section in CLAUDE.md."""
    monkeypatch.chdir(temp_project_dir)

    from skills.inject_docs.scripts.inject_fastapi_docs import (
        inject_or_update_section,
    )

    # Create existing content with old FastAPI section
    existing_content = """# My Project

## Other Documentation

Some content here.

## FastAPI Best Practices

Old content that should be replaced.

## More Sections

Other content.
"""

    # Update the section
    updated_content, was_updated = inject_or_update_section(
        existing_content, fastapi_reference_content
    )

    assert was_updated  # This time it's an update
    assert '## FastAPI Best Practices' in updated_content
    assert 'Old content that should be replaced' not in updated_content
    assert '## Other Documentation' in updated_content  # Preserved
    assert '## More Sections' in updated_content  # Preserved


def test_prefer_claude_md_over_agents_md(
    temp_project_dir: Path, monkeypatch: Any  # noqa: ANN401
) -> None:
    """Test that CLAUDE.md is preferred over AGENTS.md."""
    monkeypatch.chdir(temp_project_dir)

    from skills.inject_docs.scripts.inject_fastapi_docs import detect_target_file

    # Create both files
    (temp_project_dir / 'CLAUDE.md').write_text('# Claude\n')
    (temp_project_dir / 'AGENTS.md').write_text('# Agents\n')

    target_file = detect_target_file(temp_project_dir)
    assert target_file.name == 'CLAUDE.md'


def test_use_agents_md_when_only_option(
    temp_project_dir: Path, monkeypatch: Any  # noqa: ANN401
) -> None:
    """Test that AGENTS.md is used when CLAUDE.md doesn't exist."""
    monkeypatch.chdir(temp_project_dir)

    from skills.inject_docs.scripts.inject_fastapi_docs import detect_target_file

    # Create only AGENTS.md
    (temp_project_dir / 'AGENTS.md').write_text('# Agents\n')

    target_file = detect_target_file(temp_project_dir)
    assert target_file.name == 'AGENTS.md'


def test_file_size_formatting() -> None:
    """Test the file size formatting function."""
    from skills.inject_docs.scripts.inject_fastapi_docs import format_file_size

    assert format_file_size(500) == '500 B'
    assert format_file_size(1024) == '1.0 KB'
    assert format_file_size(2048) == '2.0 KB'
    assert format_file_size(1024 * 1024) == '1.0 MB'
    assert format_file_size(1536 * 1024) == '1.5 MB'
