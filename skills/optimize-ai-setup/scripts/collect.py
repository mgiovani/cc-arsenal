#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Deterministic, stdlib-only evidence collector for the optimize-ai-setup skill.

Reads configs and session logs for every installed AI coding harness on this
machine and prints a compact, secret-free evidence report. No LLM reads raw
logs or configs directly: it only reads this report.

The actual checks live in the ``optimize_ai_setup`` package next to this
file; this is a thin entry point so ``npx skills add``-style copies of this
skill directory stay self-contained with no install step.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from optimize_ai_setup.cli import main

if __name__ == '__main__':
    sys.exit(main())
