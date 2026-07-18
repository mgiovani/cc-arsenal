"""Unit tests for the FastAPI docs injector.

The script lives in ``skills/inject-docs/scripts/`` — a hyphenated package dir
that can't be imported normally — so it is loaded by path via importlib.
"""

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'inject-docs'
    / 'scripts'
    / 'inject_fastapi_docs.py'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location('inject_fastapi_docs', MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inject = _load_module()


def test_format_file_size_units() -> None:
    assert inject.format_file_size(512) == '512 B'
    assert inject.format_file_size(1024) == '1.0 KB'
    assert inject.format_file_size(1024 * 1024) == '1.0 MB'


def test_detect_target_file_prefers_claude_then_agents(tmp_path: Path) -> None:
    # No files yet -> CLAUDE.md (to be created).
    assert inject.detect_target_file(tmp_path) == tmp_path / 'CLAUDE.md'

    (tmp_path / 'AGENTS.md').write_text('# agents')
    assert inject.detect_target_file(tmp_path) == tmp_path / 'AGENTS.md'

    (tmp_path / 'CLAUDE.md').write_text('# claude')
    assert inject.detect_target_file(tmp_path) == tmp_path / 'CLAUDE.md'


def test_inject_appends_when_section_absent() -> None:
    existing = '# Project\n'
    new_section = '## FastAPI Best Practices\n\nbody\n'
    updated, was_updated = inject.inject_or_update_section(existing, new_section)

    assert was_updated is False
    assert updated.startswith('# Project')
    assert '## FastAPI Best Practices' in updated
    assert 'body' in updated


def test_inject_updates_existing_section_in_place() -> None:
    existing = (
        '# Title\n\n'
        '## FastAPI Best Practices\n\nold body\n\n'
        '## Other\n\nkeep me\n'
    )
    new_section = '## FastAPI Best Practices\n\nnew body\n'
    updated, was_updated = inject.inject_or_update_section(existing, new_section)

    assert was_updated is True
    assert 'new body' in updated
    assert 'old body' not in updated
    # A following section must survive untouched.
    assert '## Other' in updated
    assert 'keep me' in updated


def test_main_writes_section_and_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert inject.main() == 0

    target = tmp_path / 'CLAUDE.md'
    assert target.exists()
    assert '## FastAPI Best Practices' in target.read_text(encoding='utf-8')

    out = capsys.readouterr().out.strip()
    assert re.match(
        r'^(Created|Updated) CLAUDE\.md \([\d.]+ [KMG]?B\) - '
        r'(appended new|updated existing) section$',
        out,
    ), out
