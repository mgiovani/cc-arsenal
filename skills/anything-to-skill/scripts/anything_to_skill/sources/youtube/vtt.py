import html
import re
from collections.abc import Iterator

_TIMING = re.compile(r'^(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})\s+-->\s+\S+', re.MULTILINE)
_INLINE_TAG = re.compile(r'<[^>]*>')
_PARAGRAPH_S = 30


def _seconds(h: str | None, m: str, s: str, ms: str) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(text: str) -> list[tuple[float, str]]:
    """(start_seconds, text) cues with rolling-caption duplicates removed.

    Auto-generated captions repeat the previous cue's last line as the first line of
    the next one (and add near-zero-length cues that only carry the repeat), so a line
    is kept only when the cue before it did not already show it.
    """
    cues: list[tuple[float, str]] = []
    previous: set[str] = set()
    for block in re.split(r'\n\n+', text.replace('\r\n', '\n')):
        match = _TIMING.search(block)
        if not match:
            continue
        start = _seconds(*match.groups())
        body = block[match.end() :].split('\n', 1)
        lines = [
            ' '.join(html.unescape(_INLINE_TAG.sub('', ln)).split())
            for ln in (body[1].split('\n') if len(body) > 1 else [])
        ]
        lines = [ln for ln in lines if ln]
        cues.extend((start, ln) for ln in lines if ln not in previous)
        previous = set(lines)
    return cues


def _mmss(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f'{hours}:{minutes:02d}:{secs:02d}' if hours else f'{minutes:02d}:{secs:02d}'


def _paragraphs(
    cues: list[tuple[float, str]], boundaries: list[float]
) -> Iterator[tuple[float, str]]:
    """Group cues into (start, text) paragraphs that never straddle a chapter start."""
    para: list[str] = []
    start = 0.0
    bounds = iter(sorted(boundaries))
    next_bound = next(bounds, None)
    for at, line in cues:
        crossed = next_bound is not None and at >= next_bound
        if para and (crossed or at - start >= _PARAGRAPH_S):
            yield start, ' '.join(para)
            para = []
        while next_bound is not None and at >= next_bound:
            next_bound = next(bounds, None)
        if not para:
            start = at
        para.append(line)
    if para:
        yield start, ' '.join(para)


def to_markdown(
    cues: list[tuple[float, str]],
    chapters: list[dict],
    title: str,
    frames: dict[float, str] | None = None,
) -> str:
    """Chapters become ## sections; every paragraph opens with a [mm:ss] anchor.

    frames maps a timestamp to an image path; each lands after the paragraph it falls in.
    """
    chapters = sorted(chapters, key=lambda c: c['start_time'])
    paragraphs = list(_paragraphs(cues, [c['start_time'] for c in chapters]))
    pending = sorted((frames or {}).items())
    out = [f'# {title}']
    queue = list(chapters)
    for i, (start, body) in enumerate(paragraphs):
        while queue and queue[0]['start_time'] <= start:
            chapter = queue.pop(0)
            out.append(f'## {chapter["title"]} [{_mmss(chapter["start_time"])}]')
        out.append(f'[{_mmss(start)}] {body}')
        end = paragraphs[i + 1][0] if i + 1 < len(paragraphs) else float('inf')
        while pending and pending[0][0] < end:
            at, path = pending.pop(0)
            out.append(f'![frame at {_mmss(at)}]({path})')
    return '\n\n'.join(out) + '\n'
