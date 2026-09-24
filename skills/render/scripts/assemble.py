#!/usr/bin/env python3
"""Inline a render page's local stylesheet/script links into one file, then
gate the result against the skill's monochrome, square-corner, token-only
design contract (zero hue anywhere, radius 0, no shadows/blur, no raw CSS
length outside :root, no leftover sample data).

Usage: assemble.py INPUT.html [-o OUTPUT.html] [--allow-sample] [--check-only]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

LINK_RE = re.compile(r'<link\b([^>]*)>', re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r'<script\b([^>]*)>\s*</script>', re.IGNORECASE)
ATTR_RE = re.compile(r"""([a-zA-Z:_][a-zA-Z0-9:_.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
REMOTE_HREF_RE = re.compile(r'^(?:[a-z][a-z0-9+.-]*:)?//', re.IGNORECASE)

STYLE_BLOCK_RE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.IGNORECASE | re.DOTALL)
STYLE_ATTR_RE = re.compile(
    r"""(?<![\w-])style\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE
)
PRESENTATION_ATTR_RE = re.compile(
    r"""(?<![\w-])(fill|stroke|stop-color|color|flood-color|lighting-color)"""
    r"""\s*=\s*(?:"([^"]*)"|'([^']*)')""",
    re.IGNORECASE,
)
RADIUS_ATTR_RE = re.compile(r"""(?<![\w-])(rx|ry)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
SVG_FONT_SIZE_ATTR_RE = re.compile(
    r"""(?<![\w-])font-size\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE
)
DECL_RE = re.compile(r'([a-zA-Z-][\w-]*)\s*:\s*([^;{}]+)(?=[;}])')
LENGTH_RE = re.compile(
    r'(?<![\w.-])(-?(?:\d*\.)?\d+)'
    r'(px|rem|em|ch|ex|lh|rlh|vw|vh|vmin|vmax|vi|vb|dvh|svh|lvh|dvw|svw|lvw|'
    r'cqw|cqh|cqi|cqb|cqmin|cqmax|cm|mm|in|pt|pc|q)\b',
    re.IGNORECASE,
)
BREAKPOINTS = frozenset({'600px', '720px', '860px', '1100px'})
AT_PRELUDE_RE = re.compile(r'@(?:media|container)[^{]*')
CSS_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
CSS_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
STYLE_ATTR_INTERP_RE = re.compile(r'\$\{[^}]*\}')
STYLE_ATTR_UNITLESS_RE = re.compile(r'^-?(\d*\.)?\d+$')
FONT_SIZE_TOKEN_RE = re.compile(r'^(-?\d*\.?\d+)(px|rem|em|%)$', re.IGNORECASE)
FONT_SIZE_SMALL_KEYWORDS = {'xx-small', 'x-small', 'small', 'smaller'}
FONT_SIZE_FLOOR_PX = 15
FONT_SIZE_FLOOR_EM = FONT_SIZE_FLOOR_PX / 16  # 0.9375rem/em at a 16px root
FONT_SIZE_FLOOR_PERCENT = FONT_SIZE_FLOOR_EM * 100  # 93.75%
HEX_RE = re.compile(r'#([0-9a-fA-F]{3,8})\b')
COLOR_FUNC_RE = re.compile(
    r'\b(rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch|color)\(', re.IGNORECASE
)
VAR_RE = re.compile(r'var\([^)]*\)')
WORD_RE = re.compile(r'[a-zA-Z]+')
BOX_SHADOW_PART_RE = re.compile(
    r'^\s*inset\s+0\s+0\s+0\s+(?:1px|var\(--hair\))\s+var\(--[\w-]+\)\s*$'
)
SAMPLE_MARKER = '/*SAMPLE*/'
HEX_FULL_LEN = 6
ASSETS_DIR = Path(__file__).resolve().parent.parent / 'assets'

ALLOWED_KEYWORDS = {
    'transparent',
    'currentcolor',
    'inherit',
    'initial',
    'unset',
    'revert',
    'none',
}

NAMED_COLORS = frozenset(
    """aliceblue antiquewhite aqua aquamarine azure beige bisque black
    blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse
    chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan
    darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta
    darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
    darkslateblue darkslategray darkslategrey darkturquoise darkviolet
    deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite
    forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green
    greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender
    lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
    lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
    lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
    lightyellow lime limegreen linen magenta maroon mediumaquamarine
    mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue
    mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream
    mistyrose moccasin navajowhite navy oldlace olive olivedrab orange
    orangered orchid palegoldenrod palegreen paleturquoise palevioletred
    papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red
    rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell
    sienna silver skyblue slateblue slategray slategrey snow springgreen
    steelblue tan teal thistle tomato turquoise violet wheat white
    whitesmoke yellow yellowgreen""".split()  # noqa: SIM905 -- readable as prose, not a list literal
)

COLOR_PROP_PREFIXES = ('border', 'outline', 'text-decoration', 'column-rule')
COLOR_PROPS = {
    'color',
    'background',
    'background-color',
    'fill',
    'stroke',
    'caret-color',
    'accent-color',
    'scrollbar-color',
    'stop-color',
}
SHADOW_PROPS = {'box-shadow', 'text-shadow', 'filter', 'backdrop-filter'}


class Violation(NamedTuple):
    line: int
    rule: str
    snippet: str


def _parse_attrs(attr_text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(attr_text):
        name, dq, sq = match.groups()
        attrs[name.lower()] = dq if dq is not None else sq
    return attrs


def _is_local(href: str) -> bool:
    return bool(href) and not REMOTE_HREF_RE.match(href) and not href.startswith('data:')


def _read_local(base_dir: Path, href: str, kind: str) -> str:
    path = (base_dir / href).resolve()
    if path.is_file():
        return path.read_text(encoding='utf-8')
    # ponytail: a filled template copied out of the skill tree (e.g. into
    # .cc-arsenal/renders/) keeps its relative "../page.css" link, which no
    # longer resolves. Fall back to the skill's own assets/ by basename so
    # `assemble.py OUT.html -o OUT.html` still works in place.
    fallback = ASSETS_DIR / Path(href).name
    if fallback.is_file():
        return fallback.read_text(encoding='utf-8')
    raise FileNotFoundError(f'missing {kind} referenced by input: {href} ({path})')


def inline_assets(html: str, base_dir: Path) -> str:
    """Replace local <link rel=stylesheet> and <script src> with their file contents."""

    def repl_link(match: re.Match[str]) -> str:
        attrs = _parse_attrs(match.group(1))
        href = attrs.get('href', '')
        if attrs.get('rel', '').lower() != 'stylesheet' or not _is_local(href):
            return match.group(0)
        css = _read_local(base_dir, href, 'stylesheet')
        if '</style' in css.lower():
            raise ValueError(f'{href}: inlined CSS contains a literal "</style"')
        return f'<style>{css}</style>'

    def repl_script(match: re.Match[str]) -> str:
        attrs = _parse_attrs(match.group(1))
        src = attrs.get('src', '')
        if not _is_local(src):
            return match.group(0)
        js = _read_local(base_dir, src, 'script')
        if '</script' in js.lower():
            raise ValueError(f'{src}: inlined JS contains a literal "</script"')
        return f'<script>{js}</script>'

    html = LINK_RE.sub(repl_link, html)
    return SCRIPT_SRC_RE.sub(repl_script, html)


def _line_at(html: str, pos: int) -> int:
    return html.count('\n', 0, pos) + 1


def _is_color_bearing_prop(prop: str) -> bool:
    return prop in COLOR_PROPS or prop.startswith(COLOR_PROP_PREFIXES)


def _is_radius_prop(prop: str) -> bool:
    return (
        prop in ('rx', 'ry')
        or prop == 'border-radius'
        or (prop.startswith('border-') and prop.endswith('-radius'))
    )


def _is_all_zero(value: str) -> bool:
    tokens = value.replace('!important', '').split()
    return bool(tokens) and all(token in ('0', '0px') for token in tokens)


def _shadow_ok(prop: str, value: str) -> bool:
    v = value.strip()
    if prop == 'box-shadow':
        return v.lower() == 'none' or all(
            BOX_SHADOW_PART_RE.match(part) for part in v.split(',')
        )
    if prop == 'text-shadow':
        return v.lower() == 'none'
    if prop == 'filter':
        lowered = v.lower()
        return 'drop-shadow' not in lowered and 'blur(' not in lowered
    return prop != 'backdrop-filter'


def _font_size_token(value: str) -> str | None:
    """Pick the size token out of a font-size value or a font shorthand.

    A font shorthand's family list comes after the first comma and can
    contain words that look like tokens, so only the part before it is
    scanned. var()/calc() tokens never match and are silently allowed.
    """
    meta = value.split(',', 1)[0]
    for raw_token in meta.split():
        token = raw_token.split('/', 1)[0]
        if FONT_SIZE_TOKEN_RE.match(token) or token.lower() in FONT_SIZE_SMALL_KEYWORDS:
            return token
    return None


def _font_size_below_floor(token: str) -> bool:
    m = FONT_SIZE_TOKEN_RE.match(token)
    if not m:
        return token.lower() in FONT_SIZE_SMALL_KEYWORDS
    num, unit = float(m.group(1)), m.group(2).lower()
    if unit == 'px':
        return num < FONT_SIZE_FLOOR_PX
    if unit in ('rem', 'em'):
        return num < FONT_SIZE_FLOOR_EM
    return num < FONT_SIZE_FLOOR_PERCENT  # unit == '%'


def _svg_font_size_below_floor(value: str) -> bool:
    """SVG's font-size attribute takes a bare number (px-equivalent) or px."""
    value = value.strip()
    if 'var(' in value or 'calc(' in value:
        return False
    if _font_size_token(value) is not None:
        return _font_size_below_floor(value)
    try:
        return float(value) < FONT_SIZE_FLOOR_PX  # unitless, SVG user units
    except ValueError:
        return False


def _find_named_colors(value: str) -> list[tuple[int, str]]:
    scrubbed = VAR_RE.sub(lambda m: ' ' * len(m.group(0)), value)
    return [
        (m.start(), m.group(0))
        for m in WORD_RE.finditer(scrubbed)
        if m.group(0).lower() in NAMED_COLORS
        and m.group(0).lower() not in ALLOWED_KEYWORDS
    ]


def _hex_violations(html: str, text: str, offset: int) -> list[Violation]:
    out = []
    for m in HEX_RE.finditer(text):
        digits = m.group(1)
        if (
            len(digits) == HEX_FULL_LEN
            and digits[0:2].lower() == digits[2:4].lower() == digits[4:6].lower()
        ):
            continue
        out.append(Violation(_line_at(html, offset + m.start()), 'hex', m.group(0)))
    return out


def _color_function_violations(html: str, text: str, offset: int) -> list[Violation]:
    # color-mix( never matches: the '-' between "color" and "(" breaks COLOR_FUNC_RE.
    return [
        Violation(_line_at(html, offset + m.start()), 'color-function', m.group(0))
        for m in COLOR_FUNC_RE.finditer(text)
    ]


def _css_regions(html: str) -> list[tuple[str, int]]:
    regions = [(m.group(1), m.start(1)) for m in STYLE_BLOCK_RE.finditer(html)]
    for m in STYLE_ATTR_RE.finditer(html):
        group_index = 1 if m.group(1) is not None else 2
        regions.append((m.group(group_index), m.start(group_index)))
    return regions


def _style_block_regions(html: str) -> list[tuple[str, int]]:
    return [(m.group(1), m.start(1)) for m in STYLE_BLOCK_RE.finditer(html)]


def _scrub_css_text(text: str) -> str:
    """Blank out comments and quoted strings, same length, newlines kept.

    Keeps line numbers correct for later offset math, and stops a comment
    like "overlaps its neighbour by 1px" or a `content:"12px"` value from
    tripping the raw-length rule or confusing the :root brace walker.
    """

    def _blank(match: re.Match[str]) -> str:
        return ''.join(ch if ch == '\n' else ' ' for ch in match.group(0))

    text = CSS_COMMENT_RE.sub(_blank, text)
    return CSS_STRING_RE.sub(_blank, text)


def _root_exempt_spans(scrubbed: str) -> list[tuple[int, int]]:
    """Spans of every outermost rule whose prelude starts with :root.

    Only depth-0 rules are checked; a matching rule's whole span (through
    its matching close brace, including anything nested inside it such as
    a `@media (prefers-color-scheme: dark) { ... }` block) is exempt.
    """
    spans: list[tuple[int, int]] = []
    depth = 0
    prelude_start = 0
    open_pos: int | None = None
    for i, ch in enumerate(scrubbed):
        if ch == '{':
            if depth == 0:
                prelude = scrubbed[prelude_start:i].strip()
                open_pos = i if prelude.startswith(':root') else None
            depth += 1
        elif ch == '}':
            depth = max(depth - 1, 0)
            if depth == 0:
                if open_pos is not None:
                    spans.append((open_pos, i))
                    open_pos = None
                prelude_start = i + 1
    return spans


def _in_spans(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def _length_is_zero(number: str) -> bool:
    try:
        return float(number) == 0
    except ValueError:
        return False


def _raw_length_violations(html: str, text: str, offset: int) -> list[Violation]:
    scrubbed = _scrub_css_text(text)
    root_spans = _root_exempt_spans(scrubbed)
    prelude_spans = [(m.start(), m.end()) for m in AT_PRELUDE_RE.finditer(scrubbed)]

    out = []
    for m in LENGTH_RE.finditer(scrubbed):
        if _in_spans(m.start(), root_spans) or _in_spans(m.start(), prelude_spans):
            continue
        if _length_is_zero(m.group(1)):
            continue
        out.append(
            Violation(_line_at(html, offset + m.start()), 'raw-length', m.group(0))
        )

    for start, end in prelude_spans:
        if _in_spans(start, root_spans):
            continue
        for lm in LENGTH_RE.finditer(scrubbed[start:end]):
            if lm.group(0) not in BREAKPOINTS:
                pos = start + lm.start()
                out.append(
                    Violation(_line_at(html, offset + pos), 'raw-length', lm.group(0))
                )
    return out


def _style_attr_violations(html: str) -> list[Violation]:
    """A style="..." attribute may only set unitless custom properties.

    ${...} interpolations are stripped from the whole value first, not
    per-declaration: an interpolation's own source (e.g. a JS template
    literal joining parts with `';'`) can contain a literal ";" that would
    otherwise split one declaration into two.
    """
    out = []
    for m in STYLE_ATTR_RE.finditer(html):
        group_index = 1 if m.group(1) is not None else 2
        value_text = m.group(group_index)
        base_offset = m.start(group_index)
        stripped = STYLE_ATTR_INTERP_RE.sub('', value_text)
        for raw_decl in stripped.split(';'):
            decl = raw_decl.strip()
            if not decl:
                continue
            prop, sep, value = decl.partition(':')
            prop = prop.strip()
            value = value.strip()
            ok = (
                bool(sep)
                and prop.startswith('--')
                and (value == '' or STYLE_ATTR_UNITLESS_RE.match(value))
            )
            if not ok:
                out.append(Violation(_line_at(html, base_offset), 'style-attr', decl))
    return out


def _presentation_attr_regions(html: str) -> list[tuple[str, int]]:
    regions = []
    for m in PRESENTATION_ATTR_RE.finditer(html):
        group_index = 2 if m.group(2) is not None else 3
        regions.append((m.group(group_index), m.start(group_index)))
    return regions


def _css_declaration_violations(html: str, text: str, offset: int) -> list[Violation]:
    out = []
    for m in DECL_RE.finditer(text):
        prop, value = m.group(1).lower(), m.group(2)
        value_offset = offset + m.start(2)
        if _is_color_bearing_prop(prop):
            for local_pos, word in _find_named_colors(value):
                out.append(
                    Violation(
                        _line_at(html, value_offset + local_pos), 'named-color', word
                    )
                )
        if _is_radius_prop(prop) and not _is_all_zero(value):
            out.append(
                Violation(
                    _line_at(html, value_offset), 'radius', f'{prop}: {value.strip()}'
                )
            )
        if prop in SHADOW_PROPS and not _shadow_ok(prop, value):
            out.append(
                Violation(
                    _line_at(html, value_offset), 'shadow', f'{prop}: {value.strip()}'
                )
            )
        if prop in ('font-size', 'font') or prop.startswith('--text'):
            token = _font_size_token(value)
            if token is not None and _font_size_below_floor(token):
                out.append(
                    Violation(
                        _line_at(html, value_offset),
                        'font-size',
                        f'{prop}: {value.strip()}',
                    )
                )
    return out


def check(html: str) -> list[Violation]:
    """Gate an assembled render page; pure, the whole document in, violations out."""
    violations: list[Violation] = []

    for text, offset in _css_regions(html):
        violations += _hex_violations(html, text, offset)
        violations += _color_function_violations(html, text, offset)
        violations += _css_declaration_violations(html, text, offset)

    for text, offset in _style_block_regions(html):
        violations += _raw_length_violations(html, text, offset)

    violations += _style_attr_violations(html)

    for value, offset in _presentation_attr_regions(html):
        violations += _hex_violations(html, value, offset)
        violations += _color_function_violations(html, value, offset)
        for local_pos, word in _find_named_colors(value):
            violations.append(
                Violation(_line_at(html, offset + local_pos), 'named-color', word)
            )

    for m in RADIUS_ATTR_RE.finditer(html):
        group_index = 2 if m.group(2) is not None else 3
        value = m.group(group_index)
        if value.strip() != '0':
            violations.append(
                Violation(_line_at(html, m.start(1)), 'radius', f'{m.group(1)}="{value}"')
            )

    for m in SVG_FONT_SIZE_ATTR_RE.finditer(html):
        value = m.group(1) if m.group(1) is not None else m.group(2)
        if _svg_font_size_below_floor(value):
            violations.append(
                Violation(_line_at(html, m.start()), 'font-size', f'font-size="{value}"')
            )

    violations += [
        Violation(_line_at(html, m.start()), 'sample', SAMPLE_MARKER)
        for m in re.finditer(re.escape(SAMPLE_MARKER), html)
    ]

    violations.sort(key=lambda v: v.line)
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'input', type=Path, help='source HTML with local <link>/<script> refs'
    )
    parser.add_argument(
        '-o', '--output', type=Path, help='write assembled HTML here (default: stdout)'
    )
    parser.add_argument(
        '--allow-sample', action='store_true', help='allow a leftover /*SAMPLE*/ marker'
    )
    parser.add_argument(
        '--check-only', action='store_true', help='gate only, never write output'
    )
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f'error: input not found: {args.input}')
    html = args.input.read_text(encoding='utf-8')

    try:
        assembled = inline_assets(html, args.input.resolve().parent)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f'error: {exc}') from exc

    violations = [
        v for v in check(assembled) if not (args.allow_sample and v.rule == 'sample')
    ]
    if violations:
        report_path = args.output if args.output else args.input
        for v in violations:
            print(  # noqa: T201 -- CLI script, stdlib-only by design
                f'{report_path}:{v.line}: {v.rule}: {v.snippet}', file=sys.stderr
            )
        return 1

    if not args.check_only:
        if args.output:
            args.output.write_text(assembled, encoding='utf-8')
        else:
            print(assembled)  # noqa: T201 -- CLI script, stdlib-only by design
    return 0


if __name__ == '__main__':
    sys.exit(main())
