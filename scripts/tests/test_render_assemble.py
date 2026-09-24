"""Unit tests for the render skill's assembler/gate.

The script lives in ``skills/render/scripts/`` -- a hyphenated package dir
that can't be imported normally -- so it is loaded by path via importlib.
"""

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / 'skills' / 'render' / 'scripts' / 'assemble.py'
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location('assemble', MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assemble = _load_module()

CLEAN_PAGE = """<!doctype html>
<html>
<head>
<style>
  :root { --bg: #fafafa; --ink: #0f0f0f; --hair: 1px; }
  body { background: var(--bg); color: var(--ink); border-radius: 0; }
  .btn { box-shadow: inset 0 0 0 var(--hair) var(--ink); }
  .mix { background: color-mix(in srgb, var(--ink) 20%, var(--bg)); }
</style>
</head>
<body>
  <p>issue #123 tracked here</p>
</body>
</html>
"""


def _wrap_style(css: str) -> str:
    return f'<html><head><style>{css}</style></head><body></body></html>'


def test_inline_assets_inlines_local_css_and_js(tmp_path: Path) -> None:
    (tmp_path / 'page.css').write_text('body { color: var(--ink); }')
    (tmp_path / 'page.js').write_text('const x = 1;')
    html = (
        '<link rel="stylesheet" href="page.css">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2">'
        '<script src="page.js"></script>'
    )

    out = assemble.inline_assets(html, tmp_path)

    assert '<style>body { color: var(--ink); }</style>' in out
    assert '<script>const x = 1;</script>' in out
    assert 'href="page.css"' not in out
    assert 'src="page.js"' not in out
    assert 'href="https://fonts.googleapis.com/css2"' in out


def test_inline_assets_missing_file_raises_clearly(tmp_path: Path) -> None:
    html = '<link rel="stylesheet" href="missing.css">'
    with pytest.raises(FileNotFoundError, match='missing.css'):
        assemble.inline_assets(html, tmp_path)


def test_clean_neutral_page_passes() -> None:
    assert assemble.check(CLEAN_PAGE) == []


def test_teal_hex_fails() -> None:
    violations = assemble.check(_wrap_style('a { color: #008080; }'))
    assert any(v.rule == 'hex' and v.snippet == '#008080' for v in violations)


def test_rgb_function_fails() -> None:
    violations = assemble.check(_wrap_style('a { background: rgb(0,0,0); }'))
    assert any(v.rule == 'color-function' for v in violations)


def test_named_color_fails() -> None:
    violations = assemble.check(_wrap_style('a { color: teal; }'))
    assert any(v.rule == 'named-color' and v.snippet == 'teal' for v in violations)


def test_named_color_allowed_keyword_passes() -> None:
    violations = assemble.check(
        _wrap_style('a { color: currentColor; background: none; }')
    )
    assert violations == []


def test_border_radius_fails() -> None:
    violations = assemble.check(_wrap_style('.card { border-radius: 4px; }'))
    assert any(v.rule == 'radius' for v in violations)


def test_box_shadow_blur_fails() -> None:
    violations = assemble.check(
        _wrap_style('.card { box-shadow: 0 2px 8px var(--ink); }')
    )
    assert any(v.rule == 'shadow' for v in violations)


def test_box_shadow_allowed_inset_passes() -> None:
    violations = assemble.check(
        _wrap_style(
            ':root { --hair: 1px; }'
            ' .card { box-shadow: inset 0 0 0 var(--hair) var(--line); }'
        )
    )
    assert violations == []


def test_svg_rx_attribute_fails() -> None:
    violations = assemble.check('<svg><rect rx="6" ry="0"/></svg>')
    assert any(v.rule == 'radius' and 'rx' in v.snippet for v in violations)
    assert not any('ry' in v.snippet for v in violations)


def test_presentation_attribute_named_color_fails() -> None:
    violations = assemble.check('<svg><path fill="teal"/></svg>')
    assert any(v.rule == 'named-color' and v.snippet == 'teal' for v in violations)


def test_sample_marker_fails_without_flag() -> None:
    html = '<script>const DATA = /*SAMPLE*/{"a":1}/*SAMPLE*/;</script>'
    violations = assemble.check(html)
    sample_hits = sum(1 for v in violations if v.rule == 'sample')
    expected_markers = 2
    assert sample_hits == expected_markers


def test_issue_number_in_body_text_does_not_fail() -> None:
    assert assemble.check('<body><p>see issue #123 and #4567</p></body>') == []


def test_main_reports_violations_and_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / 'input.html'
    input_path.write_text(_wrap_style('a { color: teal; }'))
    monkeypatch.setattr('sys.argv', ['assemble.py', str(input_path), '--check-only'])

    assert assemble.main() == 1


def test_main_allow_sample_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / 'input.html'
    input_path.write_text('<script>const DATA = /*SAMPLE*/{}/*SAMPLE*/;</script>')
    monkeypatch.setattr(
        'sys.argv', ['assemble.py', str(input_path), '--check-only', '--allow-sample']
    )

    assert assemble.main() == 0


def test_main_writes_assembled_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / 'page.css').write_text('a { color: var(--ink); }')
    input_path = tmp_path / 'input.html'
    input_path.write_text('<link rel="stylesheet" href="page.css">')
    output_path = tmp_path / 'out.html'
    monkeypatch.setattr(
        'sys.argv', ['assemble.py', str(input_path), '-o', str(output_path)]
    )

    assert assemble.main() == 0
    assert '<style>a { color: var(--ink); }</style>' in output_path.read_text()


def test_main_missing_input_exits_with_clear_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / 'nope.html'
    monkeypatch.setattr('sys.argv', ['assemble.py', str(missing)])

    with pytest.raises(SystemExit, match='input not found'):
        assemble.main()


# TC-1: text-shadow other than none fails.
def test_text_shadow_non_none_fails() -> None:
    violations = assemble.check(_wrap_style('.t { text-shadow: 0 1px 0 var(--ink); }'))
    assert any(v.rule == 'shadow' for v in violations)


# TC-2: filter: drop-shadow(...) fails.
def test_filter_drop_shadow_fails() -> None:
    violations = assemble.check(
        _wrap_style('.card { filter: drop-shadow(0 2px 4px var(--ink)); }')
    )
    assert any(v.rule == 'shadow' for v in violations)


# TC-3: filter: blur(...) fails too, not just drop-shadow.
def test_filter_blur_fails() -> None:
    violations = assemble.check(_wrap_style('.card { filter: blur(4px); }'))
    assert any(v.rule == 'shadow' for v in violations)


# TC-4: any backdrop-filter fails.
def test_backdrop_filter_fails() -> None:
    violations = assemble.check(_wrap_style('.card { backdrop-filter: blur(2px); }'))
    assert any(v.rule == 'shadow' for v in violations)


# TC-5: non-zero SVG ry fails (rx="0" alone must not mask it).
def test_svg_ry_attribute_fails() -> None:
    violations = assemble.check('<svg><rect rx="0" ry="6"/></svg>')
    assert any(v.rule == 'radius' and 'ry' in v.snippet for v in violations)


# TC-6: hex color in an SVG presentation attribute fails.
def test_presentation_attribute_hex_fails() -> None:
    violations = assemble.check('<svg><path fill="#008080"/></svg>')
    assert any(v.rule == 'hex' and v.snippet == '#008080' for v in violations)


# TC-7: rgb() in an SVG presentation attribute fails.
def test_presentation_attribute_rgb_fails() -> None:
    violations = assemble.check('<svg><path stroke="rgb(0,128,128)"/></svg>')
    assert any(v.rule == 'color-function' for v in violations)


# TC-8: inline_assets raises ValueError on a literal closing tag inside
# inlined CSS/JS, which would otherwise prematurely close the wrapper tag.
def test_inline_assets_raises_on_literal_closing_style_tag(tmp_path: Path) -> None:
    (tmp_path / 'page.css').write_text('a::after { content: "</style>"; }')
    html = '<link rel="stylesheet" href="page.css">'
    with pytest.raises(ValueError, match='</style'):
        assemble.inline_assets(html, tmp_path)


def test_inline_assets_raises_on_literal_closing_script_tag(tmp_path: Path) -> None:
    (tmp_path / 'page.js').write_text('const s = "</script>";')
    html = '<script src="page.js"></script>'
    with pytest.raises(ValueError, match='</script'):
        assemble.inline_assets(html, tmp_path)


def test_inline_assets_falls_back_to_skill_assets_by_basename(
    tmp_path: Path,
) -> None:
    # An unrelated dir with no page.css of its own, linking "../page.css" the
    # way a filled template copied to .cc-arsenal/renders/ would.
    html = '<link rel="stylesheet" href="../page.css">'

    out = assemble.inline_assets(html, tmp_path)

    real_css = assemble.ASSETS_DIR.joinpath('page.css').read_text(encoding='utf-8')
    assert f'<style>{real_css}</style>' in out


# TC-9: font-size below the 15px floor, in px, fails.
def test_font_size_px_below_floor_fails() -> None:
    violations = assemble.check(_wrap_style('.meta { font-size: 12px; }'))
    assert any(v.rule == 'font-size' for v in violations)


# TC-10: font-size below the floor in rem (0.9375rem == 15px at a 16px root).
def test_font_size_rem_below_floor_fails() -> None:
    violations = assemble.check(_wrap_style('.meta { font-size: 0.8rem; }'))
    assert any(v.rule == 'font-size' for v in violations)


# TC-11: a small-size keyword fails regardless of unit.
def test_font_size_keyword_fails() -> None:
    violations = assemble.check(_wrap_style('.meta { font-size: small; }'))
    assert any(v.rule == 'font-size' for v in violations)


# TC-12: the font shorthand's size component is checked too.
def test_font_shorthand_below_floor_fails() -> None:
    violations = assemble.check(
        _wrap_style('.meta { font: 600 12px/1.4 Geist, sans-serif; }')
    )
    assert any(v.rule == 'font-size' for v in violations)


# TC-13: an SVG font-size presentation attribute below 15 fails, unitless or px.
def test_svg_font_size_attribute_fails() -> None:
    violations = assemble.check('<svg><text font-size="12">hi</text></svg>')
    assert any(v.rule == 'font-size' for v in violations)


# TC-14: 15px and 20px both clear the floor, including var()/calc().
def test_font_size_at_and_above_floor_passes() -> None:
    violations = assemble.check(
        _wrap_style('.body { font-size: 15px; } .h2 { font-size: 20px; }')
    )
    assert not any(v.rule == 'font-size' for v in violations)


def test_font_size_var_and_calc_allowed() -> None:
    violations = assemble.check(
        _wrap_style(
            '.a { font-size: var(--fs-body); } .b { font-size: calc(1rem - 2px); }'
        )
    )
    assert not any(v.rule == 'font-size' for v in violations)


def test_main_in_place_output_same_as_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / 'page.css').write_text('a { color: var(--ink); }')
    page = tmp_path / 'review-x.html'
    page.write_text('<link rel="stylesheet" href="page.css">')
    monkeypatch.setattr('sys.argv', ['assemble.py', str(page), '-o', str(page)])

    assert assemble.main() == 0
    assert '<style>a { color: var(--ink); }</style>' in page.read_text()


# --- raw-length / style-attr gate: plan-spec case table -------------------


@pytest.mark.parametrize(
    ('css', 'expect_raw_length'),
    [
        ('.a{padding:12px}', True),
        ('.a{padding:var(--space-3)}', False),
        (':root{--space-3:12px}', False),
        (
            ':root:not([data-theme="light"])'
            '{@media (prefers-color-scheme: dark){--x:3px}}',
            False,
        ),
        ('.a{--mark-top:8px}', True),
        (
            '.a{margin:0px; flex:1 1 0; line-height:1.25; width:50%; '
            'transition:opacity 120ms; transform:rotate(45deg);}',
            False,
        ),
        ('.a{letter-spacing:-0.02em}', True),
        ('.a{max-width:62ch}', True),
        ('.a{height:70vh}', True),
        ('.a{font-size:1rem}', True),
        ('.a{width:calc(100% - 16px)}', True),
        ('.a{width:calc(100% - var(--space-4))}', False),
        ('@media (max-width:720px){.a{color:red}}', False),
        ('@media (max-width:700px){.a{color:red}}', True),
        ('/* by 1px */ .a{content:"12px"}', False),
    ],
)
def test_raw_length_case_table(css: str, expect_raw_length: bool) -> None:
    violations = assemble.check(_wrap_style(css))
    hit = any(v.rule == 'raw-length' for v in violations)
    assert hit == expect_raw_length


@pytest.mark.parametrize(
    ('style_value', 'expect_violation'),
    [
        ('--v:.42', False),
        ('--v:${n}', False),
        ('width:12px', True),
        ('--x:12px', True),
        ('color:var(--ink)', True),
        ('--v:${n}px', True),
    ],
)
def test_style_attr_case_table(style_value: str, expect_violation: bool) -> None:
    violations = assemble.check(f'<div style="{style_value}"></div>')
    hit = any(v.rule == 'style-attr' for v in violations)
    assert hit == expect_violation


def test_text_custom_property_below_floor_fails() -> None:
    violations = assemble.check(_wrap_style(':root{--text-sm:12px}'))
    assert any(v.rule == 'font-size' for v in violations)


def test_box_shadow_allows_hair_token_shadow_literal_still_rejected() -> None:
    # A bare 1px shadow is now itself a raw-length violation outside :root,
    # even though BOX_SHADOW_PART_RE still recognizes the literal for shadow.
    violations = assemble.check(
        _wrap_style('.a { box-shadow: inset 0 0 0 1px var(--ink); }')
    )
    assert any(v.rule == 'raw-length' for v in violations)


# --- shipped-pages regression: every real page the skill ships must be clean


RENDER_ASSETS_DIR = Path(__file__).resolve().parents[2] / 'skills' / 'render' / 'assets'


def _shipped_html_pages() -> list[Path]:
    pages = sorted(RENDER_ASSETS_DIR.glob('*.html'))
    pages += sorted((RENDER_ASSETS_DIR / 'templates').glob('*.html'))
    return pages


@pytest.mark.parametrize('page', _shipped_html_pages(), ids=lambda p: p.name)
def test_shipped_page_passes_gate(page: Path) -> None:
    assembled = assemble.inline_assets(page.read_text(encoding='utf-8'), page.parent)
    violations = [v for v in assemble.check(assembled) if v.rule != 'sample']
    assert violations == [], f'{page.name}: {violations}'


# --- diagrams.js guard: only allowed .style. use is setProperty('--...')


def test_diagrams_js_has_no_direct_style_writes() -> None:
    diagrams_js = RENDER_ASSETS_DIR / 'diagrams.js'
    if not diagrams_js.is_file():
        pytest.skip('diagrams.js not landed yet')
    text = diagrams_js.read_text(encoding='utf-8')
    for m in re.finditer(r'\.style\.', text):
        tail = text[m.end() : m.end() + len("setProperty('--")]
        assert tail == "setProperty('--", (
            f".style. used outside setProperty('--...') near: "
            f'{text[max(0, m.start() - 20) : m.end() + 20]!r}'
        )
