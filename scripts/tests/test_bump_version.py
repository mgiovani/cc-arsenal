"""Unit tests for the version bump script."""

import json
from pathlib import Path

import pytest

from scripts import bump_version


def _write_config(tmp_path: Path, targets: list[dict]) -> Path:
    config_path = tmp_path / '.version-bump.json'
    config_path.write_text(json.dumps({'targets': targets}))
    return config_path


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, targets: list[dict]) -> Path:
    config_path = _write_config(tmp_path, targets)
    monkeypatch.setattr(bump_version, 'ROOT', tmp_path)
    monkeypatch.setattr(bump_version, 'CONFIG_PATH', config_path)
    return config_path


def test_bump_updates_all_version_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marketplace = tmp_path / 'marketplace.json'
    marketplace.write_text(
        json.dumps({'metadata': {'version': '1.0.0'}, 'plugins': [{'version': '1.0.0'}]})
    )
    plugin = tmp_path / 'plugin.json'
    plugin.write_text(json.dumps({'version': '1.0.0'}))

    _setup(tmp_path, monkeypatch, [{'file': 'marketplace.json'}, {'file': 'plugin.json'}])
    monkeypatch.setattr('sys.argv', ['bump_version.py', '2.0.0'])

    bump_version.main()

    expected_count = 2
    assert '"version": "2.0.0"' in marketplace.read_text()
    assert marketplace.read_text().count('"version": "2.0.0"') == expected_count
    assert '"version": "2.0.0"' in plugin.read_text()


def test_rerun_with_same_version_is_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin = tmp_path / 'plugin.json'
    plugin.write_text(json.dumps({'version': '1.0.0'}))
    _setup(tmp_path, monkeypatch, [{'file': 'plugin.json'}])
    monkeypatch.setattr('sys.argv', ['bump_version.py', '1.0.0'])

    before = plugin.read_text()
    bump_version.main()
    after = plugin.read_text()

    assert before == after


def test_target_missing_version_field_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    no_version = tmp_path / 'no_version.json'
    no_version.write_text(json.dumps({'name': 'no version here'}))
    _setup(tmp_path, monkeypatch, [{'file': 'no_version.json'}])
    monkeypatch.setattr('sys.argv', ['bump_version.py', '2.0.0'])

    with pytest.raises(SystemExit):
        bump_version.main()


def test_missing_config_exits_with_clear_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bump_version, 'ROOT', tmp_path)
    monkeypatch.setattr(bump_version, 'CONFIG_PATH', tmp_path / '.version-bump.json')
    monkeypatch.setattr('sys.argv', ['bump_version.py', '2.0.0'])

    with pytest.raises(SystemExit, match='config not found'):
        bump_version.main()


def test_missing_targets_key_reports_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / '.version-bump.json'
    config_path.write_text(json.dumps({'not_targets': []}))
    monkeypatch.setattr(bump_version, 'ROOT', tmp_path)
    monkeypatch.setattr(bump_version, 'CONFIG_PATH', config_path)
    monkeypatch.setattr('sys.argv', ['bump_version.py', '2.0.0'])

    with pytest.raises(SystemExit, match='missing "targets" key'):
        bump_version.main()


def test_target_missing_file_key_reports_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A present 'targets' list whose entry lacks 'file' must not be misreported
    # as a missing 'targets' key.
    _setup(tmp_path, monkeypatch, [{'not_file': 'x'}])
    monkeypatch.setattr('sys.argv', ['bump_version.py', '2.0.0'])

    with pytest.raises(SystemExit, match="target entry missing its 'file' key"):
        bump_version.main()
