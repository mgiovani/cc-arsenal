"""Unit tests for the i18n-check diff script, loaded by path via importlib."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'i18n-check'
    / 'scripts'
    / 'i18n_diff.py'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location('i18n_diff', MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


i18n_diff = _load_module()


def test_flatten_nested_and_lists() -> None:
    assert i18n_diff.flatten({'a': {'b': 'x'}, 'c': ['y']}) == {'a.b': 'x', 'c.0': 'y'}


def test_diff_buckets() -> None:
    base = {'a': 'Developer', 'b': '42', 'c': 'Hello', 'd': '{name}'}
    other = {'a': 'Developer', 'b': '42', 'c': 'Ola', 'd': '{name}', 'z': 'old'}
    result = i18n_diff.diff(base, other)
    assert result['untranslated'] == ['a']
    assert result['invariant'] == ['b', 'd']
    assert result['orphan'] == ['z']
    assert result['missing'] == []


def test_exit_code_on_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    en = tmp_path / 'en.json'
    pt = tmp_path / 'pt.json'
    en.write_text(json.dumps({'a': {'b': 'Hi'}, 'c': 'Yo'}))
    pt.write_text(json.dumps({'a': {'b': 'Oi'}}))
    assert i18n_diff.main([str(en), str(pt)]) == 1
    assert '- c' in capsys.readouterr().out


def test_clean_exit_and_yaml_unwrap(tmp_path: Path) -> None:
    en = tmp_path / 'en.yml'
    pt = tmp_path / 'pt.yml'
    en.write_text('en:\n  a: Hi\n')
    pt.write_text('pt:\n  a: Oi\n  extra: x\n')
    assert i18n_diff.main([str(en), str(pt)]) == 0


def test_unreadable_locale_fails(tmp_path: Path) -> None:
    en = tmp_path / 'en.json'
    en.write_text('{}')
    assert i18n_diff.main([str(en), str(tmp_path / 'nope.json')]) == 1
