import re
import tempfile
from pathlib import Path

from anything_to_skill.sources.youtube.listing import YtDlpError, ytdlp

CAPTIONS_STATUS = 429
_LANG = re.compile(r'[A-Za-z]{2,3}')
CAPTIONS_429 = 'rate limited by YouTube (HTTP 429) fetching captions'
# Modest pauses: YouTube throttles the subtitle endpoint per IP, and bursts trip it.
SLEEP_S = '2'


class CaptionsThrottledError(YtDlpError):
    """The subtitle endpoint answered 429; audio download (ASR) is a separate endpoint."""

    def __init__(self) -> None:
        super().__init__(f'{CAPTIONS_429}: retry later', status=CAPTIONS_STATUS)


def fetch_captions(url: str, workdir: Path, lang: str = 'en') -> Path | None:
    """Download VTT (manual first, then auto); None means the video needs ASR."""
    # yt-dlp matches --sub-langs exactly and keys tracks by primary tag ('en'), while
    # videos report 'en-US'.
    lang = lang.split('-')[0]
    # the tag reaches yt-dlp as a regex, so an uploader-chosen value must be a plain code
    if not _LANG.fullmatch(lang):
        lang = 'en'
    try:
        # With both flags yt-dlp lets a manual track override the auto one for the same language.
        proc = ytdlp(
            [
                '--skip-download',
                '--no-playlist',
                '--write-subs',
                '--write-auto-subs',
                '--sub-langs',
                lang,
                '--sub-format',
                'vtt',
                '--sleep-subtitles',
                SLEEP_S,
                '--sleep-requests',
                SLEEP_S,
                '-o',
                str(workdir / '%(id)s.%(ext)s'),
            ],
            url,
        )
    except YtDlpError as exc:
        # yt-dlp exits non-zero when the subtitle request is throttled
        if exc.status == CAPTIONS_STATUS:
            raise CaptionsThrottledError from exc
        raise
    found = sorted(workdir.glob('*.vtt'))
    if found:
        return found[0]
    # yt-dlp exits 0 when only the subtitle request was throttled; ASR would hide that.
    if 'HTTP Error 429' in proc.stderr:
        raise CaptionsThrottledError
    return None


def read_captions(url: str, lang: str = 'en') -> str:
    """The VTT text of a video's manual or auto captions, or '' when it has none."""
    with tempfile.TemporaryDirectory() as tmp:
        path = fetch_captions(url, Path(tmp), lang)
        return path.read_text('utf-8', errors='replace') if path else ''
