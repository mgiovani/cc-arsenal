"""Generic, safety-first file/JSON/window-selection utilities shared by every
collector: every path read anywhere in this package passes through here."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from optimize_ai_setup.constants import MAX_BYTES_PER_FILE

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

FMT_MILLION = 1_000_000
FMT_THOUSAND = 1_000
CHARS_PER_TOKEN = 4
MAX_FILES_PER_HARNESS = 2000


def fmt_num(value: float) -> str:
    value = float(value)
    if abs(value) >= FMT_MILLION:
        return f'{value / FMT_MILLION:.1f}M'
    if abs(value) >= FMT_THOUSAND:
        return f'{value / FMT_THOUSAND:.1f}K'
    return f'{value:.0f}'


def chars_to_tokens(chars: int) -> int:
    # ponytail: chars/4 token estimate, real tokenizer would be +/-20%
    return chars // CHARS_PER_TOKEN


def tokens_to_chars(tokens: float) -> int:
    return int(tokens) * CHARS_PER_TOKEN


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(pct * (len(ordered) - 1))))
    return ordered[idx]


def median(values: list[float]) -> float:
    return percentile(values, 0.5)


FORBIDDEN_EXACT_NAMES = {'auth.json', 'oauth_creds.json', 'google_accounts.json'}
FORBIDDEN_NAME_RE = re.compile(r'(cred|oauth|token)', re.IGNORECASE)


def is_forbidden_path(path: Path) -> bool:
    name = path.name
    if name in FORBIDDEN_EXACT_NAMES or name.endswith('.env'):
        return True
    return bool(name.endswith('.json') and FORBIDDEN_NAME_RE.search(name))


PLACEHOLDER_RE = re.compile(r'^\$\{[A-Za-z_][A-Za-z0-9_]*\}$')


def looks_like_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.match(value.strip()))


def compact_path(path: Path, home: Path) -> str:
    try:
        return f'~/{path.relative_to(home)}'
    except ValueError:
        return path.name


def read_json_checked(path: Path) -> tuple[dict, bool]:
    """Returns (data, ok). ok is False only when the file exists but could not
    be parsed as a JSON object, so callers can report it instead of silently
    looking empty (a top-level JSON array/string/number is just as unusable to
    every caller here, which all call .get()/.update() on the result)."""
    if is_forbidden_path(path) or not path.is_file():
        return {}, True
    try:
        data = json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}, False
    if not isinstance(data, dict):
        return {}, False
    return data, True


def read_json(path: Path) -> dict:
    return read_json_checked(path)[0]


def get_dict(source: object, key: str) -> dict:
    """Returns source[key] if source is a dict and that value is itself a
    dict, else {}. Guards the common `(x.get(k) or {})` chain, which still
    crashes on the next `.get()`/`.items()`/`.values()` when x isn't a dict
    (source is object, not dict) or x[k] is present but holds the wrong JSON
    type -- a str, list, or number where an object was expected."""
    if not isinstance(source, dict):
        return {}
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def mcp_server_names(config: dict) -> set[str]:
    return set(get_dict(config, 'mcpServers').keys())


def read_text_capped(path: Path, max_bytes: int) -> str:
    if is_forbidden_path(path):
        return ''
    try:
        with path.open(encoding='utf-8', errors='ignore') as fh:
            return fh.read(max_bytes)
    except OSError:
        return ''


@dataclass(frozen=True)
class WindowedFiles:
    paths: list[Path]
    total_in_window: int

    @property
    def sampled(self) -> bool:
        return len(self.paths) < self.total_in_window


def select_in_window(
    candidates: Iterable[Path], days: int, cap: int = MAX_FILES_PER_HARNESS
) -> WindowedFiles:
    cutoff = time.time() - days * 86400
    dated: list[tuple[float, Path]] = []
    for candidate in candidates:
        if is_forbidden_path(candidate):
            continue
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            dated.append((mtime, candidate))
    dated.sort(key=lambda pair: pair[0], reverse=True)
    return WindowedFiles([p for _, p in dated[:cap]], len(dated))


def iter_filtered_lines(
    path: Path, needles: tuple[str, ...], max_bytes: int = MAX_BYTES_PER_FILE
) -> Iterator[str]:
    if is_forbidden_path(path):
        return
    read = 0
    try:
        with path.open(encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                read += len(line)
                if read > max_bytes:
                    return
                if any(needle in line for needle in needles):
                    yield line
    except OSError:
        return


def find_git_root(start: Path) -> Path | None:
    current = start
    while True:
        if (current / '.git').exists():
            return current
        if current.parent == current:
            return None
        current = current.parent
