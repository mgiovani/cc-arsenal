#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "laya",
# ]
# ///
"""`a2s.py verify --laya` (or, with --compact, `a2s.py compact-verify --laya`) with the Laya model installed.

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.cli import run_command
from anything_to_skill.compact import verify as compact_verify
from anything_to_skill.emit import verify


def main(argv: list[str]) -> int:
    compact = '--compact' in argv
    argv = [a for a in argv if a != '--compact'] + ['--laya']
    module = compact_verify if compact else verify
    return run_command(
        'compact-verify' if compact else 'verify', argv, module.add_args, module.run
    )


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
