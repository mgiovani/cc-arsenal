#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "laya",
# ]
# ///
"""Advisory local judge of a drafted structure, using the Laya model.

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.laya.judge import main

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
