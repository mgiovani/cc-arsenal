import argparse
import asyncio
import re
import shutil
import time
from http import HTTPStatus
from urllib.parse import urlsplit

from anything_to_skill.core.models import RunSummary, Unit
from anything_to_skill.core.ssrf import SSRFError
from anything_to_skill.core.workspace import Ctx
from anything_to_skill.sources.web import browser
from anything_to_skill.sources.web.discover import (
    boost_linked,
    crawl_scope,
    discover,
    follow_links,
    rerank_pending,
)
from anything_to_skill.sources.web.extract import (
    is_blocked,
    is_js_shell,
    strip_host_boilerplate,
    to_markdown,
)
from anything_to_skill.sources.web.fetch import (
    FetchError,
    FetchResult,
    Net,
    ResponseTooLargeError,
    RobotsDisallowedError,
    close_session,
)
from anything_to_skill.sources.web.frontier import (
    LinkScorer,
    extract_links,
    make_scorer,
)
from anything_to_skill.sources.web.throttle import (
    HostBlockedError,
    HostThrottle,
    RobotsCache,
)

MAX_IDLE_WAIT_S = 60.0
_H1 = re.compile(r'^#\s+(.+)$', re.M)


def add_args(parser: argparse.ArgumentParser) -> None:
    """Add this source's flags; --slug/--base/--max-pages/--allow-private already exist."""
    parser.add_argument(
        '--brain',
        choices=['rules', 'laya'],
        default='rules',
        help='link scorer for the frontier; laya falls back to rules when unavailable',
    )
    parser.add_argument(
        '--discover-only',
        action='store_true',
        help='expand seeds into page units (for estimate) without fetching pages',
    )
    parser.add_argument('--workers', type=int, default=4, help='concurrent fetch tasks')
    parser.add_argument(
        '--min-delay',
        type=float,
        default=1.0,
        help='floor of the per-host delay in seconds (robots Crawl-delay wins when larger)',
    )
    parser.add_argument('--max-depth', type=int, default=4, help='BFS link depth limit')
    parser.add_argument(
        '--max-queue', type=int, default=5000, help='BFS pending-unit cap'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='never launch agent-browser; JS shells become needs_js',
    )


class _Crawl:
    def __init__(self, ctx: Ctx, args: argparse.Namespace) -> None:
        self.ctx = ctx
        self.args = args
        self.store = ctx.store
        self.summary = RunSummary()
        throttle = HostThrottle(self.store.log_throttle, floor=args.min_delay)
        self.net = Net(throttle, RobotsCache(), ctx.allow_private)
        self.dropped = ctx.dropped_ids()
        self.dropped_web = sum(
            u.source == 'web' and u.id in self.dropped
            for u in self.store.units(status='done')
        )
        self.claimed = 0
        self.busy = 0
        self.browser_lock = asyncio.Lock()
        self._scorers: dict[str, LinkScorer] = {}

    async def go(self) -> RunSummary:
        try:
            await self.expand_seeds()
            rerank_pending(self.ctx, self.args.brain)
            if not self.args.discover_only:
                if not self.args.no_browser and shutil.which(browser.BIN):
                    self.store.requeue('needs_js')
                await asyncio.gather(*(self.worker() for _ in range(self.args.workers)))
                strip_host_boilerplate(self.store)
        finally:
            await close_session()
        return self.summary

    def error(self, message: str) -> None:
        self.ctx.log(message)
        self.summary.note(message)

    async def expand_seeds(self) -> None:
        for seed in self.store.units(source='web', kind='seed', status='pending'):
            try:
                added = await discover(
                    self.ctx,
                    seed.uri,
                    seed.meta.get('scope'),
                    self.net,
                    self.args.brain,
                )
            except SSRFError as exc:
                self.finish_status(seed, 'skipped', f'ssrf: {exc}')
            except (FetchError, HostBlockedError) as exc:
                self.error(f'seed {seed.uri}: {exc}')
            else:
                self.ctx.log(f'seed {seed.uri}: {added} pages queued')

    def spent(self) -> int:
        return self.store.token_total(exclude=self.dropped)

    def stop(self) -> bool:
        limit = self.ctx.max_pages
        budget = self.ctx.token_budget
        return (limit is not None and self.claimed >= limit) or (
            budget is not None and self.spent() >= budget
        )

    def fits_budget(self) -> bool:
        """False when the next page, plus those in flight, would likely pass the token budget
        (each judged at the largest size so far: a small first page such as a landing page
        would otherwise let a whole wave of big ones through). With no page done yet there is
        no estimate, so a single probe page runs alone first."""
        budget = self.ctx.token_budget
        if budget is None:
            return True
        done = self.store.counts().get('web', {}).get('done', 0) - self.dropped_web
        if not done:
            return not self.busy
        largest = self.store.token_max('web', self.dropped)
        return self.spent() + (self.busy + 1) * largest <= budget

    async def worker(self) -> None:
        while not self.stop():
            if not self.fits_budget():
                if not self.busy:
                    return
                await asyncio.sleep(0.1)
                continue
            claimed = self.store.claim('web')
            if not claimed:
                due = self.store.next_due('web')
                wait = None if due is None else due - time.time()
                if self.busy == 0 and (wait is None or wait > MAX_IDLE_WAIT_S):
                    return
                await asyncio.sleep(
                    0.1 if self.busy else min(max(wait or 0.0, 0.05), 1.0)
                )
                continue
            self.claimed += 1
            self.busy += 1
            try:
                await self.process(claimed[0])
            except Exception as exc:  # noqa: BLE001 - a poison page must not abort the crawl
                self.retry(claimed[0], f'{type(exc).__name__}: {exc}')
            finally:
                self.busy -= 1

    def finish_status(self, unit: Unit, status: str, reason: str) -> None:
        self.store.mark(unit.id, status, reason)
        if hasattr(self.summary, status):
            setattr(self.summary, status, getattr(self.summary, status) + 1)

    def retry(self, unit: Unit, reason: str) -> None:
        if self.store.fail(unit.id, reason) == 'failed':
            self.summary.failed += 1
            self.error(f'{unit.uri}: {reason}')

    async def process(self, unit: Unit) -> None:
        referer = self.store.get(unit.parent).uri if unit.parent else None
        try:
            res = await self.net.get(unit.uri, unit.etag, unit.last_modified, referer)
        except SSRFError as exc:
            self.finish_status(unit, 'skipped', f'ssrf: {exc}')
        except RobotsDisallowedError:
            self.finish_status(unit, 'skipped', 'disallowed by robots.txt')
        except HostBlockedError:
            self.finish_status(unit, 'blocked', 'host circuit breaker open')
        except ResponseTooLargeError as exc:
            self.finish_status(unit, 'skipped', str(exc))
        except FetchError as exc:
            self.retry(unit, str(exc))
        else:
            await self.handle(unit, res)

    async def handle(self, unit: Unit, res: FetchResult) -> None:
        status = res.status
        if status == HTTPStatus.NOT_MODIFIED:
            self.store.not_modified(unit.id)
            self.summary.done += 1
        elif status in (404, 410):
            self.finish_status(unit, 'skipped', f'HTTP {status}')
        elif status == HTTPStatus.FORBIDDEN:
            await self.rendered(unit, res, f'HTTP {status}', 'blocked')
        elif status in (401, 451):
            self.finish_status(unit, 'blocked', f'HTTP {status}')
        elif status == HTTPStatus.OK:
            await self.content(unit, res)
        elif (
            status == HTTPStatus.TOO_MANY_REQUESTS
            or status >= HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            self.retry(unit, f'HTTP {status}')
        else:
            self.finish_status(unit, 'skipped', f'HTTP {status}')

    async def content(self, unit: Unit, res: FetchResult) -> None:
        ctype = res.content_type.lower()
        if 'markdown' in ctype or ctype.startswith('text/plain'):
            m = _H1.search(res.body)
            self.finish(unit, res, res.body, m.group(1).strip() if m else None)
        elif 'html' in ctype or not ctype:
            if is_blocked(res.body):
                await self.rendered(unit, res, 'challenge page', 'blocked')
            elif is_js_shell(res.body):
                await self.rendered(unit, res, 'javascript shell', 'needs_js')
            else:
                md, title = to_markdown(res.body, res.url)
                if not md:
                    self.finish_status(unit, 'skipped', 'no extractable content')
                    return
                self.follow(unit, res, title)
                self.finish(unit, res, md, title)
        else:
            self.finish_status(unit, 'skipped', f'unsupported content-type {ctype}')

    async def rendered(
        self, unit: Unit, res: FetchResult, reason: str, unavailable: str
    ) -> None:
        """agent-browser for a JS shell, a 403 or a challenge page; `unavailable` is the status
        when the browser cannot or may not produce the page.

        401 and 451 never come here, and a challenge the browser cannot pass stays blocked:
        we do not solve CAPTCHAs, logins or paywalls.
        """
        host = urlsplit(res.url).netloc
        state = self.net.throttle.host(host)
        if self.args.no_browser or state.tripped or state.dead:
            return self.finish_status(unit, unavailable, reason)
        async with self.browser_lock:
            try:
                await self.net.throttle.acquire(host)
            except HostBlockedError:  # went dead while this worker waited on the lock
                return self.finish_status(unit, unavailable, reason)
            rendered = None
            try:
                rendered = await asyncio.to_thread(browser.render, res.url)
            except browser.BrowserBlockedError:
                return self.finish_status(
                    unit, 'blocked', f'{reason}; blocked in browser'
                )
            finally:
                self.net.throttle.release(host, 200 if rendered else 0)
        if rendered is None or not await self.browsable(rendered[1]):
            return self.finish_status(unit, unavailable, reason)
        self.finish(unit, res, rendered[0], None)
        return None

    async def browsable(self, final_url: str) -> bool:
        """The page the browser ended on passes the same SSRF and robots gates as any fetch."""
        try:
            await self.net.check(final_url)
        except SSRFError:
            return False
        origin = f'{urlsplit(final_url).scheme}://{urlsplit(final_url).netloc}'
        return self.net.robots.allowed(origin, final_url)

    def finish(
        self, unit: Unit, res: FetchResult, markdown: str, title: str | None
    ) -> None:
        self.store.finish(
            unit.id,
            markdown,
            title=title,
            hint={'final_url': res.url} if res.url != unit.uri else None,
            meta={'content_type': res.content_type.split(';')[0].strip()},
            etag=res.etag,
            last_modified=res.last_modified,
        )
        self.summary.done += 1

    def scorer(self, scope: str) -> LinkScorer:
        if scope not in self._scorers:
            self._scorers[scope] = make_scorer(
                self.ctx.goal, self.args.brain, scope, self.ctx.log
            )
        return self._scorers[scope]

    def follow(self, unit: Unit, res: FetchResult, title: str | None) -> None:
        """Feed the BFS frontier, or promote the listed pages this page links to."""
        found = crawl_scope(self.store, unit.uri)
        if found is None:
            return
        scope, mode = found
        links = extract_links(res.body, res.url)
        if mode == 'bfs':
            follow_links(
                self.ctx,
                unit.id,
                unit.depth,
                links,
                self.scorer(scope),
                scope,
                title or '',
                max_depth=self.args.max_depth,
                max_queue=self.args.max_queue,
            )
        else:
            boost_linked(self.ctx, unit, title or '', links, scope)


def run(ctx: Ctx, args: argparse.Namespace) -> RunSummary:
    return asyncio.run(_Crawl(ctx, args).go())
