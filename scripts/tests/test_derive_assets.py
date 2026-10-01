"""Unit tests for the project-illustrator asset deriver (loaded by path)."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

Image = pytest.importorskip('PIL.Image')

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'project-illustrator'
    / 'scripts'
    / 'derive_assets.py'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location('derive_assets', MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


da = _load_module()
OPAQUE = 255


def test_crop_box_centered_keeps_aspect() -> None:
    assert da.crop_box((2160, 720), (1200, 630)) == (
        (2160 - 1371) // 2,
        0,
        (2160 - 1371) // 2 + 1371,
        720,
    )


def test_crop_box_focus_is_clamped_inside_image() -> None:
    left, top, right, bottom = da.crop_box((1000, 1000), (2, 1), focus=(0.0, 1.0))
    assert (left, right) == (0, 1000)
    assert (top, bottom) == (500, 1000)


def test_thumbnail_has_transparent_corners_and_opaque_centre() -> None:
    img = Image.new('RGBA', (1024, 1024), (200, 30, 30, 255))
    out, warning = da.derive(img, 'thumbnail')
    assert warning is None
    assert out.size == (256, 256)
    assert out.getpixel((0, 0))[3] == 0
    assert out.getpixel((128, 128))[3] == OPAQUE


def test_small_source_warns_instead_of_upscaling_silently() -> None:
    _, warning = da.derive(Image.new('RGBA', (100, 100), 'white'), 'avatar')
    assert warning is not None
    assert 'upscaled' in warning


def test_main_writes_all_targets_and_exit_code_flags_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    master = tmp_path / 'master.png'
    Image.new('RGB', (2160, 2160), 'white').save(master)
    assert da.main([str(master), str(tmp_path / 'out')]) == 0
    assert {p.stem for p in (tmp_path / 'out').glob('*.png')} == set(da.TARGETS)

    Image.new('RGB', (64, 64), 'white').save(master)
    assert da.main([str(master), str(tmp_path / 'small')]) == 1
    assert 'WARNING' in capsys.readouterr().err
