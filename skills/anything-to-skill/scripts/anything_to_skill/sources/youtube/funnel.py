"""Stages 2 and 3 of the video ranking funnel.

Stage 1 (run.rank) judges every listed title. Stage 2 reads the description, chapter titles and
tags of the best N1; stage 3 reads a few transcript excerpts of the best N2. Each stage asks Laya
the same two-option question as stage 1, so their scores blend directly. A stage that gets
throttled or errors stops where it is and the earlier stages' scores stand.
"""

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from anything_to_skill.sources.youtube import captions, listing, vtt
from anything_to_skill.sources.youtube.listing import YtDlpError

TITLE_CHARS = 70
DESCRIPTION_CHARS = 500
CHAPTERS_SHOWN = 12
TAGS_SHOWN = 8
WINDOW_CHARS = 1200  # ~300 tokens at the repo's chars/4 estimate
PAUSE_S = 1.0
BACKOFF_S = 30.0
_URL = re.compile(r'https?://\S+')


@dataclass
class Evidence:
    """What the funnel learned about one video. `vtt` is None when captions were never
    asked for and '' when the video has none; `info` is {} when its metadata was unreadable."""

    info: dict[str, Any] | None = None
    vtt: str | None = None
    meta: float | None = None
    text: float | None = None


def _title(entry: dict[str, Any]) -> str:
    return ' '.join(str(entry.get('title') or '').split())[:TITLE_CHARS]


class _ThrottledError(Exception):
    """yt-dlp was still throttled after a back-off: stop the stage."""


def describe(title: str, info: dict[str, Any]) -> str:
    """Judgeable text for a video: title, description head, chapter titles and tags."""
    description = ' '.join(_URL.sub('', info.get('description') or '').split())
    chapters = [c.get('title', '') for c in info.get('chapters') or []][:CHAPTERS_SHOWN]
    lines = [
        f'Video title: {title}',
        f'Description: {description[:DESCRIPTION_CHARS]}' if description else '',
        f'Chapters: {"; ".join(c for c in chapters if c)}' if chapters else '',
        f'Tags: {", ".join(info["tags"][:TAGS_SHOWN])}' if info.get('tags') else '',
    ]
    return '\n'.join(ln for ln in lines if ln)


def _excerpt(cues: list[tuple[float, str]], start: int) -> tuple[str, int]:
    words: list[str] = []
    size = 0
    i = start
    while i < len(cues) and size < WINDOW_CHARS:
        words.append(cues[i][1])
        size += len(cues[i][1]) + 1
        i += 1
    return ' '.join(words), i


def windows(
    cues: list[tuple[float, str]],
    chapters: list[dict[str, Any]],
    match: Callable[[str], int],
) -> list[str]:
    """Up to three ~300-token excerpts: the start, the middle, and the chapter that mentions the
    goal most (the three-quarter mark when no chapter does). Overlapping ones are dropped."""
    if not cues:
        return []
    third = len(cues) * 3 // 4
    best = max(chapters, key=lambda c: match(c.get('title', '')), default=None)
    if best and match(best.get('title', '')) > 0:
        begin = float(best.get('start_time') or 0)
        third = next((i for i, (t, _) in enumerate(cues) if t >= begin), third)
    out: list[str] = []
    reached = 0
    for start in sorted({0, len(cues) // 2, third}):
        if start < reached:
            continue
        text, reached = _excerpt(cues, start)
        out.append(text)
    return out


class Funnel:
    """Fetches the evidence for stages 2 and 3 and keeps it per video url."""

    def __init__(
        self,
        ranker: Any,
        match: Callable[[str], int],
        on_throttle: Callable[[YtDlpError, float], None],
        log: Callable[[str], None],
    ) -> None:
        self.ranker = ranker
        self.match = match
        self.on_throttle = on_throttle
        self.log = log
        self.evidence: dict[str, Evidence] = {}
        self.report: dict[str, Any] = {}

    def get(self, entry: dict[str, Any]) -> Evidence:
        return self.evidence.setdefault(entry['url'], Evidence())

    def merged(self, entry: dict[str, Any]) -> dict[str, Any]:
        """The entry with whatever metadata stage 2 found, for keyword matching."""
        return {**entry, **(self.get(entry).info or {})}

    def _polite(self, call: Callable[[], Any]) -> Any:
        """One yt-dlp call after a pause; a 429/403 is logged, waited out and retried once."""
        time.sleep(PAUSE_S)
        try:
            return call()
        except YtDlpError as exc:
            if not exc.throttled:
                raise
            self.on_throttle(exc, BACKOFF_S)
            time.sleep(BACKOFF_S)
        try:
            return call()
        except YtDlpError as exc:
            if not exc.throttled:
                raise
            self.on_throttle(exc, 0.0)
            raise _ThrottledError from exc

    def _info(self, entry: dict[str, Any]) -> dict[str, Any]:
        ev = self.get(entry)
        if ev.info is not None:
            return ev.info
        try:
            info = self._polite(lambda: listing.video_info(entry['url']))
        except (YtDlpError, ValueError):
            info = {}
        ev.info = info
        return info

    def _judge(self, stage: str, texts: list[str]) -> list[float] | None:
        try:
            return self.ranker.judge(texts)
        except Exception as exc:  # noqa: BLE001 - a model failure must not lose the earlier stages
            self.report.setdefault('errors', []).append(f'{stage}: {exc!r}')
            return None

    def read_metadata(self, entries: list[dict[str, Any]], picks: list[int]) -> None:
        """Stage 2: score the description and chapters of the entries at `picks`."""
        self.log(f'ranking stage 2: reading metadata of {len(picks)} videos')
        scored: list[int] = []
        try:
            for i in picks:
                if self._info(entries[i]):
                    scored.append(i)
        except _ThrottledError:
            self.report['throttled'] = 'meta'
        texts = [describe(_title(entries[i]), self._info(entries[i])) for i in scored]
        scores = self._judge('meta', texts) if texts else []
        for i, score in zip(scored, scores or [], strict=False):
            self.get(entries[i]).meta = score
        self.report['meta'] = {'asked': len(picks), 'scored': len(scores or [])}

    def read_transcripts(self, entries: list[dict[str, Any]], picks: list[int]) -> None:
        """Stage 3: score excerpts of the captions (never speech recognition) at `picks`."""
        self.log(f'ranking stage 3: reading captions of {len(picks)} videos')
        scored = 0
        try:
            for i in picks:
                scored += self._score_captions(entries[i])
        except _ThrottledError:
            self.report['throttled'] = 'transcripts'
        self.report['transcripts'] = {'asked': len(picks), 'scored': scored}

    def _score_captions(self, entry: dict[str, Any]) -> bool:
        ev = self.get(entry)
        info = self._info(entry)
        if ev.vtt is None:
            lang = info.get('language') or 'en'
            try:
                ev.vtt = self._polite(lambda: captions.read_captions(entry['url'], lang))
            except YtDlpError:
                return False
        cues = vtt.parse_vtt(ev.vtt or '')
        title = _title(entry)
        excerpts = windows(cues, info.get('chapters') or [], self.match)
        scores = (
            self._judge(
                'transcripts',
                [f'Video title: {title}\nTranscript excerpt: {w}' for w in excerpts],
            )
            if excerpts
            else None
        )
        if not scores:
            return False
        ev.text = sum(scores) / len(scores)
        return True
