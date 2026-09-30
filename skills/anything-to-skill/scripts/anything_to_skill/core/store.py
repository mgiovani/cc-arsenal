import hashlib
import json
import sqlite3
import threading
import time
from collections.abc import Collection
from pathlib import Path
from typing import Any

from anything_to_skill.core import tokens
from anything_to_skill.core.models import STATUSES, Unit
from anything_to_skill.core.sanitize import clean, strip_invisible

LEASE_S = 600
MAX_ATTEMPTS = 4
BACKOFF_BASE_S = 30
BACKOFF_CAP_S = 3600
USER_DROPS_KEY = 'dropped_units'

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    uri TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL DEFAULT 'page',
    parent INTEGER,
    depth INTEGER NOT NULL DEFAULT 0,
    priority REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_at REAL NOT NULL DEFAULT 0,
    etag TEXT,
    last_modified TEXT,
    sha TEXT,
    md_path TEXT,
    title TEXT,
    tokens INTEGER NOT NULL DEFAULT 0,
    hint TEXT NOT NULL DEFAULT '{}',
    meta TEXT NOT NULL DEFAULT '{}',
    error TEXT,
    updated REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS unit_status_next ON unit (status, next_at);
CREATE INDEX IF NOT EXISTS unit_claim ON unit (status, source, priority DESC, id);
CREATE TABLE IF NOT EXISTS throttle_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    host TEXT NOT NULL,
    event TEXT NOT NULL,
    status INTEGER,
    wait REAL NOT NULL DEFAULT 0,
    detail TEXT
);
"""


def backoff(attempts: int) -> float:
    """Seconds to wait after the given number of failed attempts (exponential, capped)."""
    return min(BACKOFF_CAP_S, BACKOFF_BASE_S * 2 ** max(0, attempts - 1))


class Store:
    """SQLite-backed unit queue. One process writes; a lock serialises its threads."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.md_dir = self.root / 'md'
        self.md_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(
            self.root / 'state.db', isolation_level=None, check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.execute('PRAGMA synchronous=NORMAL')
        self._db.execute('PRAGMA busy_timeout=5000')
        self._db.executescript(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> 'Store':
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _run(self, sql: str, params: dict[str, Any] | tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(sql, params).fetchall()

    def set_meta(self, key: str, value: Any) -> None:
        self._run(
            'INSERT INTO meta(k, v) VALUES (?, ?) '
            'ON CONFLICT(k) DO UPDATE SET v = excluded.v',
            (key, json.dumps(value)),
        )

    def get_meta(self, key: str, default: Any = None) -> Any:
        rows = self._run('SELECT v FROM meta WHERE k = ?', (key,))
        return json.loads(rows[0]['v']) if rows else default

    def user_drops(self) -> set[int]:
        """Unit ids dropped with `a2s drop`; the plan never keeps them, so nothing fetches them."""
        return {int(k) for k in self.get_meta(USER_DROPS_KEY, {})}

    def all_meta(self) -> dict[str, Any]:
        return {r['k']: json.loads(r['v']) for r in self._run('SELECT k, v FROM meta')}

    def add_unit(
        self,
        source: str,
        uri: str,
        kind: str = 'page',
        parent: int | None = None,
        depth: int = 0,
        priority: float = 0.0,
        hint: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> int:
        """Insert a pending unit, or return the existing unit's id when uri is known."""
        rows = self._run(
            'INSERT INTO unit(source, uri, kind, parent, depth, priority, hint, meta, updated) '
            'VALUES (:source, :uri, :kind, :parent, :depth, :priority, :hint, :meta, :now) '
            'ON CONFLICT(uri) DO NOTHING RETURNING id',
            {
                'source': source,
                'uri': uri,
                'kind': kind,
                'parent': parent,
                'depth': depth,
                'priority': priority,
                'hint': json.dumps(clean(hint or {})),
                'meta': json.dumps(clean(meta or {})),
                'now': time.time(),
            },
        )
        if rows:
            return rows[0]['id']
        return self._run('SELECT id FROM unit WHERE uri = ?', (uri,))[0]['id']

    def get(self, unit_id: int) -> Unit:
        rows = self._run('SELECT * FROM unit WHERE id = ?', (unit_id,))
        if not rows:
            raise KeyError(unit_id)
        return Unit.from_row(rows[0])

    def get_by_uri(self, uri: str) -> Unit | None:
        rows = self._run('SELECT * FROM unit WHERE uri = ?', (uri,))
        return Unit.from_row(rows[0]) if rows else None

    def units(
        self,
        source: str | None = None,
        status: str | None = None,
        kind: str | None = None,
    ) -> list[Unit]:
        rows = self._run(
            'SELECT * FROM unit WHERE (:source IS NULL OR source = :source) '
            'AND (:status IS NULL OR status = :status) '
            'AND (:kind IS NULL OR kind = :kind) ORDER BY id',
            {'source': source, 'status': status, 'kind': kind},
        )
        return [Unit.from_row(r) for r in rows]

    def claim(
        self,
        source: str | None = None,
        status: str = 'pending',
        limit: int = 1,
        now: float | None = None,
    ) -> list[Unit]:
        """Atomically lease up to limit due units, best priority first.

        The lease pushes next_at out by LEASE_S, so a crashed run's claims become
        claimable again on their own and nothing needs a separate in-progress status.
        """
        now = time.time() if now is None else now
        rows = self._run(
            'UPDATE unit SET attempts = attempts + 1, next_at = :lease, updated = :now '
            'WHERE id IN (SELECT id FROM unit WHERE status = :status AND next_at <= :now '
            'AND (:source IS NULL OR source = :source) '
            'AND id NOT IN (SELECT value FROM json_each(:dropped)) '
            'ORDER BY priority DESC, id LIMIT :limit) RETURNING *',
            {
                'lease': now + LEASE_S,
                'now': now,
                'status': status,
                'source': source,
                'limit': limit,
                'dropped': json.dumps(sorted(self.user_drops())),
            },
        )
        units = [Unit.from_row(r) for r in rows]
        units.sort(key=lambda u: (-u.priority, u.id))
        return units

    def next_due(
        self, source: str | None = None, status: str = 'pending'
    ) -> float | None:
        """Earliest next_at among not-yet-final units, so a runner can sleep instead of exit."""
        rows = self._run(
            'SELECT MIN(next_at) AS t FROM unit WHERE status = :status '
            'AND (:source IS NULL OR source = :source) '
            'AND id NOT IN (SELECT value FROM json_each(:dropped))',
            {
                'status': status,
                'source': source,
                'dropped': json.dumps(sorted(self.user_drops())),
            },
        )
        return rows[0]['t']

    def finish(
        self,
        unit_id: int,
        markdown: str,
        title: str | None = None,
        hint: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> Unit:
        """Single persistence point for content: sanitize, count, hash, write md, mark done.

        hint and meta merge into what the unit already carries; title, etag and
        last_modified keep their old value when not given.
        """
        current = self.get(unit_id)
        text = strip_invisible(markdown)
        rel = f'md/{unit_id}.md'
        target = self.root / rel
        tmp = target.with_suffix('.md.tmp')
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(target)
        self._run(
            "UPDATE unit SET status = 'done', error = NULL, sha = :sha, md_path = :md, "
            'title = COALESCE(:title, title), tokens = :tokens, hint = :hint, meta = :meta, '
            'etag = COALESCE(:etag, etag), last_modified = COALESCE(:lm, last_modified), '
            'updated = :now WHERE id = :id',
            {
                'sha': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'md': rel,
                'title': clean(title),
                'tokens': tokens.count(text),
                'hint': json.dumps({**current.hint, **clean(hint or {})}),
                'meta': json.dumps({**current.meta, **clean(meta or {})}),
                'etag': etag,
                'lm': last_modified,
                'now': time.time(),
                'id': unit_id,
            },
        )
        return self.get(unit_id)

    def not_modified(self, unit_id: int) -> None:
        """A 304: the stored markdown is still current, so the unit is done again."""
        self._run(
            "UPDATE unit SET status = 'done', error = NULL, updated = ? WHERE id = ?",
            (time.time(), unit_id),
        )

    def fail(
        self,
        unit_id: int,
        error: str,
        max_attempts: int = MAX_ATTEMPTS,
        now: float | None = None,
    ) -> str:
        """Record a failed attempt: retry with backoff, or give up as 'failed'.

        The unit keeps its current status while retrying (so a needs_asr unit stays
        needs_asr); claim() already counted this attempt.
        """
        now = time.time() if now is None else now
        attempts = self.get(unit_id).attempts
        if attempts >= max_attempts:
            self._run(
                "UPDATE unit SET status = 'failed', error = ?, updated = ? WHERE id = ?",
                (error, now, unit_id),
            )
            return 'failed'
        self._run(
            'UPDATE unit SET error = ?, next_at = ?, updated = ? WHERE id = ?',
            (error, now + backoff(attempts), now, unit_id),
        )
        return self.get(unit_id).status

    def mark(self, unit_id: int, status: str, error: str | None = None) -> None:
        """Move a unit to a non-retrying status and reset its retry budget."""
        if status not in STATUSES:
            raise ValueError(f'unknown status: {status}')
        self._run(
            'UPDATE unit SET status = ?, error = ?, attempts = 0, next_at = 0, updated = ? '
            'WHERE id = ?',
            (status, error, time.time(), unit_id),
        )

    def requeue(self, *statuses: str) -> int:
        """Put units in the given statuses back to pending with a fresh retry budget."""
        marks = ','.join('?' * len(statuses))
        rows = self._run(
            f"UPDATE unit SET status = 'pending', attempts = 0, next_at = 0 "  # noqa: S608
            f'WHERE status IN ({marks}) RETURNING id',  # placeholders only, values bound
            statuses,
        )
        return len(rows)

    def set_priority(self, unit_id: int, priority: float) -> None:
        self._run('UPDATE unit SET priority = ? WHERE id = ?', (priority, unit_id))

    def set_hint(self, unit_id: int, hint: dict[str, Any]) -> None:
        self._run(
            'UPDATE unit SET hint = ? WHERE id = ?', (json.dumps(clean(hint)), unit_id)
        )

    def set_kind(self, unit_id: int, kind: str) -> None:
        self._run('UPDATE unit SET kind = ? WHERE id = ?', (kind, unit_id))

    def read_markdown(self, unit_id: int) -> str:
        return (self.root / f'md/{unit_id}.md').read_text(encoding='utf-8')

    def counts(self) -> dict[str, dict[str, int]]:
        """source -> status -> number of units."""
        out: dict[str, dict[str, int]] = {}
        for r in self._run(
            'SELECT source, status, COUNT(*) AS n FROM unit GROUP BY 1, 2'
        ):
            out.setdefault(r['source'], {})[r['status']] = r['n']
        return out

    def token_total(
        self, source: str | None = None, exclude: Collection[int] = ()
    ) -> int:
        rows = self._run(
            "SELECT COALESCE(SUM(tokens), 0) AS t FROM unit WHERE status = 'done' "
            'AND (:source IS NULL OR source = :source) '
            'AND id NOT IN (SELECT value FROM json_each(:dropped))',
            {'source': source, 'dropped': json.dumps(sorted(exclude))},
        )
        return rows[0]['t']

    def log_throttle(
        self,
        host: str,
        event: str,
        status: int | None = None,
        wait: float = 0.0,
        detail: str | None = None,
    ) -> None:
        self._run(
            'INSERT INTO throttle_event(ts, host, event, status, wait, detail) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (time.time(), host, event, status, wait, detail),
        )

    def throttle_counts(self) -> dict[str, dict[str, int]]:
        """Event totals per host over the whole log, not just the recent tail."""
        counts: dict[str, dict[str, int]] = {}
        for r in self._run(
            'SELECT host, event, COUNT(*) AS n FROM throttle_event GROUP BY host, event'
        ):
            counts.setdefault(r['host'], {})[r['event']] = r['n']
        return counts

    def throttle_events(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._run(
            'SELECT * FROM throttle_event ORDER BY id DESC LIMIT ?', (limit,)
        )
        return [dict(r) for r in reversed(rows)]
