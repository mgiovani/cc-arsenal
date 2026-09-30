import re
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from anything_to_skill.core.models import Unit

# Words that carry no topic signal in a goal sentence.
_STOP = frozenset(
    {
        'the',
        'and',
        'for',
        'with',
        'from',
        'that',
        'this',
        'into',
        'about',
        'how',
        'what',
        'when',
        'best',
        'practices',
        'practice',
        'guide',
        'guides',
        'use',
        'using',
        'used',
        'learn',
        'want',
        'need',
        'are',
        'you',
        'your',
        'can',
        'all',
        'any',
        'not',
    }
)
_WORD = re.compile(r'[a-z0-9]+')
_NOISE = frozenset(
    {
        'docs',
        'doc',
        'documentation',
        'en',
        'en-us',
        'latest',
        'stable',
        'watch',
        'embed',
        'shorts',
        'current',
    }
)
_VERSION = re.compile(r'^v?\d+(\.\d+)*$')
_EXT = re.compile(r'\.(html?|md|markdown|txt|rst|pdf|docx?|pptx?|epub|php|aspx?)$', re.I)
MIN_KEYWORD_CHARS = 3
KEYWORD_HIT = 1.5
MAX_HITS = 4
MAX_TITLE_SLUG_CHARS = 48
SHORT_SLUG_CHARS = 40
MIN_TITLE_WORDS = 3
LLMS_TXT_BONUS = 3.0
SHALLOW_BONUS = 2.0


_APOSTROPHE = re.compile(r"['\u2019\u2018`]")
# Splits a title where a subtitle, series tag or trailing qualifier begins.
_TITLE_BREAK = re.compile(r'\s+[-\u2013\u2014|]\s+|\s*//\s*|\s*:\s+|\s+in the\s+')
_FILLER = frozenset(
    {'a', 'an', 'and', 'as', 'at', 'by', 'for', 'from', 'in', 'into', 'of', 'on', 'or'}
    | {'the', 'to', 'vs', 'with', 'your'}
)


def slugify(text: str) -> str:
    """Lowercase words joined by '-'; apostrophes vanish rather than split ("don't" is "dont")."""
    return re.sub(r'[^a-z0-9]+', '-', _APOSTROPHE.sub('', text.lower())).strip('-')


def short_slug(text: str, limit: int = SHORT_SLUG_CHARS) -> str:
    """slugify, cut at a word boundary once it passes `limit` characters (never ending on filler)."""
    slug = slugify(text)
    if len(slug) <= limit:
        return slug
    words = (
        slug[:limit].split('-')[:-1] if slug[limit] != '-' else slug[:limit].split('-')
    )
    while len(words) > 1 and words[-1] in _FILLER:
        words.pop()
    return '-'.join(words) or slug[:limit]


def video_slug(title: str) -> str:
    """Short folder-worthy name for a video: the title's main clause minus filler words.

    `LIVE: Uncle Bob on Software Fundamentals in the Age of AI` becomes
    `uncle-bob-software-fundamentals-age-ai`; a one- or two-word lead ("LIVE") is a tag, not the title.
    """
    parts = [p for p in _TITLE_BREAK.split(title) if p.strip()]
    main = next((p for p in parts if len(p.split()) >= MIN_TITLE_WORDS), title)
    words = slugify(main).split('-')
    return short_slug('-'.join(w for w in words if w not in _FILLER) or slugify(main))


def goal_keywords(goal: str) -> set[str]:
    return {
        w
        for w in _WORD.findall(goal.lower())
        if len(w) >= MIN_KEYWORD_CHARS and w not in _STOP
    }


def _as_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value] if isinstance(value, list) else []


def hints(unit: Unit) -> list[str]:
    """Slugged grouping path for a unit: directory segments, then the page name (always last).

    Order of trust: explicit hint['section'] / hint['breadcrumb'] (set by a source), then the
    relative file path in hint['relpath'] / hint['path'] (local), then the URL path minus noise
    segments. A video is named by its short title, never its URL, and its channel (a list
    hint['path']) is not a topic.
    """
    path_hint = unit.hint.get('relpath') or unit.hint.get('path')
    if urlsplit(unit.uri).scheme in ('http', 'https'):
        raw = [s for s in urlsplit(unit.uri).path.split('/') if s]
    else:
        rel = path_hint or PurePosixPath(unit.uri.replace('\\', '/')).name
        raw = [s for s in str(rel).split('/') if s]
    if raw:
        raw[-1] = _EXT.sub('', raw[-1])
    segs = [
        s for s in map(slugify, raw) if s and s not in _NOISE and not _VERSION.match(s)
    ]
    if unit.kind == 'video':
        segs = []
    explicit = [
        s
        for s in map(
            slugify,
            _as_list(unit.hint.get('section') or unit.hint.get('breadcrumb')),
        )
        if s
    ]
    titled = (
        video_slug(unit.title or '')
        if unit.kind == 'video'
        else short_slug(unit.title or '', MAX_TITLE_SLUG_CHARS)
    )
    name = segs[-1] if segs else titled or f'unit-{unit.id}'
    return (explicit or segs[:-1]) + [name]


def priority(unit: Unit, goal_keywords: set[str], in_llms_txt: bool) -> float:
    """Higher is more worth keeping: llms.txt membership, shallow depth, goal-keyword hits."""
    haystack = f'{unit.title or ""} {urlsplit(unit.uri).path or unit.uri}'.lower()
    hits = sum(kw in haystack for kw in goal_keywords)
    return (
        (LLMS_TXT_BONUS if in_llms_txt else 0.0)
        + SHALLOW_BONUS / (1 + unit.depth)
        + min(hits, MAX_HITS) * KEYWORD_HIT
    )
