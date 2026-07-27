#!/usr/bin/env python3
"""Validate a token file against the DTCG 2025.10 shape
(https://www.designtokens.org/tr/2025.10/ — STABLE, never /tr/drafts/):

  1. every token (an object with `$value`) has a `$type` that is resolvable —
     declared on the token or inherited from an ancestor group;
  2. every `{group.token.path}` alias resolves to a real token;
  3. no circular alias chains.

Findings print as `ERROR  path  message`; exits nonzero on any error."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ALIAS_RE = re.compile(r'\{([^}]+)\}')
PURE_ALIAS_RE = re.compile(r'^\{([^}]+)\}$')

Error = tuple[str, str]  # (dotted path, message)


def collect(
    node: object,
    path: list[str],
    inherited_type: str | None,
    tokens: dict[str, object],
    types: dict[str, str | None],
) -> None:
    """Walk the tree, recording each token's $value and its own/inherited $type.
    Alias-derived types are resolved later, in validate's second pass."""
    if not isinstance(node, dict):
        return
    if '$value' in node:
        dotted = '.'.join(path)
        tokens[dotted] = node['$value']
        types[dotted] = node.get('$type', inherited_type)
        return
    group_type = node.get('$type', inherited_type)
    for key, child in node.items():
        if not key.startswith('$'):
            collect(child, [*path, key], group_type, tokens, types)


def _refs(value: object) -> list[str]:
    """Every {alias} target referenced anywhere inside a token value."""
    if isinstance(value, str):
        return ALIAS_RE.findall(value)
    if isinstance(value, dict):
        return [t for v in value.values() for t in _refs(v)]
    if isinstance(value, list | tuple):
        return [t for v in value for t in _refs(v)]
    return []


def check_aliases(tokens: dict[str, object], errors: list[Error]) -> None:
    # Existence of every referenced target.
    for path, value in tokens.items():
        for target in _refs(value):
            if target not in tokens:
                errors.append((path, f'alias -> {{{target}}} does not resolve'))

    # Cycle detection over pure-alias edges ({a.b} whose whole value is one alias).
    edges: dict[str, str] = {}
    for path, value in tokens.items():
        m = PURE_ALIAS_RE.match(value) if isinstance(value, str) else None
        if m and m.group(1) in tokens:
            edges[path] = m.group(1)

    for start in edges:
        seen, cur = [start], start
        while cur in edges:
            cur = edges[cur]
            if cur in seen:
                errors.append((start, f'circular alias: {" -> ".join([*seen, cur])}'))
                break
            seen.append(cur)


def validate(doc: dict) -> list[Error]:
    errors: list[Error] = []
    tokens: dict[str, object] = {}
    types: dict[str, str | None] = {}
    collect(doc, [], None, tokens, types)
    # Second pass over $type. A token still lacking an own/inherited $type is an
    # error ONLY when it is not a pure alias: per DTCG 2025.10 a pure-alias token
    # takes its effective $type from the alias target (walking the chain via the
    # tokens map), so it is well-typed even inside an untyped group. Unresolved or
    # cyclic aliases are reported separately by check_aliases.
    for path, value in tokens.items():
        if types.get(path) is not None:
            continue
        if isinstance(value, str) and PURE_ALIAS_RE.match(value):
            continue
        errors.append(
            (path or '(root)', 'token has no $type and none inherited from a group')
        )
    check_aliases(tokens, errors)
    return errors


def _selftest() -> bool:
    good = {
        'color': {
            '$type': 'color',
            'base': {
                'blue': {'$value': {'colorSpace': 'srgb', 'components': [0.1, 0.2, 0.9]}}
            },
            'primary': {'$value': '{color.base.blue}'},
            'hover': {'$value': '{color.primary}'},
        },
        'space': {'$type': 'dimension', 'md': {'$value': {'value': 16, 'unit': 'px'}}},
        # Untyped group whose token is typed SOLELY via an alias to a typed
        # primitive living in a separate group (a valid semantic-layer pattern).
        'brand': {'accent': {'$value': '{color.base.blue}'}},
    }
    bad = {
        'orphan': {'$value': '#ffffff'},  # no $type, none inherited
        'a': {'$type': 'color', 'x': {'$value': '{a.missing}'}},  # unresolved alias
        'loop': {  # circular alias
            '$type': 'color',
            'p': {'$value': '{loop.q}'},
            'q': {'$value': '{loop.p}'},
        },
    }
    # Round-trip through a tempfile to exercise the real file-loading path.
    with tempfile.TemporaryDirectory() as tmp:
        gp, bp = Path(tmp) / 'good.json', Path(tmp) / 'bad.json'
        gp.write_text(json.dumps(good))
        bp.write_text(json.dumps(bad))
        good_errs = validate(json.loads(gp.read_text()))
        bad_errs = validate(json.loads(bp.read_text()))

    assert good_errs == [], good_errs
    assert any('no $type' in m for _, m in bad_errs), bad_errs
    assert any('does not resolve' in m for _, m in bad_errs), bad_errs
    assert any('circular alias' in m for _, m in bad_errs), bad_errs
    print('OK')
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tokens', help='path to a DTCG tokens JSON file')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1
    if not args.tokens:
        ap.error('pass --tokens FILE')

    doc = json.loads(Path(args.tokens).read_text())
    errors = validate(doc)
    for path, msg in errors:
        print(f'ERROR  {path}  {msg}')
    print(f'\n{len(errors)} error(s).')
    print('VALID' if not errors else 'INVALID')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
