#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Ingest local markdown/text files and folders (no heavy dependencies).

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.cli import run_source

if __name__ == '__main__':
    sys.exit(run_source('local', sys.argv[1:]))
