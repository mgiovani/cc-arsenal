import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from http import HTTPStatus

from protego import Protego

ROBOTS_TTL_S = 86400
MAX_WAIT_S = 300.0
BLOCK_STATUSES = (429, 403)
THROTTLE_STATUSES = (429, 503)
# Statuses that say nothing about the host's mood (missing pages are normal in a crawl).
HEALTHY_ERRORS = (404, 410)

LogFn = Callable[..., None]


class HostBlockedError(Exception):
    """The circuit breaker gave up on this host: a probe after the cooldown was refused too."""


def parse_retry_after(value: str | None, now: float | None = None) -> float | None:
    """Retry-After as seconds, from either a delta-seconds or an HTTP-date value."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - (time.time() if now is None else now))


@dataclass
class _Host:
    limit: int
    inflight: int = 0
    ok_streak: int = 0
    next_ok: float = 0.0
    backoff_n: int = 0
    crawl_delay: float = 0.0
    blocks: int = 0
    open_until: float = 0.0
    tripped: bool = False
    probing: bool = False
    dead: bool = False


class HostThrottle:
    """Per-host politeness: AIMD concurrency, jittered delay, Retry-After, circuit breaker.

    `floor` is the minimum inter-request delay in seconds and also scales the
    backoff base, so one knob (--min-delay) slows or speeds everything together.
    Only events worth showing (backoff, breaker) go to `log`, not every request.
    """

    def __init__(
        self,
        log: LogFn | None = None,
        *,
        floor: float = 1.0,
        start: int = 2,
        ceiling: int = 4,
        grow_after: int = 8,
        breaker_after: int = 5,
        cooldown: float = 60.0,
        backoff_base: float | None = None,
        backoff_cap: float = MAX_WAIT_S,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._log = log or (lambda *_a, **_k: None)
        self.floor = floor
        self.start = start
        self.ceiling = ceiling
        self.grow_after = grow_after
        self.breaker_after = breaker_after
        self.cooldown = cooldown
        self.backoff_base = 5.0 * floor if backoff_base is None else backoff_base
        self.backoff_cap = backoff_cap
        self.clock = clock
        self.sleep = sleep
        self.rng = rng or random.Random()  # noqa: S311 - jitter, not security
        self._hosts: dict[str, _Host] = {}

    def host(self, name: str) -> _Host:
        return self._hosts.setdefault(name, _Host(limit=self.start))

    def set_crawl_delay(self, host: str, seconds: float) -> None:
        self.host(host).crawl_delay = seconds

    async def acquire(self, host: str) -> None:
        h = self.host(host)
        while True:
            if h.dead:
                raise HostBlockedError(host)
            now = self.clock()
            if h.inflight >= h.limit or (h.tripped and h.inflight):
                wait = 0.05
            else:
                wait = max(h.next_ok, h.open_until) - now
            if wait <= 0:
                break
            await self.sleep(wait)
        if h.tripped:
            h.probing = True
        h.inflight += 1
        gap = max(h.crawl_delay, self.floor) * self.rng.uniform(1, 2)
        h.next_ok = max(h.next_ok, now + gap)

    def release(self, host: str, status: int, retry_after: float | None = None) -> None:
        """Report a finished request; status 0 means a network error (neutral)."""
        h = self.host(host)
        h.inflight = max(0, h.inflight - 1)
        now = self.clock()
        if h.probing:
            self._probe_result(host, h, status)
        if status in THROTTLE_STATUSES:
            self._back_off(host, h, status, retry_after, now)
        elif 0 < status < HTTPStatus.BAD_REQUEST or status in HEALTHY_ERRORS:
            h.backoff_n = 0
            h.ok_streak += 1
            if h.ok_streak >= self.grow_after and h.limit < self.ceiling:
                h.limit += 1
                h.ok_streak = 0
        if status in BLOCK_STATUSES:
            h.blocks += 1
            if h.blocks >= self.breaker_after and not h.tripped:
                h.tripped = True
                h.open_until = now + self.cooldown
                self._log(
                    host, 'breaker_open', status, self.cooldown, f'{h.blocks} blocks'
                )
        elif status != 0 and not h.tripped:
            h.blocks = 0

    def _back_off(
        self, host: str, h: _Host, status: int, retry_after: float | None, now: float
    ) -> None:
        h.limit = max(1, h.limit // 2)
        h.ok_streak = 0
        h.backoff_n += 1
        jitter = self.rng.uniform(
            0, min(self.backoff_cap, self.backoff_base * 2**h.backoff_n)
        )
        wait = min(MAX_WAIT_S, max(retry_after or 0.0, jitter))
        h.next_ok = max(h.next_ok, now + wait)
        detail = f'retry-after={retry_after:g}s' if retry_after is not None else 'jitter'
        self._log(host, 'backoff', status, wait, f'{detail}; concurrency={h.limit}')

    def _probe_result(self, host: str, h: _Host, status: int) -> None:
        h.probing = False
        if status in BLOCK_STATUSES:
            h.dead = True
            self._log(host, 'host_skipped', status, 0.0, 'probe after cooldown refused')
        elif status != 0:
            h.tripped = False
            h.blocks = 0
            self._log(host, 'breaker_closed', status, 0.0, 'probe succeeded')


class RobotsCache:
    """robots.txt per origin, cached 24h.

    A 5xx or a network error means disallow all; any 4xx means no rules (RFC 9309).
    protego does the matching, so `*`/`$` wildcards and longest-match hold on every
    supported Python, unlike urllib's parser.
    """

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._entries: dict[str, tuple[float, Protego]] = {}

    def fresh(self, origin: str) -> bool:
        entry = self._entries.get(origin)
        return entry is not None and self._clock() - entry[0] < ROBOTS_TTL_S

    def load(self, origin: str, status: int | None, body: str = '') -> Protego:
        """Record a robots.txt fetch result; status None means the request failed."""
        if status == HTTPStatus.OK:
            rules = Protego.parse(body)
        elif status is None or status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            rules = Protego.parse('User-agent: *\nDisallow: /')
        else:
            rules = Protego.parse('')
        self._entries[origin] = (self._clock(), rules)
        return rules

    def allowed(self, origin: str, url: str) -> bool:
        entry = self._entries.get(origin)
        return entry is not None and entry[1].can_fetch(url, '*')

    def crawl_delay(self, origin: str) -> float | None:
        entry = self._entries.get(origin)
        delay = entry[1].crawl_delay('*') if entry else None
        return float(delay) if delay is not None else None

    def sitemaps(self, origin: str) -> list[str]:
        entry = self._entries.get(origin)
        return list(entry[1].sitemaps) if entry else []
