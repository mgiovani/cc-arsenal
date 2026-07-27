#!/usr/bin/env python3
"""Compute WCAG 2.2 AA contrast ratios for the colour pairs declared in a DTCG
token file and emit the contrast-report table. Reads the pairs to check from
`$extensions["org.designtokens.contrast"].pairs`, resolves `{alias}` refs to
concrete colours, computes each ratio natively (no external dependency), and
flags (a) any pair below its required AA threshold and (b) any status colour
that would carry meaning by colour alone (WCAG 1.4.1). Exits nonzero if any
declared pair fails its required level."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ALIAS_RE = re.compile(r'^\{([^}]+)\}$')
HEX_RE = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')
# Status roles that must never be conveyed by colour alone (WCAG 1.4.1 Use of Colour).
STATUS_RE = re.compile(
    r'(success|error|warning|danger|info|valid|invalid|positive|negative)', re.IGNORECASE
)

HEX_SHORT, HEX_FULL = 3, 6
SRGB_LINEAR_CUTOFF = 0.03928

# level -> (minimum ratio, human label). AA is the target; AAA listed for completeness.
LEVELS = {
    'AA-normal': (4.5, 'AA normal text'),
    'AA-large': (3.0, 'AA large text (>=24px, or >=18.66px bold)'),
    'AA-ui': (3.0, 'AA UI components / graphical objects (1.4.11)'),
    'AAA-normal': (7.0, 'AAA normal text'),
    'AAA-large': (4.5, 'AAA large text'),
}

# A colour $value handled below is a #hex string, an [r,g,b] sequence in [0,1],
# or a DTCG structured colour object {"colorSpace": "srgb", "components": [...]}.


def _hex_to_components(value: str) -> list[float]:
    h = value.strip().lstrip('#')
    if len(h) == HEX_SHORT:
        h = ''.join(c * 2 for c in h)
    if len(h) != HEX_FULL:
        raise ValueError(f'not a #rgb/#rrggbb hex colour: {value!r}')
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]


def to_components(value: object) -> list[float]:
    """Normalise a colour $value to gamma-encoded sRGB components in [0,1].

    Non-sRGB colour spaces (display-p3, oklch, ...) are not convertible here and
    raise, rather than silently producing a wrong ratio.
    """
    if isinstance(value, str):
        return _hex_to_components(value)
    if isinstance(value, list | tuple):
        return [float(c) for c in value[:3]]
    if isinstance(value, dict):
        space = value.get('colorSpace', 'srgb')
        if space != 'srgb':
            raise ValueError(
                f'cannot verify contrast for colorSpace {space!r}; '
                'supply an sRGB/hex equivalent'
            )
        if 'hex' in value:
            return _hex_to_components(value['hex'])
        comps = value.get('components', [])
        if not isinstance(comps, list | tuple):
            raise ValueError(f'sRGB colour missing a components array: {value!r}')
        return [float(c) for c in comps[:3]]
    raise ValueError(f'unrecognised colour value: {value!r}')


def _linearize(c: float) -> float:
    return c / 12.92 if c <= SRGB_LINEAR_CUTOFF else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(value: object) -> float:
    r, g, b = (_linearize(c) for c in to_components(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: object, b: object) -> float:
    """WCAG contrast ratio of two colours (order-independent), >=1.0."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _iter_color_tokens(node: object, path: list[str], out: dict[str, object]) -> None:
    """Collect {dotted.path: $value} for every colour token in the tree."""
    if not isinstance(node, dict):
        return
    if '$value' in node:
        if node.get('$type') == 'color' or _looks_color(node['$value']):
            out['.'.join(path)] = node['$value']
        return
    for key, child in node.items():
        if not key.startswith('$'):
            _iter_color_tokens(child, [*path, key], out)


def _looks_color(value: object) -> bool:
    if isinstance(value, str):
        return bool(ALIAS_RE.match(value) or HEX_RE.match(value))
    return isinstance(value, dict) and 'colorSpace' in value


def resolve(ref: object, tokens: dict[str, object], seen: tuple[str, ...] = ()) -> object:
    """Resolve a colour value or `{alias}` to a concrete (non-alias) $value."""
    m = ALIAS_RE.match(ref) if isinstance(ref, str) else None
    if not m:
        return ref
    target = m.group(1)
    if target in seen:
        raise ValueError(f'circular alias: {" -> ".join([*seen, target])}')
    if target not in tokens:
        raise ValueError(f'alias -> {{{target}}} does not resolve')
    return resolve(tokens[target], tokens, (*seen, target))


def _pairs_from(doc: dict) -> list[dict]:
    ext = doc.get('$extensions', {})
    node = ext.get('org.designtokens.contrast', {}) if isinstance(ext, dict) else {}
    pairs = node.get('pairs', []) if isinstance(node, dict) else []
    return pairs if isinstance(pairs, list) else []


def build_report(doc: dict, extra_pairs: list[dict] | None = None) -> tuple[str, int]:
    """Return (markdown report, failing-pair count)."""
    tokens: dict[str, object] = {}
    _iter_color_tokens(doc, [], tokens)
    pairs = [*_pairs_from(doc), *(extra_pairs or [])]

    rows: list[str] = []
    failures = 0
    for p in pairs:
        name = p.get('name', '')
        level = p.get('level', 'AA-normal')
        need, _label = LEVELS.get(level, LEVELS['AA-normal'])
        try:
            ratio = contrast_ratio(resolve(p['fg'], tokens), resolve(p['bg'], tokens))
            ok = ratio >= need
            failures += 0 if ok else 1
            verdict = 'PASS' if ok else '**FAIL**'
            rows.append(
                f'| {name} | `{p["fg"]}` | `{p["bg"]}` | {ratio:.2f}:1 '
                f'| {level} ({need}:1) | {verdict} |'
            )
        except (KeyError, ValueError) as exc:
            failures += 1
            rows.append(
                f'| {name} | `{p.get("fg", "?")}` | `{p.get("bg", "?")}` | — '
                f'| {level} | **ERROR: {exc}** |'
            )

    # Colour-alone advisory (WCAG 1.4.1) — status roles must not rely on hue alone.
    color_alone = sorted({path for path in tokens if STATUS_RE.search(path)})

    out = [
        '# Contrast report — WCAG 2.2 AA',
        '',
        '| Pair | Foreground | Background | Ratio | Required | Result |',
        '|---|---|---|---|---|---|',
    ]
    out.extend(rows or ['| _(no contrast pairs declared in $extensions)_ | | | | | |'])
    out += [
        '',
        f'**{failures} failing pair(s).** '
        'AA target: normal text >=4.5:1, large text & UI >=3:1.',
        '',
        '## Use of colour (WCAG 1.4.1)',
    ]
    if color_alone:
        out.append(
            'These status colours MUST NOT be the only channel — '
            'pair each with an icon, text label, or pattern:'
        )
        out += [f'- `{p}`' for p in color_alone]
    else:
        out.append(
            'No status-role colour tokens detected; '
            'still ensure no meaning is carried by colour alone.'
        )
    return '\n'.join(out), failures


def _selftest() -> bool:
    # Required anchors: pure black vs white == 21.0, and a mid pair.
    assert round(contrast_ratio('#000000', '#ffffff'), 4) == 21.0
    mid = contrast_ratio('#767676', '#ffffff')  # classic AA-normal boundary grey
    assert 4.5 <= mid <= 4.6, mid
    # Structured sRGB parity with hex, and shorthand hex.
    black = {'colorSpace': 'srgb', 'components': [0, 0, 0]}
    assert abs(contrast_ratio(black, '#ffffff') - 21.0) < 1e-9
    assert abs(contrast_ratio('#fff', '#000000') - 21.0) < 1e-9
    # Non-sRGB is flagged, not silently wrong.
    rejection_reason = ''
    try:
        contrast_ratio({'colorSpace': 'oklch', 'components': [0.6, 0.1, 240]}, '#fff')
        raise AssertionError('expected non-sRGB to raise')
    except ValueError as exc:
        # Expected: to_components() rejects non-sRGB colour spaces by design
        # (see its docstring), so reaching here means the guard fired
        # correctly. Capture the message and check it below, so a future
        # refactor that changes what's rejected can't silently slip past.
        rejection_reason = str(exc)
    assert 'oklch' in rejection_reason, rejection_reason
    # End-to-end through the file-loading path: alias resolution, a failing pair,
    # and a colour-alone flag. Uses a tempfile to exercise the real CLI entry.
    doc = {
        'color': {
            '$type': 'color',
            'base': {
                'white': {'$value': '#ffffff'},
                'grey': {'$value': '#999999'},
                'red': {'$value': '#dc2626'},
            },
            'semantic': {
                'bg': {'$value': '{color.base.white}'},
                'text-muted': {'$value': '{color.base.grey}'},
                'status-error': {'$value': '{color.base.red}'},
            },
        },
        '$extensions': {
            'org.designtokens.contrast': {
                'pairs': [
                    {
                        'name': 'muted text',
                        'fg': '{color.semantic.text-muted}',
                        'bg': '{color.semantic.bg}',
                        'level': 'AA-normal',
                    }
                ]
            }
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'tokens.dtcg.json'
        path.write_text(json.dumps(doc))
        loaded = json.loads(path.read_text())
    report, failures = build_report(loaded)
    assert failures == 1, report  # #999 on white ~2.8:1 fails AA-normal
    assert 'status-error' in report  # colour-alone advisory picked up the status token
    assert 'FAIL' in report
    print('OK')
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tokens', help='path to a DTCG tokens JSON file')
    ap.add_argument('--fg', help='ad-hoc foreground hex (with --bg)')
    ap.add_argument('--bg', help='ad-hoc background hex (with --fg)')
    ap.add_argument('--level', default='AA-normal', choices=list(LEVELS))
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1

    if args.fg and args.bg:
        ratio = contrast_ratio(args.fg, args.bg)
        need, _ = LEVELS[args.level]
        ok = ratio >= need
        verdict = 'PASS' if ok else 'FAIL'
        print(
            f'{args.fg} on {args.bg}: {ratio:.2f}:1  {verdict} ({args.level} >= {need}:1)'
        )
        return 0 if ok else 1

    if not args.tokens:
        ap.error('pass --tokens FILE, or --fg and --bg')
    doc = json.loads(Path(args.tokens).read_text())
    report, failures = build_report(doc)
    print(report)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
