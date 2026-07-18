"""Bump every version field declared in .version-bump.json to a new value.

Note: a single global regex per file, not JSON-path-aware traversal —
the repo's declared targets are 1:1 with every "version" key that exists in
each file (metadata.version + all plugins[].version fully covers
marketplace.json; plugin.json has exactly one "version" key), so replacing
every match preserves formatting exactly and needs no JSON round-trip.
If a file ever needs a "version" key left untouched, switch to path-aware
parsing instead of widening this regex.

Usage: python -m scripts.bump_version 4.1.0
"""

import argparse
import json
import re
from pathlib import Path

VERSION_RE = re.compile(r'"version"\s*:\s*"\d+\.\d+\.\d+"')
SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / '.version-bump.json'


def main() -> None:
    parser = argparse.ArgumentParser(description='Bump versions in .version-bump.json')
    parser.add_argument('version', help='new semver version, e.g. 4.1.0')
    args = parser.parse_args()

    if not SEMVER_RE.match(args.version):
        raise SystemExit(f"error: '{args.version}' is not a plain semver (X.Y.Z)")

    if not CONFIG_PATH.exists():
        raise SystemExit(f'error: config not found: {CONFIG_PATH}')
    try:
        config = json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f'error: invalid JSON in {CONFIG_PATH}: {exc}') from exc
    try:
        files = sorted({target['file'] for target in config['targets']})
    except KeyError as exc:
        raise SystemExit(f'error: {CONFIG_PATH} missing "targets" key') from exc

    for rel_path in files:
        path = ROOT / rel_path
        if not path.exists():
            raise SystemExit(f'error: target file not found: {rel_path}')
        text = path.read_text()
        new_text, count = VERSION_RE.subn(f'"version": "{args.version}"', text)
        if count == 0:
            raise SystemExit(
                f'error: no "version" field matched in {rel_path} -- check '
                f'.version-bump.json targets and the field formatting in the file'
            )
        path.write_text(new_text)
        print(f'{rel_path}: updated {count} version field(s)')  # noqa: T201 -- CLI script, stdlib-only by design


if __name__ == '__main__':
    main()
