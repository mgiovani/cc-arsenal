#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "yt-dlp[default]",
#   "pillow",
#   "imagehash",
#   "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""Transcribe YouTube videos that have no captions.

Thin entry point: the logic lives in the anything_to_skill package next to this file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anything_to_skill.cli import run_source

if __name__ == '__main__':
    sys.exit(run_source('youtube', [*sys.argv[1:], '--asr']))
