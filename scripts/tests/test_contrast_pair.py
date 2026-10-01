"""Tests for the ad-hoc ``--pair`` mode of the design-tokens contrast script."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'product-design-tokens'
    / 'scripts'
    / 'contrast.py'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location('contrast', MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contrast = _load_module()


def test_black_on_white_passes_everything() -> None:
    line, ok = contrast.pair_report('#000000', '#ffffff')
    assert ok
    assert '21.00:1' in line
    assert 'AA PASS' in line
    assert 'AAA PASS' in line


def test_grey_fails_normal_but_not_large() -> None:
    _, normal_ok = contrast.pair_report('#999999', '#ffffff')
    large_line, large_ok = contrast.pair_report('#777777', '#ffffff', large=True)
    assert not normal_ok
    assert large_ok
    assert 'AA PASS' in large_line
    assert 'AAA PASS' not in large_line


def test_aa_boundary_grey() -> None:
    line, ok = contrast.pair_report('#767676', '#ffffff')
    assert ok
    assert 'AAA FAIL' in line


def test_main_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr('sys.argv', ['contrast.py', '--pair', '#999', '#fff'])
    assert contrast.main() == 1
    assert 'AA FAIL' in capsys.readouterr().out
    monkeypatch.setattr('sys.argv', ['contrast.py', '--pair', '#000', '#fff'])
    assert contrast.main() == 0
