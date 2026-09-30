#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Workspace driver: init, detect, seed, drop, undrop, requeue, status, estimate, plan, brief, emit, verify, evals-freeze, compact-brief, compact-verify, compact.

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.cli import main

if __name__ == '__main__':
    sys.exit(main())
