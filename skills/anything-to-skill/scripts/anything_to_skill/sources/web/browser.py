import json
import re
import shutil
import subprocess
import uuid
from urllib.parse import urlsplit

from curl_cffi.requests.impersonate import DEFAULT_CHROME

from anything_to_skill.sources.web.extract import is_blocked

BIN = 'agent-browser'
MIN_CHARS = 200
STEP_TIMEOUT_S = 60
VIEWPORT = ('1440', '900')
STEALTH_ARGS = '--disable-blink-features=AutomationControlled'
FALLBACK_CHROME_MAJOR = '150'


class BrowserBlockedError(Exception):
    """The rendered page is a challenge/denial page, not content."""


def chrome_major() -> str:
    """Chrome major that curl_cffi impersonates, so the browser and the fetcher present one identity."""
    m = re.search(r'\d+', str(DEFAULT_CHROME))
    return m.group() if m else FALLBACK_CHROME_MAJOR


def user_agent() -> str:
    return (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        f'(KHTML, like Gecko) Chrome/{chrome_major()}.0.0.0 Safari/537.36'
    )


def _run(args: list[str]) -> str | None:
    try:
        done = subprocess.run(
            [BIN, *args],
            capture_output=True,
            text=True,
            timeout=STEP_TIMEOUT_S,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    return done.stdout if done.returncode == 0 else None


def _usable(text: str | None) -> str | None:
    """Text worth keeping; raises BrowserBlockedError on a challenge page."""
    if not text:
        return None
    if is_blocked(text):
        raise BrowserBlockedError
    text = text.strip()
    return text if len(text) >= MIN_CHARS else None


def _same_host(final: str, host: str) -> bool:
    return urlsplit(final).hostname == host


def _quick(url: str, host: str, pin: str) -> tuple[str, str] | None:
    """`agent-browser read <url>`: no browser launched; enough for many JS-heavy pages."""
    out = _run(['--allowed-domains', pin, 'read', url, '--json'])
    try:
        data = json.loads(out or '')['data']
        final, content = data['finalUrl'], data['content']
    except (ValueError, KeyError, TypeError):
        return None
    try:
        text = _usable(content)
    except BrowserBlockedError:
        return None
    return (text, final) if text and _same_host(final, host) else None


def _browse(url: str, host: str, pin: str, *, headed: bool) -> tuple[str, str] | None:
    session = ['--session', f'a2s-{uuid.uuid4().hex[:8]}']
    launch = [
        *session,
        '--allowed-domains',
        pin,
        '--user-agent',
        user_agent(),
        '--args',
        STEALTH_ARGS,
    ]
    if headed:
        launch.append('--headed')
    try:
        if _run([*launch, 'open', url]) is None:
            return None
        _run([*session, 'set', 'viewport', *VIEWPORT])
        _run([*session, 'wait', '--load', 'networkidle'])
        final = (_run([*session, 'get', 'url']) or '').strip()
        # a client-side redirect off the fetched host is never trusted, whatever it rendered
        if not _same_host(final, host):
            return None
        text = _usable(_run([*session, 'read']))
        return (text, final) if text else None
    finally:
        _run([*session, 'close'])


def render(url: str) -> tuple[str, str] | None:
    """(text, final URL) of a JavaScript-rendered page via agent-browser, else None.

    Tries a quick `read <url>`, then a headless browser, then (only if that was blocked) a
    headed retry. Every step is pinned to the page's own host with --allowed-domains, so
    redirects and subresources elsewhere are refused. Raises BrowserBlockedError when the
    page is still a bot challenge after the retry; a challenge is never solved.

    --profile is deliberately absent: agent-browser refuses --allowed-domains together
    with --profile (and with --user-data-dir), and the host pin is not negotiable.
    """
    host = urlsplit(url).hostname
    if not host or not shutil.which(BIN):
        return None
    pin = f'{host},*.{host}'
    if found := _quick(url, host, pin):
        return found
    try:
        return _browse(url, host, pin, headed=False)
    except BrowserBlockedError:
        found = _browse(url, host, pin, headed=True)
        if found is None:
            raise
        return found
