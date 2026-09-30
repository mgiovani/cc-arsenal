import argparse
import contextlib
import importlib
import json
import re
import tempfile
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from anything_to_skill.core.models import RunSummary, Unit
from anything_to_skill.core.workspace import Ctx
from anything_to_skill.sources.youtube import asr, captions, frames, funnel, listing, vtt
from anything_to_skill.sources.youtube.captions import (
    CAPTIONS_429,
    CaptionsThrottledError,
)
from anything_to_skill.sources.youtube.listing import YtDlpError

NAME = 'youtube'
VIDEO_CAP = {'quick': 10, 'standard': 30, 'complete': 500}
BRAIN_WEIGHT = 0.7
KEYWORD_SATURATION = (
    3  # goal words in one title that already count as a full keyword match
)
UNJUDGED_LAYA = 0.5
# Later stages read more of the video, so they weigh more in the blended Laya score.
STAGE_WEIGHT = {'title': 1.0, 'meta': 2.0, 'text': 3.0}
# (videos whose metadata is read, videos whose captions are read) by effort.
FUNNEL_SIZES = {'quick': (15, 6), 'standard': (30, 12), 'complete': (60, 24)}
CACHE_DIR = 'yt-cache'
HOST = 'youtube.com'
CAPTIONS_429_LIMIT = 2
PRIORITY_SCALE = 10.0
SKIPPED_KEPT = 30
RANKING_KEY = 'youtube.ranking'
DESCRIPTION_CHARS = 1000
_STOPWORDS = {
    'the', 'and', 'for', 'with', 'from', 'that', 'this', 'about', 'how', 'use',
    'using', 'best', 'practices', 'guide', 'into', 'your', 'are',
    'core', 'work', 'works', 'concept', 'concepts', 'fundamentals', 'basics',
}  # fmt: skip
_WORD = re.compile(r'[a-z0-9][a-z0-9+#.]{2,}')
_ACRONYM = re.compile(r'\b[A-Z]{2}\b')
PLURAL_MIN_LEN = 4
_VIDEO_ID = re.compile(r'[\w-]{1,32}')
_TITLE_WORD = re.compile(r'(?<![#\w])[a-z0-9]{2,}')
DUPLICATE_JACCARD = 0.6
SHORT_SECONDS = 90
MIN_SHARED_WORDS = 2


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--asr',
        action='store_true',
        help='transcribe videos without captions instead of fetching (transcribe.py)',
    )
    parser.add_argument('--asr-model', help='whisper model name or repo')
    parser.add_argument(
        '--frames', action='store_true', help='also save deduplicated video stills'
    )
    parser.add_argument(
        '--brain',
        choices=['rules', 'laya'],
        default='rules',
        help='rank channel/playlist videos with Laya when there are more than the cap; '
        'falls back to keywords when unavailable',
    )
    parser.add_argument(
        '--max-videos',
        type=int,
        help='videos kept per playlist or channel (default by effort)',
    )
    parser.add_argument(
        '--rank-meta',
        type=int,
        metavar='N1',
        help='with --brain laya: rank the best N1 titles again on their description and '
        'chapters (default 15/30/60 by effort, 0 to skip)',
    )
    parser.add_argument(
        '--rank-transcripts',
        type=int,
        metavar='N2',
        help='with --brain laya: rank the best N2 again on caption excerpts, never ASR '
        '(default 6/12/24 by effort, 0 to skip)',
    )


def _keywords(goal: str) -> set[str]:
    # '.' stays inside a token (node.js) but a sentence-ending one is not part of the word.
    words = {w.rstrip('.') for w in _WORD.findall(goal.lower())} - _STOPWORDS
    # A plural goal word ("LLMs") must still hit its singular ("LLM").
    return {w[:-1] if len(w) >= PLURAL_MIN_LEN and w.endswith('s') else w for w in words}


def _matcher(goal: str) -> Callable[[str], int]:
    """Counts the goal's keywords a text mentions. Word-start match: "core" must not hit
    "hardcore". A two-letter acronym in the goal ("AI") must match as a whole word, or "air"
    would hit it."""
    patterns = [re.compile(rf'\b{re.escape(w)}') for w in _keywords(goal)]
    patterns += [re.compile(rf'\b{a.lower()}\b') for a in set(_ACRONYM.findall(goal))]
    return lambda text: sum(bool(p.search(text.lower())) for p in patterns)


def _title_words(entry: dict[str, Any]) -> frozenset[str]:
    return (
        frozenset(_TITLE_WORD.findall(str(entry.get('title') or '').lower())) - _STOPWORDS
    )


def _duration(entry: dict[str, Any]) -> float:
    value = entry.get('duration')
    return float(value) if isinstance(value, int | float) else 0.0


def near_duplicates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Same talk twice: title words overlap (Jaccard) or a Short repeats a longer video's topic."""
    wa, wb = _title_words(a), _title_words(b)
    shared = len(wa & wb)
    if not shared:
        return False
    if shared / len(wa | wb) >= DUPLICATE_JACCARD:
        return True
    short_first = 0 < min(_duration(a), _duration(b)) <= SHORT_SECONDS
    return short_first and shared >= MIN_SHARED_WORDS and (wa <= wb or wb <= wa)


def dedupe(entries: list[dict[str, Any]], order: list[int]) -> list[int]:
    """`order` with near-duplicates pushed behind the rest: the longer copy of a pair keeps the
    slot, and the next candidate takes the place of the copy that lost."""
    kept: list[int] = []
    losers: list[int] = []
    for i in order:
        twin = next((k for k in kept if near_duplicates(entries[i], entries[k])), None)
        if twin is None:
            kept.append(i)
        elif _duration(entries[i]) > _duration(entries[twin]):
            kept[kept.index(twin)] = i
            losers.append(twin)
        else:
            losers.append(i)
    return kept + losers


def keyword_hits(entries: list[dict[str, Any]], goal: str) -> list[int]:
    match = _matcher(goal)
    return [match(_searchable(e)) for e in entries]


def _searchable(entry: dict[str, Any]) -> str:
    chapters = ' '.join(c.get('title', '') for c in entry.get('chapters') or [])
    tags = ' '.join(entry.get('tags') or [])
    return f'{entry.get("title", "")} {entry.get("description", "")} {chapters} {tags}'


def select(
    entries: list[dict[str, Any]], goal: str, cap: int
) -> list[tuple[dict, float]]:
    """Keep goal-matching videos (best first), or the first `cap` when none match.

    A lone video is an explicit request, so it is never filtered.
    """
    if len(entries) == 1:
        return [(entries[0], 0)]
    scored = [
        (e, float(h)) for e, h in zip(entries, keyword_hits(entries, goal), strict=True)
    ]
    matched = sorted((pair for pair in scored if pair[1] > 0), key=lambda p: -p[1])
    ranked = matched or scored
    order = dedupe([e for e, _ in ranked], list(range(len(ranked))))
    return [ranked[i] for i in order[:cap]]


def _row(
    entry: dict[str, Any], score: float, laya: float, keywords: int, ev: Any
) -> dict:
    return {
        'id': entry.get('id'),
        'title': ' '.join(str(entry.get('title') or '').split())[:80],
        'score': round(score, 3),
        'laya': round(laya, 3),
        'meta': None if ev.meta is None else round(ev.meta, 3),
        'transcript': None if ev.text is None else round(ev.text, 3),
        'keywords': keywords,
    }


def blend(
    entries: list[dict[str, Any]],
    goal: str,
    title: list[float | None],
    fun: funnel.Funnel | None,
) -> tuple[list[float], list[float], list[int]]:
    """(blended score, Laya score, keyword hits) per entry.

    The Laya score is the mean of the stages that judged the video, later stages weighing more.
    A video no stage judged gets the neutral score, never 0, so the keyword share still orders it.
    """
    hits = keyword_hits([fun.merged(e) if fun else e for e in entries], goal)
    laya, blended = [], []
    for i, entry in enumerate(entries):
        ev = fun.get(entry) if fun else funnel.Evidence()
        parts = [
            (STAGE_WEIGHT[stage], score)
            for stage, score in (
                ('title', title[i]),
                ('meta', ev.meta),
                ('text', ev.text),
            )
            if score is not None
        ]
        weight = sum(w for w, _ in parts)
        value = sum(w * s for w, s in parts) / weight if weight else UNJUDGED_LAYA
        laya.append(value)
        blended.append(
            BRAIN_WEIGHT * value
            + (1 - BRAIN_WEIGHT) * min(1.0, hits[i] / KEYWORD_SATURATION)
        )
    return blended, laya, hits


def rank(
    entries: list[dict[str, Any]],
    goal: str,
    cap: int,
    ranker: Any,
    fun: funnel.Funnel | None = None,
    sizes: tuple[int, int] = (0, 0),
) -> tuple[list[tuple[dict, float]], dict[str, Any]]:
    """Best-first `cap` videos by Laya blended with the keyword score, plus the record of why.

    Stage 1 judges every title (for a large listing, a shortlist of the best keyword and
    embedding matches). With a funnel, the best `sizes[0]` are then re-judged on their
    description and chapters and the best `sizes[1]` of those on caption excerpts.
    """
    title, agreed = ranker.score(entries, keyword_hits(entries, goal))
    blended, laya, hits = blend(entries, goal, title, fun)
    order = sorted(range(len(entries)), key=lambda i: (-blended[i], i))
    if fun and sizes[0]:
        fun.read_metadata(entries, order[: sizes[0]])
        blended, laya, hits = blend(entries, goal, title, fun)
        order = sorted(range(len(entries)), key=lambda i: (-blended[i], i))
    if fun and sizes[1]:
        fun.read_transcripts(entries, order[: sizes[1]])
        blended, laya, hits = blend(entries, goal, title, fun)
        order = sorted(range(len(entries)), key=lambda i: (-blended[i], i))
    order = dedupe(entries, order)
    rows = [
        _row(
            entries[i],
            blended[i],
            UNJUDGED_LAYA if title[i] is None else title[i],
            hits[i],
            fun.get(entries[i]) if fun else funnel.Evidence(),
        )
        for i in order
    ]
    record = {
        'method': 'laya',
        'candidates': len(entries),
        'judged': sum(t is not None for t in title),
        'cap': cap,
        'top_orders_agree': all(agreed[i] for i in order[:cap] if title[i] is not None),
        'funnel': fun.report if fun else {},
        'chosen': rows[:cap],
        'skipped': rows[cap : cap + SKIPPED_KEPT],
        'skipped_total': max(0, len(rows) - cap),
    }
    return [(entries[i], blended[i]) for i in order[:cap]], record


def _make_ranker(ctx: Ctx, args: argparse.Namespace, summary: RunSummary) -> Any:
    """A Laya ranker, or None with one warning when Laya cannot load."""
    if args.brain != 'laya':
        return None
    try:
        brain = importlib.import_module('anything_to_skill.laya.brain')
        return brain.LayaVideoRanker(ctx.goal)
    except Exception as exc:  # noqa: BLE001 - laya is optional and heavy
        _warn(ctx, summary, f'--brain laya unavailable ({exc!r}); ranking by keywords')
        return None


def funnel_sizes(ctx: Ctx, args: argparse.Namespace) -> tuple[int, int]:
    quick, standard = FUNNEL_SIZES['quick'], FUNNEL_SIZES['standard']
    default = FUNNEL_SIZES.get(ctx.effort, standard if ctx.effort != 'quick' else quick)
    meta, text = (
        default[i] if (given := getattr(args, name, None)) is None else given
        for i, name in enumerate(('rank_meta', 'rank_transcripts'))
    )
    return max(0, meta), max(0, text)


def cache_path(ctx: Ctx, video_id: Any) -> Path | None:
    if not isinstance(video_id, str) or not _VIDEO_ID.fullmatch(video_id):
        return None
    return ctx.ws.dir / CACHE_DIR / f'{video_id}.json'


def _keep_evidence(
    ctx: Ctx, fun: funnel.Funnel, chosen: list[tuple[dict, float]]
) -> None:
    """Chosen videos keep the metadata and captions the funnel already downloaded, so ingest
    does not fetch them twice. Everything else the funnel read is dropped with it."""
    for entry, _ in chosen:
        ev = fun.get(entry)
        path = cache_path(ctx, entry.get('id'))
        if path and ev.info:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'info': ev.info, 'vtt': ev.vtt}), 'utf-8')


def choose(
    ctx: Ctx,
    args: argparse.Namespace,
    summary: RunSummary,
    seed: Unit,
    entries: list[dict[str, Any]],
    cap: int,
) -> list[tuple[dict, float]]:
    """Laya ranking when the listing exceeds the cap, keyword selection otherwise."""
    if len(entries) > cap and (ranker := _make_ranker(ctx, args, summary)):
        sizes = funnel_sizes(ctx, args)
        fun = funnel.Funnel(
            ranker,
            _matcher(ctx.goal),
            lambda exc, wait: _log_throttle(ctx, exc, wait),
            ctx.log,
        )
        try:
            chosen, record = rank(entries, ctx.goal, cap, ranker, fun, sizes)
        except Exception as exc:  # noqa: BLE001 - a broken model must not lose the run
            _warn(ctx, summary, f'laya ranking failed ({exc!r}); ranking by keywords')
        else:
            if throttled := fun.report.get('throttled'):
                _warn(
                    ctx,
                    summary,
                    f'ranking stage {throttled} throttled: kept the earlier stages',
                )
            _keep_evidence(ctx, fun, chosen)
            ranking = ctx.store.get_meta(RANKING_KEY, {})
            ranking[seed.uri] = record
            ctx.store.set_meta(RANKING_KEY, ranking)
            return [(e, round(score * PRIORITY_SCALE, 3)) for e, score in chosen]
    return select(entries, ctx.goal, cap)


def _warn(ctx: Ctx, summary: RunSummary, message: str) -> None:
    if message not in summary.errors:
        ctx.log(f'warning: {message}')
    summary.note(message)


def expand_seeds(ctx: Ctx, args: argparse.Namespace, summary: RunSummary) -> None:
    cap = args.max_videos or VIDEO_CAP.get(ctx.effort, VIDEO_CAP['standard'])
    if ctx.max_pages:
        cap = min(cap, ctx.max_pages)
    for seed in ctx.store.units(NAME, 'pending', 'seed'):
        try:
            entries = listing.list_videos(seed.uri)
        except YtDlpError as exc:
            _log_throttle(ctx, exc)
            ctx.store.mark(seed.id, 'failed', str(exc))
            summary.failed += 1
            summary.note(str(exc))
            continue
        for entry, score in choose(ctx, args, summary, seed, entries, cap):
            uri = entry['url']
            # Seeding a canonical watch URL would collide with the seed's own unique uri.
            if uri == seed.uri and entry.get('id'):
                uri = f'https://youtu.be/{entry["id"]}'
            ctx.store.add_unit(
                NAME,
                uri,
                kind='video',
                parent=seed.id,
                priority=float(score),
                meta={'video_id': entry.get('id'), 'title': entry.get('title')},
            )
        ctx.store.mark(seed.id, 'skipped')


def _log_throttle(ctx: Ctx, exc: YtDlpError, wait: float = 0.0) -> None:
    """Record a 429/403 so `status --json` shows it; yt-dlp never reaches the web throttle."""
    if exc.status:
        ctx.store.log_throttle(HOST, str(exc.status), exc.status, wait, str(exc)[:200])


def _fail(ctx: Ctx, unit: Unit, exc: YtDlpError, summary: RunSummary) -> None:
    summary.note(str(exc))
    if exc.permanent:
        ctx.store.mark(unit.id, 'skipped', str(exc))
        summary.skipped += 1
        return
    if ctx.store.fail(unit.id, str(exc)) == 'failed':
        summary.failed += 1
    _log_throttle(ctx, exc, max(0.0, ctx.store.get(unit.id).next_at - time.time()))


def _captions_throttled(
    ctx: Ctx, unit: Unit, exc: CaptionsThrottledError, summary: RunSummary
) -> None:
    """Retry once; a second consecutive subtitle 429 hands the video to ASR instead.

    ASR downloads audio, a different endpoint, so it can succeed while subtitles stay throttled.
    """
    if CAPTIONS_429 not in (unit.error or ''):
        _fail(ctx, unit, exc, summary)
        return
    ctx.store.mark(unit.id, 'needs_asr', str(exc))
    _log_throttle(ctx, exc)
    summary.note(
        f'captions throttled {CAPTIONS_429_LIMIT} times for {unit.uri}: '
        'moved to needs_asr, run transcribe.py',
    )


def _stills(
    ctx: Ctx,
    unit: Unit,
    info: dict[str, Any],
    cues: list[tuple[float, str]],
    summary: RunSummary,
) -> dict[float, str]:
    """Frame extraction is a bonus: any failure here must not lose the transcript."""
    stamps = frames.frame_timestamps(info.get('chapters') or [], cues)
    if not stamps:
        return {}
    video_id = info.get('id') or unit.meta.get('video_id') or unit.id
    try:
        paths = frames.extract_frames(
            unit.uri, stamps, ctx.ws.dir / 'frames', prefix=str(video_id)
        )
    except (YtDlpError, OSError, StopIteration) as exc:
        if isinstance(exc, YtDlpError):
            _log_throttle(ctx, exc)
        summary.note(f'frames skipped for {unit.uri}: {exc}')
        return {}
    return {float(frames.seconds_of(p)): f'assets/frames/{p.name}' for p in paths}


def _finish(
    ctx: Ctx,
    args: argparse.Namespace,
    unit: Unit,
    info: dict[str, Any],
    cues: list[tuple[float, str]],
    origin: str,
    summary: RunSummary,
) -> None:
    title = info.get('title') or unit.meta.get('title') or unit.uri
    chapters = info.get('chapters') or []
    shots = _stills(ctx, unit, info, cues, summary) if args.frames else {}
    channel = info.get('channel') or info.get('uploader')
    ctx.store.finish(
        unit.id,
        vtt.to_markdown(cues, chapters, title, shots),
        title=title,
        hint={
            'path': [channel] if channel else [],
            'headings': [c['title'] for c in chapters],
        },
        meta={
            'video_id': info.get('id'),
            'channel': channel,
            'upload_date': info.get('upload_date'),
            'duration': info.get('duration'),
            # plan/pack summarizes a chapterless video from its description
            'description': (info.get('description') or '')[:DESCRIPTION_CHARS],
            'text_from': origin,
            'frames': shots,
        },
    )
    summary.done += 1


def _read_cache(ctx: Ctx, unit: Unit) -> dict[str, Any]:
    path = cache_path(ctx, unit.meta.get('video_id'))
    try:
        return json.loads(path.read_text('utf-8')) if path else {}
    except (OSError, ValueError):
        return {}


def _drop_cache(ctx: Ctx, unit: Unit) -> None:
    if path := cache_path(ctx, unit.meta.get('video_id')):
        path.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            path.parent.rmdir()


def _fetch(ctx: Ctx, args: argparse.Namespace, unit: Unit, summary: RunSummary) -> None:
    # The ranking funnel may already hold this video's metadata and captions.
    cached = _read_cache(ctx, unit)
    try:
        info = cached.get('info') or listing.video_info(unit.uri)
        text = cached.get('vtt')
        if text is None:
            text = captions.read_captions(unit.uri, info.get('language') or 'en')
        cues = vtt.parse_vtt(text)
    except CaptionsThrottledError as exc:
        _captions_throttled(ctx, unit, exc, summary)
        return
    except YtDlpError as exc:
        _fail(ctx, unit, exc, summary)
        return
    if cues:
        _finish(ctx, args, unit, info, cues, 'captions', summary)
    else:
        ctx.store.mark(unit.id, 'needs_asr')
    _drop_cache(ctx, unit)


def _transcribe(
    ctx: Ctx, args: argparse.Namespace, unit: Unit, summary: RunSummary
) -> bool:
    """Returns False when ASR cannot run at all, so the caller stops instead of retrying."""
    try:
        info = listing.video_info(unit.uri)
        with tempfile.TemporaryDirectory() as tmp:
            cues = asr.transcribe(asr.fetch_audio(unit.uri, Path(tmp)), args.asr_model)
    except YtDlpError as exc:
        _fail(ctx, unit, exc, summary)
        return True
    except ImportError as exc:
        ctx.store.mark(unit.id, 'needs_asr')
        summary.note(f'no whisper backend installed ({exc}): run transcribe.py')
        return False
    except Exception as exc:  # noqa: BLE001 - whisper backends raise arbitrary types
        # Not a YtDlpError: without this the run dies and the unit is re-leased forever.
        if ctx.store.fail(unit.id, f'{type(exc).__name__}: {exc}') == 'failed':
            summary.failed += 1
        summary.note(f'transcription failed for {unit.uri}: {exc}')
        return True
    if not cues:
        ctx.store.mark(unit.id, 'skipped', 'no speech detected')
        summary.skipped += 1
        return True
    _finish(ctx, args, unit, info, cues, 'asr', summary)
    return True


def _at_page_cap(ctx: Ctx) -> bool:
    return (
        ctx.max_pages is not None
        and ctx.store.counts().get(NAME, {}).get('done', 0) >= ctx.max_pages
    )


def _work(ctx: Ctx, args: argparse.Namespace, summary: RunSummary) -> None:
    status = 'needs_asr' if args.asr else 'pending'
    # Counting stored videos, not this run's, keeps a resumed run inside --max-pages.
    while not ctx.over_budget() and not _at_page_cap(ctx):
        claimed = ctx.store.claim(NAME, status)
        if not claimed:
            return
        if args.asr:
            if not _transcribe(ctx, args, claimed[0], summary):
                return
        else:
            _fetch(ctx, args, claimed[0], summary)


def _report_waiting(ctx: Ctx, summary: RunSummary, status: str) -> None:
    """Say so when units sit in retry backoff, else an early re-run looks like a silent no-op."""
    now = time.time()
    waiting = [u.next_at for u in ctx.store.units(NAME, status) if u.next_at > now]
    if waiting:
        until = (
            datetime.fromtimestamp(min(waiting))
            .astimezone()
            .strftime('%Y-%m-%d %H:%M:%S')
        )
        _warn(ctx, summary, f'{len(waiting)} units waiting until {until} (retry backoff)')


def run(ctx: Ctx, args: argparse.Namespace) -> RunSummary:
    summary = RunSummary()
    if not args.asr:
        expand_seeds(ctx, args, summary)
    _work(ctx, args, summary)
    _report_waiting(ctx, summary, 'needs_asr' if args.asr else 'pending')
    summary.needs_asr = len(ctx.store.units(NAME, 'needs_asr'))
    return summary
