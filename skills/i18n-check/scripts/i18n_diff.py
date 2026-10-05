#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Diff locale files against a default locale: missing, untranslated, orphan keys.

Usage: i18n_diff.py DEFAULT_FILE OTHER_FILE [OTHER_FILE ...]

Reads JSON (nested or flat) and YAML. A YAML file with a single top-level
mapping (Rails: `en: {...}`) is unwrapped so its keys line up across locales.
Exit 1 if any key is missing or a locale file cannot be read.
"""

# ruff: noqa: T201 -- CLI script, stdout is the interface
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MIN_ARGS = 2
INVARIANT_RE = re.compile(
    r"""^(
        \s* | [\d\s.,:%+\-/]+ | (https?://|mailto:)\S+
        | (\s*(\{\{?[^{}]*\}?\}|%\{\w+\}|%\d*\$?[sdif]|:\w+|\$\{[^}]*\})\s*)+
    )$""",
    re.VERBOSE,
)


def load(path: Path) -> object:
    text = path.read_text(encoding='utf-8')
    if path.suffix in {'.yml', '.yaml'}:
        import yaml  # noqa: PLC0415 -- JSON-only runs need no PyYAML

        data = yaml.safe_load(text)
        if isinstance(data, dict) and len(data) == 1:
            (only,) = data.values()
            if isinstance(only, dict):
                return only
        return data
    return json.loads(text)


def flatten(node: object, prefix: str = '') -> dict[str, object]:
    if isinstance(node, dict):
        items = node.items()
    elif isinstance(node, list):
        items = enumerate(node)
    else:
        return {prefix: node}
    out: dict[str, object] = {}
    for key, value in items:
        out.update(flatten(value, f'{prefix}.{key}' if prefix else str(key)))
    return out


def is_invariant(value: object) -> bool:
    return not isinstance(value, str) or bool(INVARIANT_RE.match(value))


def diff(base: dict[str, object], other: dict[str, object]) -> dict[str, list[str]]:
    shared = [k for k in base if k in other and base[k] == other[k]]
    return {
        'missing': sorted(set(base) - set(other)),
        'untranslated': sorted(k for k in shared if not is_invariant(base[k])),
        'invariant': sorted(k for k in shared if is_invariant(base[k])),
        'orphan': sorted(set(other) - set(base)),
    }


def main(argv: list[str]) -> int:
    if len(argv) < MIN_ARGS:
        print(__doc__, file=sys.stderr)
        return 2
    base = flatten(load(Path(argv[0])))
    failed = False
    for name in argv[1:]:
        print(f'## {name} (default: {argv[0]})')
        try:
            result = diff(base, flatten(load(Path(name))))
        except (OSError, ValueError) as err:
            print(f'  locale file not readable: {err}\n')
            failed = True
            continue
        labels = {
            'missing': 'Missing',
            'untranslated': 'Untranslated (identical to default)',
            'invariant': 'Identical but likely fine (numbers, URLs, placeholders)',
            'orphan': 'Orphan (not in default)',
        }
        if not any(result[k] for k in ('missing', 'untranslated', 'orphan')):
            print('  no gaps')
        for kind, label in labels.items():
            if result[kind]:
                print(f'  {label} ({len(result[kind])}):')
                for key in result[kind]:
                    print(f'    - {key}')
        print()
        failed |= bool(result['missing'])
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
