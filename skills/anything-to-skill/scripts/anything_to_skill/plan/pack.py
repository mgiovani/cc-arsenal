import re
from collections.abc import Iterator
from typing import Any

from anything_to_skill.core import tokens
from anything_to_skill.core.models import Unit
from anything_to_skill.plan.priority import hints, short_slug, slugify

MIN_SPLIT_SEGMENTS = 2
SMALL = 800  # pages below this are concatenated with neighbours
MIN_FILE = 1500
TARGET_MAX = 4000
HARD_MAX = 8000
TOC_LINES = 300
SUMMARY_CHARS = 160
FENCE = re.compile(
    r'^ {0,3}(?:> ?)* {0,3}(`{3,}|~{3,})(.*)$'
)  # fences may sit in blockquotes
_H1 = re.compile(r'^# +(.+?)\s*$')
_LINK = re.compile(r'\[([^\]]*)\]\([^)]*\)')
_MONTH = r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?'
_DATE = re.compile(
    rf'\b(?:\d{{4}}-\d{{2}}-\d{{2}}|{_MONTH} \d{{1,2}}(?:st|nd|rd|th)?,? \d{{4}}|\d{{1,2}} {_MONTH} \d{{4}}|{_MONTH} \d{{4}})\b',
    re.I,
)
_BANNER = re.compile(
    r'\b(?:released?|last (?:updated|modified)|published|posted on|copyright|'
    r'all rights reserved|unsupported version|this page in other versions|skip to)\b|\u00a9',
    re.I,
)
_TOC_LINE = re.compile(r'^(?:[A-Z]\.)?\d+(?:\.\d+)+\.?\s+[^.!?]*$')
_BYLINE = re.compile(r'\S+@\S+\.\w+')
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9`"])')
BANNER_MAX_CHARS = 120
DATE_LINE_MAX_CHARS = 60
MIN_SENTENCE_CHARS = 25
MIN_NAV_WORDS = 4
MIN_NAV_LINKS = 2
MIN_SUMMARY_WORDS = 4
SUBSTANTIVE_WORDS = 8
SUMMARY_SECTIONS = 6
MIN_STEM_CHARS = 5
SPLIT_SLUG_CHARS = 40
_STAMP = re.compile(r'\s*\[\d{1,2}:\d{2}(?::\d{2})?\]\s*')
# Spoken or blog-style openers that say nothing about the page: greetings, self-introduction, framing.
_OPENER = re.compile(
    r"^(?:(?:hi|hello|hey|howdy|welcome|greetings|thanks|thank you|what'?s up|good (?:morning|afternoon|evening)"
    r"|(?:hey )?(?:friends|folks|guys|everyone|everybody)|my name is|i'?m \w+ and"
    r'|in this (?:video|tutorial|lesson|post|article)|today (?:we|i)\b)\b'
    r'|(?:ok|okay|alright|all right|so|well|yeah|um|uh)\b[,.!]?\s)',
    re.I,
)
# Short site chrome: translation notices and calls to action.
_NOTICE = re.compile(
    r'\b(?:translation of this (?:article|page|post)|is available (?:here|in)'
    r'|(?:training|consulting) and (?:consulting|training)|subscribe to|sign up for'
    r'|follow (?:me|us) on)\b',
    re.I,
)
_SUFFIX = re.compile(r'(?:ing|es|s)$')


def walk_lines(text: str) -> Iterator[tuple[str, bool]]:
    """Yield (line, protected): protected is True inside a fenced block, delimiters included."""
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line.rstrip('\r\n'))
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
            yield line, fence is not None
        else:
            yield line, True
            if (
                m
                and m.group(1)[0] == fence[0]
                and len(m.group(1)) >= fence[1]
                and not m.group(2).strip()
            ):
                fence = None


def _split_before_heading(text: str, level: int) -> list[str]:
    prefix = '#' * level + ' '
    segs: list[str] = []
    cur = ''
    for line, protected in walk_lines(text):
        if cur and not protected and line.startswith(prefix):
            segs.append(cur)
            cur = ''
        cur += line
    return [*segs, cur] if cur else segs


def _split_paragraphs(text: str) -> list[str]:
    segs: list[str] = []
    cur = ''
    for line, protected in walk_lines(text):
        cur += line
        if not protected and not line.strip():
            segs.append(cur)
            cur = ''
    return [*segs, cur] if cur else segs


def _merge(pieces: list[str], limit: int) -> list[str]:
    out: list[str] = []
    cur = ''
    for piece in pieces:
        if cur and tokens.count(cur) + tokens.count(piece) > limit:
            out.append(cur)
            cur = ''
        cur += piece
    return [*out, cur] if cur else out


def split_text(
    text: str, limit: int = TARGET_MAX, levels: tuple[int, ...] = (2, 3)
) -> list[str]:
    """Split on ## then ### then paragraphs; pieces concatenate back to text and never cut a fence.

    A single paragraph or fence larger than limit stays whole.
    """
    if tokens.count(text) <= limit:
        return [text]
    if not levels:
        return _merge(_split_paragraphs(text), limit)
    segs = _split_before_heading(text, levels[0])
    if len(segs) < MIN_SPLIT_SEGMENTS:
        return split_text(text, limit, levels[1:])
    return _merge([p for s in segs for p in split_text(s, limit, levels[1:])], limit)


def _demote(body: str) -> str:
    return ''.join(
        f'#{line}' if not prot and line.startswith('#') else line
        for line, prot in walk_lines(body)
    )


def _headings(body: str) -> list[str]:
    return [
        line.strip()
        for line, prot in walk_lines(body)
        if not prot and re.match(r'^#{2,3} \S', line)
    ]


def _toc(body: str) -> str:
    rows = []
    for h in _headings(body):
        level = len(h) - len(h.lstrip('#'))
        title = h.lstrip('#').strip()
        rows.append(f'{"  " * (level - 2)}- [{title}](#{slugify(title)})')
    return '## Contents\n\n' + '\n'.join(rows) + '\n\n' if rows else ''


def _strip_h1(text: str) -> tuple[str | None, str]:
    head, _, rest = text.partition('\n')
    m = _H1.match(head)
    return (m.group(1), rest.lstrip('\n')) if m else (None, text)


def _is_boilerplate(line: str, text: str, repeated: frozenset[str]) -> bool:
    """A banner, date stamp or link-only navigation row rather than page content."""
    if ' '.join(line.split()) in repeated:
        return True
    if len(text) <= BANNER_MAX_CHARS and (_BANNER.search(text) or _NOTICE.search(text)):
        return True
    if len(text) <= DATE_LINE_MAX_CHARS and _DATE.search(text):
        return True
    if (
        _TOC_LINE.match(text)
        or _BYLINE.search(text)
        or len(text.split()) < MIN_SUMMARY_WORDS
    ):
        return True
    links = len(_LINK.findall(line))
    return links >= MIN_NAV_LINKS and len(_LINK.sub('', line).split()) < MIN_NAV_WORDS


def _clip(text: str) -> str:
    return (
        text
        if len(text) <= SUMMARY_CHARS
        else text[: SUMMARY_CHARS - 3].rsplit(' ', 1)[0] + '...'
    )


def _lead_sentences(body: str, repeated: frozenset[str]) -> list[str]:
    """The first real sentence under each of the first few headings (or before the first).

    Banners, dates, nav rows, host-repeated lines, transcript timestamps and greeting openers
    never count as a sentence; the search moves on to the next line of the same section.
    """
    leads: list[str] = []
    fresh = True
    for line, prot in walk_lines(body):
        if prot:
            continue
        if line.lstrip().startswith('#'):
            fresh = True
            if len(leads) >= SUMMARY_SECTIONS:
                break
            continue
        s = _STAMP.sub(
            ' ',
            _LINK.sub(r'\1', line)
            .strip()
            .lstrip('>*-+ ')
            .replace('`', '')
            .replace('*', ''),
        )
        s = re.sub(r'\s+', ' ', s).strip()
        if not fresh or not s or s.startswith(('|', '!')):
            continue
        if _is_boilerplate(line, s, repeated) or _OPENER.match(s):
            continue
        first = _SENTENCE_END.split(s, maxsplit=1)[0]
        leads.append(first if len(first) >= MIN_SENTENCE_CHARS else s)
        fresh = False
    return leads


def _summary(
    body: str,
    fallback: str,
    repeated: frozenset[str] = frozenset(),
    keywords: frozenset[str] = frozenset(),
) -> str:
    """One line for the INDEX: the section-opening sentence that names a goal keyword, else the
    first substantive one (8+ words), else the first real line, else `fallback`."""
    leads = _lead_sentences(body, repeated)
    solid = [s for s in leads if len(s.split()) >= SUBSTANTIVE_WORDS]
    stems = {_SUFFIX.sub('', k) if len(k) > MIN_STEM_CHARS else k for k in keywords}
    on_goal = [s for s in solid if any(k in s.lower() for k in stems)]
    pick = (on_goal or solid or leads or [fallback])[0]
    return _clip(pick)


def _describe(
    u: Unit,
    piece: str,
    fallback: str,
    repeated: frozenset[str],
    keywords: frozenset[str],
    carried: str = '',
) -> str:
    """INDEX summary of one file's text. A video reads better as its chapter titles (or, with
    none, its description or title) than as a transcript sentence; `carried` is the chapter a split
    piece continues."""
    if u.kind == 'video':
        chapters = real_headings(piece) or ([carried] if carried else [])
        if chapters:
            return _clip('Chapters: ' + '; '.join(chapters))
        if lead := _lead_sentences(str(u.meta.get('description') or ''), repeated):
            return _clip(lead[0])
        return _clip(fallback)  # a transcript line is a fragment, the title is not
    return _summary(_strip_h1(piece)[1], fallback, repeated, keywords)


def _title(unit: Unit, text: str) -> str:
    return unit.title or _strip_h1(text)[0] or hints(unit)[-1].replace('-', ' ')


def render_file(
    entry: dict[str, Any], units: dict[int, Unit], texts: dict[int, str]
) -> str:
    """Materialize one plan file: title, one-line summary, source, then the page slices."""
    slices = [
        (units[p['unit']], texts[p['unit']][p['start'] : p['end']])
        for p in entry['parts']
    ]
    multi = len({u.id for u, _ in slices}) > 1
    if multi:
        body = ''.join(
            f'## {_title(u, texts[u.id])}\n\nSource: {u.source_label()}\n\n{_demote(_strip_h1(s)[1]).strip()}\n\n'
            for u, s in slices
        )
        head = f'# {entry["title"]}\n\n> {entry["summary"]}\n\n'
    else:
        unit, s = slices[0]
        body = _strip_h1(s)[1].strip() + '\n'
        head = f'# {entry["title"]}\n\n> {entry["summary"]}\n\nSource: {unit.source_label()}\n\n'
    toc = _toc(body) if (head + body).count('\n') > TOC_LINES else ''
    return (head + toc + body).rstrip() + '\n'


class Namer:
    def __init__(self) -> None:
        self.taken: set[str] = set()

    def __call__(self, base: str) -> str:
        name, n = f'{base}.md', 1
        while name in self.taken:
            n += 1
            name = f'{base}-{n}.md'
        self.taken.add(name)
        return name


def _kind(units: list[Unit]) -> str:
    kinds = sorted(str(u.hint.get('kind') or u.kind) for u in units)
    return max(kinds, key=kinds.count)


_ADMONITIONS = frozenset({'note', 'tip', 'caution', 'warning', 'important'})
_SECTION_NUMBER = re.compile(r'^(?:[A-Z]\.)?\d+(?:\.\d+)*\.?\s+')


def real_headings(piece: str) -> list[str]:
    """Heading texts without link markup, section numbers or video timestamps; admonition boxes
    (Note, Tip) are not sections."""
    out = []
    for h in _headings(piece):
        text = _SECTION_NUMBER.sub(
            '', _STAMP.sub(' ', _LINK.sub(r'\1', h.lstrip('#'))).strip()
        )
        if text and text.lower() not in _ADMONITIONS:
            out.append(text)
    return out


def chapters_of(text: str) -> list[tuple[int, int, str]]:
    """(start, end, title) of each `##` chapter as slices of `text`; text before the first
    chapter belongs to it."""
    out: list[tuple[int, int, str]] = []
    start = end = 0
    for seg in _split_before_heading(text, 2):
        end += len(seg)
        if seg.startswith('## '):
            title = _STAMP.sub(' ', seg.partition('\n')[0].lstrip('#')).strip()
            out.append((start, end, title))
            start = end
    return out


def pack_files(
    units: list[Unit],
    texts: dict[int, str],
    *,
    names: dict[int, str] | None = None,
    boilerplate: frozenset[str] = frozenset(),
    keywords: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Group and split one section's pages into 1.5k-4k token files (hard max 8k, fence-safe).

    Order is preserved. `names` (unit id to name) overrides a unit's file name stem. Entries
    carry `name` (bare file name), `title`, `summary`, `kind`, `tokens`, `units` and `parts`
    (char slices of each unit's stored markdown, enough for render_file to rebuild the text).
    A page above HARD_MAX yields several entries, each named after its first `##` heading, else
    `<heading>-part-N` for a piece that continues one. A video is never packed with others: each
    chapter is a file named by the chapter title, a chapterless video is one file named by the
    video.
    `boilerplate` lines (repeated across a host's pages) never become a summary; a summary
    sentence that names a goal `keyword` wins over the first one.
    """
    by_id = {u.id: u for u in units}
    name_for = Namer()
    entries: list[dict[str, Any]] = []

    def add(
        members: list[Unit],
        parts: list[dict[str, int]],
        base: str,
        title: str,
        summary: str,
    ) -> None:
        entry = {
            'name': name_for(base),
            'title': title,
            'summary': summary,
            'kind': _kind(members),
            'units': [u.id for u in members],
            'parts': parts,
        }
        entry['tokens'] = tokens.count(render_file(entry, by_id, texts))
        entries.append(entry)

    def whole(u: Unit) -> dict[str, int]:
        return {'unit': u.id, 'start': 0, 'end': len(texts[u.id])}

    def base(u: Unit) -> str:
        return (names or {}).get(u.id) or hints(u)[-1]

    def add_video(u: Unit) -> None:
        text, title = texts[u.id], _title(u, texts[u.id])
        root = base(u)
        chapters = chapters_of(text) or [(0, len(text), '')]
        for start, end, chapter in chapters:
            body = text[start:end]
            pieces = split_text(body) if tokens.count(body) > HARD_MAX else [body]
            stem = short_slug(chapter) or root
            offset = start
            for n, piece in enumerate(pieces, 1):
                part = {'unit': u.id, 'start': offset, 'end': offset + len(piece)}
                offset += len(piece)
                more = len(pieces) > 1
                add(
                    [u],
                    [part],
                    f'{stem}-part-{n}' if more else stem,
                    f'{title}: {chapter}' if chapter else title,
                    _describe(u, piece, title, boilerplate, keywords, chapter),
                )

    sizes = {u.id: tokens.count(texts[u.id]) for u in units}
    pending: list[Unit] = []

    def flush() -> None:
        if not pending:
            return
        group = list(pending)
        pending.clear()
        if len(group) == 1:
            u = group[0]
            add(
                group,
                [whole(u)],
                base(u),
                _title(u, texts[u.id]),
                _describe(u, texts[u.id], _title(u, texts[u.id]), boilerplate, keywords),
            )
            return
        titles = [_title(u, texts[u.id]) for u in group]
        summary = 'Covers: ' + '; '.join(titles)
        if len(summary) > SUMMARY_CHARS:
            summary = summary[: SUMMARY_CHARS - 3].rsplit(' ', 1)[0] + '...'
        add(
            group,
            [whole(u) for u in group],
            f'{base(group[0])}-etc',
            titles[0] + ' and related',
            summary,
        )

    for u in units:
        if u.kind == 'video':
            flush()
            add_video(u)
            continue
        size = sizes[u.id]
        if size < SMALL:
            if pending and sum(sizes[p.id] for p in pending) + size > TARGET_MAX:
                flush()
            pending.append(u)
            if sum(sizes[p.id] for p in pending) >= MIN_FILE:
                flush()
            continue
        flush()
        text, title = texts[u.id], _title(u, texts[u.id])
        if size <= HARD_MAX:
            add(
                [u],
                [whole(u)],
                base(u),
                title,
                _describe(u, text, title, boilerplate, keywords),
            )
            continue
        offset = 0
        current = ''
        seen: dict[str, int] = {}
        for piece in split_text(text):
            part = {'unit': u.id, 'start': offset, 'end': offset + len(piece)}
            offset += len(piece)
            heads = real_headings(piece)
            heading = heads[0] if heads else current
            current = heads[-1] if heads else current
            nth = seen[current] = seen.get(current, 0) + 1
            slug = short_slug(heading, SPLIT_SLUG_CHARS)
            if not slug or base(u).endswith(slug):
                slug = 'overview'
            if not heads and heading:
                slug, label = f'{slug}-part-{nth}', f' (part {nth})'
            else:
                label = ''
            add(
                [u],
                [part],
                f'{base(u)}-{slug}',
                f'{title}: {heading}{label}' if heading else title,
                _describe(u, piece, title, boilerplate, keywords, current),
            )
    flush()
    return entries
