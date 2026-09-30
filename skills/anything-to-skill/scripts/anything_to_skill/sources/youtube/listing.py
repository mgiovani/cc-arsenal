import importlib.util
import json
import re
import shutil
import subprocess
import sys
from typing import Any

MAX_LISTING = 500
# A bare channel URL is only its front page; the tabs hold the videos. Live streams and shorts
# are separate listings that a `/videos`-only fetch never sees (143 of 299 on one real channel).
CHANNEL_TABS = ('videos', 'streams', 'shorts')
# Modest pause between requests inside one yt-dlp run; YouTube throttles bursts per IP.
SLEEP_REQUESTS = '1'
_CHANNEL_ROOT = re.compile(
    r'^(https?://[^/]+/(?:@[^/]+|channel/[^/]+|c/[^/]+|user/[^/]+))/?$'
)
_HINTS = (
    (
        r'\bdeno\b|JavaScript runtime|\bEJS\b|n[- ]challenge',
        "yt-dlp could not run YouTube's JS challenge solver: install deno (https://deno.com) and update yt-dlp",
    ),
    (
        r'PO[ _-]?Token',
        'YouTube demands a PO token for this client: update yt-dlp or retry later',
    ),
    (
        r'not a bot',
        'YouTube flagged this IP as a bot: retry later or from another network',
    ),
    (r'HTTP Error 429', 'rate limited by YouTube (HTTP 429): retry later'),
    (r'HTTP Error 403', 'YouTube refused the download (HTTP 403): retry later'),
)
_THROTTLED = re.compile(r'HTTP Error (429|403)')
_PERMANENT = re.compile(
    r'Private video|Video unavailable|This video is unavailable|has been removed|'
    r'members-only|confirm your age|account associated with this video has been terminated',
    re.IGNORECASE,
)
_INFO_KEYS = (
    'id',
    'title',
    'description',
    'chapters',
    'tags',
    'upload_date',
    'duration',
    'channel',
    'uploader',
    'language',
    'webpage_url',
)


class YtDlpError(RuntimeError):
    """A yt-dlp failure with an actionable message; permanent ones are not worth retrying."""

    def __init__(
        self, message: str, *, permanent: bool = False, status: int | None = None
    ) -> None:
        super().__init__(message)
        self.permanent = permanent
        self.status = status  # 429 or 403: YouTube pushing back, worth a throttle event

    @property
    def throttled(self) -> bool:
        return self.status is not None


def explain(stderr: str) -> YtDlpError:
    lines = [ln.strip() for ln in stderr.splitlines() if ln.strip()]
    last = (lines[-1] if lines else 'yt-dlp failed')[:300]
    match = _THROTTLED.search(stderr)
    status = int(match.group(1)) if match else None
    for pattern, hint in _HINTS:
        if re.search(pattern, stderr, re.IGNORECASE):
            return YtDlpError(f'{hint} ({last})', status=status)
    return YtDlpError(last, permanent=bool(_PERMANENT.search(stderr)), status=status)


def _command() -> list[str]:
    # A module call finds the yt-dlp that `uv run --script` installed for this interpreter.
    if importlib.util.find_spec('yt_dlp'):
        return [sys.executable, '-m', 'yt_dlp']
    if path := shutil.which('yt-dlp'):
        return [path]
    raise YtDlpError('yt-dlp is not installed: run this through its uv shim')


def ytdlp(args: list[str], url: str, timeout: float = 180) -> subprocess.CompletedProcess:
    """Run yt-dlp; `--` keeps a hostile URL from being read as an option."""
    try:
        proc = subprocess.run(
            [*_command(), *args, '--', url],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise YtDlpError(f'yt-dlp timed out after {timeout:.0f}s') from exc
    if proc.returncode:
        raise explain(proc.stderr)
    return proc


def watch_url(entry: dict[str, Any]) -> str:
    if entry.get('id'):
        return f'https://www.youtube.com/watch?v={entry["id"]}'
    return entry.get('webpage_url') or entry.get('url') or ''


def _flatten(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue
        if entry.get('_type') == 'playlist' or 'entries' in entry:
            flat.extend(_flatten(entry.get('entries') or []))
        else:
            flat.append(entry)
    return flat


def _list_tab(url: str) -> list[dict[str, Any]]:
    proc = ytdlp(
        [
            '--flat-playlist',
            '--playlist-end',
            str(MAX_LISTING),
            '--sleep-requests',
            SLEEP_REQUESTS,
            '-J',
        ],
        url,
        timeout=300,
    )
    data = json.loads(proc.stdout)
    return _flatten(data['entries']) if 'entries' in data else [data]


def list_videos(url: str) -> list[dict[str, Any]]:
    """yt-dlp --flat-playlist -J entries for a video, playlist or channel URL.

    A bare channel lists every tab (videos, streams, shorts). A tab the channel lacks is
    skipped, but a throttled one raises so a partial listing is never silent, and so does a
    channel where no tab could be listed.
    """
    if match := _CHANNEL_ROOT.match(url):
        urls = [f'{match.group(1)}/{tab}' for tab in CHANNEL_TABS]
    else:
        urls = [url]
    entries: list[dict[str, Any]] = []
    failure: YtDlpError | None = None
    for tab_url in urls:
        try:
            entries += _list_tab(tab_url)
        except YtDlpError as exc:
            if exc.throttled:
                raise
            failure = failure or exc
    if failure and not entries:
        raise failure
    seen: set[str] = set()
    videos = []
    for entry in entries:
        link = watch_url(entry)
        if link and link not in seen:
            seen.add(link)
            videos.append({**entry, 'url': link})
    return videos


def video_info(url: str) -> dict[str, Any]:
    """yt-dlp -J for one video: chapters, description, upload date."""
    data = json.loads(
        ytdlp(['--no-playlist', '--sleep-requests', SLEEP_REQUESTS, '-J'], url).stdout
    )
    return {k: data[k] for k in _INFO_KEYS if data.get(k) is not None}
