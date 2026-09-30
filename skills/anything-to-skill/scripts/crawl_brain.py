#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "curl_cffi>=0.16",
#   "trafilatura>=2.0",
#   "defusedxml>=0.7.1",
#   "html-to-markdown>=3.0",
#   "protego>=0.4",
#   "laya",
# ]
# ///
"""ingest_web with the local Laya model ranking which links to follow.

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.cli import run_source

if __name__ == '__main__':
    sys.exit(run_source('web', [*sys.argv[1:], '--brain', 'laya']))
