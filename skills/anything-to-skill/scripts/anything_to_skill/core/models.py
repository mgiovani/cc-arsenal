import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit

STATUSES = (
    'pending',
    'done',
    'skipped',
    'failed',
    'needs_asr',
    'needs_js',
    'needs_convert',
    'blocked',
)

# Corpus-token budget per effort tier; None means mirror everything.
EFFORT_BUDGET: dict[str, int | None] = {
    'quick': 50_000,
    'standard': 200_000,
    'complete': None,
}


_SECRET_KEY = re.compile(r'token|key|secret|pass|auth|sig|session|cred', re.IGNORECASE)


def source_label(uri: str, path_hint: object = None) -> str:
    """Provenance text safe to write into a shareable skill.

    Web URIs lose userinfo and credential-looking query values; local paths shrink to
    the relative path hint or the file name, so no absolute path or home directory leaks.
    """
    parts = urlsplit(uri)
    if parts.scheme in ('http', 'https'):
        host = parts.netloc.rpartition('@')[2]
        query = urlencode(
            [(k, v) for k, v in parse_qsl(parts.query) if not _SECRET_KEY.search(k)]
        )
        return parts._replace(netloc=host, query=query, fragment='').geturl()
    if isinstance(path_hint, str) and path_hint:
        return path_hint
    path = unquote(parts.path) if parts.scheme == 'file' else uri
    return PurePosixPath(path.replace('\\', '/')).name or 'source'


@dataclass
class Unit:
    id: int
    source: str
    uri: str
    kind: str = 'page'
    parent: int | None = None
    depth: int = 0
    priority: float = 0.0
    status: str = 'pending'
    attempts: int = 0
    next_at: float = 0.0
    etag: str | None = None
    last_modified: str | None = None
    sha: str | None = None
    md_path: str | None = None
    title: str | None = None
    tokens: int = 0
    hint: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    updated: float = 0.0

    def source_label(self) -> str:
        return source_label(self.uri, self.hint.get('path'))

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Unit':
        data = dict(row)
        data['hint'] = json.loads(data['hint'] or '{}')
        data['meta'] = json.loads(data['meta'] or '{}')
        return cls(**data)


MAX_ERRORS = 20


@dataclass
class RunSummary:
    done: int = 0
    skipped: int = 0
    failed: int = 0
    needs_asr: int = 0
    needs_js: int = 0
    needs_convert: int = 0
    blocked: int = 0
    errors: list[str] = field(default_factory=list)

    def note(self, message: str) -> None:
        """Record an error once, up to MAX_ERRORS, so a huge run cannot flood the summary."""
        if message not in self.errors and len(self.errors) < MAX_ERRORS:
            self.errors.append(message)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class Finding:
    """One scanner hit (scan/*, laya/factcheck.py); severity is 'hard' or 'warn'."""

    rule: str
    message: str
    line: int | None = None
    severity: str = 'warn'
