import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any
from urllib.parse import urljoin, urlsplit

from anything_to_skill.core.ssrf import check_url
from anything_to_skill.sources.web.throttle import (
    THROTTLE_STATUSES,
    HostThrottle,
    RobotsCache,
    parse_retry_after,
)

ACCEPT = 'text/markdown, text/html;q=0.8'
MAX_HOPS = 8
RETRIES = 4
TIMEOUT_S = 30
MAX_PAGE_BYTES = 10_000_000
MAX_LIST_BYTES = 50_000_000  # sitemaps and llms.txt
MAX_ROBOTS_BYTES = 1_000_000

_session: Any = None
_session_loop: asyncio.AbstractEventLoop | None = None


class FetchError(Exception):
    """Network-level failure (DNS, TLS, timeout, too many redirects); worth a retry."""


class ResponseTooLargeError(FetchError):
    """The body passed the byte cap (counted after decompression, so a gzip bomb trips it too)."""


class RobotsDisallowedError(Exception):
    pass


@dataclass
class FetchResult:
    url: str
    status: int
    body: str = ''
    content_type: str = ''
    etag: str | None = None
    last_modified: str | None = None
    history: list[str] = field(default_factory=list)


def _get_session() -> Any:
    """One long-lived Chrome-impersonating session per event loop, so cookies persist per host."""
    global _session, _session_loop  # noqa: PLW0603
    loop = asyncio.get_running_loop()
    if _session is None or _session_loop is not loop:
        from curl_cffi.requests import AsyncSession  # noqa: PLC0415 - lazy heavy dep

        # retry=0: retries are the throttle's job (Retry-After aware), not the client's
        _session = AsyncSession(impersonate='chrome', retry=0, timeout=TIMEOUT_S)
        _session_loop = loop
    return _session


async def close_session() -> None:
    global _session, _session_loop
    if _session is not None:
        await _session.close()
    _session, _session_loop = None, None


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.netloc}'


def _headers(
    accept: str,
    referer: str | None,
    target: str,
    etag: str | None,
    last_modified: str | None,
) -> dict[str, str]:
    # Only these are added; UA, sec-ch-ua and Accept-Encoding stay as the impersonated Chrome sends them.
    headers = {'Accept': accept, 'Accept-Language': 'en-US,en;q=0.9'}
    if referer:
        headers['Referer'] = referer
        same = _origin(referer) == _origin(target)
        headers['Sec-Fetch-Site'] = 'same-origin' if same else 'cross-site'
    if etag:
        headers['If-None-Match'] = etag
    if last_modified:
        headers['If-Modified-Since'] = last_modified
    return headers


async def _check(url: str, allow_private: bool) -> None:
    if not allow_private:
        await asyncio.to_thread(check_url, url)


async def _read_body(resp: Any, max_bytes: int | None) -> str:
    limit = max_bytes or MAX_PAGE_BYTES
    chunks: list[bytes] = []
    size = 0
    try:
        async for chunk in resp.aiter_content():
            size += len(chunk)
            if size > limit:
                raise ResponseTooLargeError(f'body over {limit} bytes: {resp.url}')
            chunks.append(chunk)
    except ResponseTooLargeError:
        raise
    except Exception as exc:
        raise FetchError(f'{type(exc).__name__}: {exc}') from exc
    finally:
        await resp.aclose()
    return b''.join(chunks).decode(resp.charset or 'utf-8', errors='replace')


async def fetch(
    url: str,
    etag: str | None,
    last_modified: str | None,
    *,
    referer: str | None = None,
    allow_private: bool = False,
    throttle: HostThrottle | None = None,
    accept: str = ACCEPT,
    on_hop: Callable[[str], Awaitable[None]] | None = None,
    max_bytes: int | None = None,
) -> FetchResult:
    """Conditional GET through the shared curl_cffi session; 304 returns status 304 and no body.

    Redirects are followed by hand so every hop passes the SSRF check before it is
    requested. 429/503 responses are retried after the throttle's wait; the last
    response is returned when retries run out. `on_hop` vets each redirect target
    (robots.txt for a new origin). Raises SSRFError, HostBlockedError, FetchError
    (ResponseTooLargeError when the body passes `max_bytes`).
    """
    session = _get_session()
    throttle = throttle or HostThrottle(floor=0.0)
    history: list[str] = []
    current = url
    for _ in range(MAX_HOPS + 1):
        await _check(current, allow_private)
        if history and on_hop:
            await on_hop(current)
        host = urlsplit(current).netloc
        conditional = current == url
        hop_referer = referer if not history else history[-1]
        resp = None
        for _try in range(RETRIES):
            await throttle.acquire(host)
            try:
                resp = await session.get(
                    current,
                    headers=_headers(
                        accept,
                        hop_referer,
                        current,
                        etag if conditional else None,
                        last_modified if conditional else None,
                    ),
                    allow_redirects=False,
                    stream=True,
                )
            except Exception as exc:
                throttle.release(host, 0)
                raise FetchError(f'{type(exc).__name__}: {exc}') from exc
            retry_after = parse_retry_after(resp.headers.get('retry-after'))
            throttle.release(host, resp.status_code, retry_after)
            if resp.status_code not in THROTTLE_STATUSES:
                break
            await resp.aclose()
        assert resp is not None  # noqa: S101 - RETRIES >= 1
        location = resp.headers.get('location')
        if (
            HTTPStatus.MULTIPLE_CHOICES <= resp.status_code < HTTPStatus.BAD_REQUEST
            and resp.status_code != HTTPStatus.NOT_MODIFIED
            and location
        ):
            await resp.aclose()
            history.append(current)
            current = urljoin(current, location)
            continue
        body = (
            await _read_body(resp, max_bytes)
            if resp.status_code != HTTPStatus.NOT_MODIFIED
            else ''
        )
        return FetchResult(
            url=current,
            status=resp.status_code,
            body=body,
            content_type=resp.headers.get('content-type', ''),
            etag=resp.headers.get('etag'),
            last_modified=resp.headers.get('last-modified'),
            history=history,
        )
    raise FetchError(f'too many redirects from {url}')


@dataclass
class Net:
    """Fetch plus the politeness state every request shares: throttle, robots, SSRF policy."""

    throttle: HostThrottle
    robots: RobotsCache
    allow_private: bool = False
    _locks: dict[str, asyncio.Lock] = field(default_factory=dict)

    async def ensure_robots(self, origin: str) -> None:
        lock = self._locks.setdefault(origin, asyncio.Lock())
        async with lock:
            if self.robots.fresh(origin):
                return
            try:
                res = await fetch(
                    f'{origin}/robots.txt',
                    None,
                    None,
                    allow_private=self.allow_private,
                    throttle=self.throttle,
                    accept='text/plain, */*;q=0.5',
                    max_bytes=MAX_ROBOTS_BYTES,
                )
                self.robots.load(origin, res.status, res.body)
            except FetchError:
                self.robots.load(origin, None)
            delay = self.robots.crawl_delay(origin)
            if delay:
                self.throttle.set_crawl_delay(urlsplit(origin).netloc, delay)

    async def check(self, url: str) -> None:
        """Raise SSRFError unless the URL is fetchable under this run's SSRF policy."""
        await _check(url, self.allow_private)

    async def _gate(self, url: str) -> None:
        origin = _origin(url)
        await self.ensure_robots(origin)
        if not self.robots.allowed(origin, url):
            raise RobotsDisallowedError(url)

    async def get(
        self,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
        referer: str | None = None,
        max_bytes: int | None = None,
    ) -> FetchResult:
        """robots.txt-checked fetch; raises RobotsDisallowedError, SSRFError, HostBlockedError, FetchError."""
        await _check(url, self.allow_private)
        await self._gate(url)
        return await fetch(
            url,
            etag,
            last_modified,
            referer=referer,
            allow_private=self.allow_private,
            throttle=self.throttle,
            on_hop=self._gate,
            max_bytes=max_bytes,
        )
