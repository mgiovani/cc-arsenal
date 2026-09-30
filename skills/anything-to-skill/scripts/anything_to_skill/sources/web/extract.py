import html as htmllib
import re
from collections import Counter
from urllib.parse import urldefrag, urljoin, urlsplit

from anything_to_skill.core.store import Store

BOILERPLATE_KEY = 'web.boilerplate'
MIN_FENCE = 3  # shortest run that still counts as a code line
EDGE_HEAD = 3  # leading prose lines checked for site banners
EDGE_TAIL = 8  # trailing prose lines checked for footers
# a linked banner may sit on far fewer pages than a plain one
LINKED_EDGE_THRESHOLD = 0.05
LINKED_EDGE_MIN_PAGES = 3
MAX_STRIP_PASSES = 3
NAV_TEXT_MAX = (
    120  # plain text allowed around the links of a one-line nav bar (chapter titles)
)
SHELL_TEXT_MAX = 200
BLOCKED_TEXT_MAX = 3000
_PRE = re.compile(r'<pre[\s>]', re.I)
_NAMES = r'(?:docContent|doc-content|main-content|markdown-body|md-content|content|main)'
# Tiers in priority order; the first tier with a hit supplies the content container.
_CONTAINERS = [
    re.compile(r'<(main|article)\b[^>]*>', re.I),
    re.compile(r'<(div|section)\b[^>]*\brole="main"[^>]*>', re.I),
    re.compile(rf'<(div|section)\b[^>]*\bid="{_NAMES}"[^>]*>', re.I),
    re.compile(
        rf'<(div|section)\b[^>]*\bclass="(?:[^"]*\s)?{_NAMES}(?:\s[^"]*)?"[^>]*>', re.I
    ),
]
_TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
_H1 = re.compile(r'^#\s+(.+)$', re.M)
_DROP = re.compile(r'<(script|style|noscript|template)\b.*?</\1>|<!--.*?-->', re.I | re.S)
_TAG = re.compile(r'<[^>]+>')
_BLOCKED = re.compile(
    r'just a moment|attention required|verify you are (a )?human|are you a robot'
    r'|access denied|captcha|checking your browser|request blocked|unusual traffic',
    re.I,
)
_LINK = re.compile(r'(?<!!)\[([^\]]*)\]\(\s*<?([^)\s>]*)>?(\s+"[^"]*")?\s*\)')
_RULE = re.compile(r'([-*_])(\s*\1){2,}')
_NAV_ANCHOR = re.compile(r'(prev(ious)?|next|up|home)( page)?', re.I)
_LINK_TARGET = re.compile(r'\]\([^)]*\)')
_EXCLUDED = ['nav', 'aside', 'footer', 'script', 'style']


def visible_text(html: str) -> str:
    return ' '.join(htmllib.unescape(_TAG.sub(' ', _DROP.sub(' ', html))).split())


def is_js_shell(html: str) -> bool:
    """A near-empty document that ships scripts: the content is rendered client-side."""
    return len(visible_text(html)) < SHELL_TEXT_MAX and '<script' in html.lower()


def is_blocked(text: str) -> bool:
    """A short challenge/denial page; long pages may merely mention a captcha."""
    plain = visible_text(text)
    return len(plain) < BLOCKED_TEXT_MAX and bool(_BLOCKED.search(plain))


def _fences(md: str) -> int:
    return sum(1 for line in md.splitlines() if line.lstrip().startswith('```')) // 2


def _title(html: str, md: str) -> str | None:
    if m := _TITLE.search(html):
        text = ' '.join(htmllib.unescape(m.group(1)).split())
        if text:
            return text
    m = _H1.search(md)
    return (m.group(1) or '').strip() or None if m else None


def content_container(html: str) -> str:
    """The main content element, found by tag/role/id/class hints; the whole page if none."""
    for pattern in _CONTAINERS:
        if m := pattern.search(html):
            tag = re.compile(rf'<{m.group(1)}\b|</{m.group(1)}\s*>', re.I)
            depth = 0
            for t in tag.finditer(html, m.start()):
                depth += 1 if t.group(0)[1] != '/' else -1
                if depth == 0:
                    return html[m.start() : t.end()]
            return html[m.start() :]
    return html


def _via_html_to_markdown(html: str, url: str) -> str:
    from html_to_markdown import (  # noqa: PLC0415 - lazy heavy dep
        ConversionOptions,
        convert,
    )

    fragment = content_container(html)
    options = ConversionOptions(
        heading_style='atx',
        exclude_selectors=_EXCLUDED,
        skip_images=True,
        extract_metadata=False,
        base_url=url,
    )
    return (convert(fragment, options).content or '').strip()


def resolve_links(md: str, url: str) -> str:
    """Make links absolute and unwrap same-page links (heading permalinks, in-page anchors).

    Done here rather than by trafilatura, which resolves `../x/` against the wrong base.
    Fenced code is left alone.
    """
    page = urldefrag(url)[0]

    def fix(m: re.Match[str]) -> str:
        text, href, title = m.group(1), m.group(2), m.group(3) or ''
        target = urljoin(url, href) if href else url
        return text if urldefrag(target)[0] == page else f'[{text}]({target}{title})'

    out, in_fence = [], False
    for line in md.split('\n'):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
        out.append(line if in_fence else _LINK.sub(fix, line))
    return '\n'.join(out)


def to_markdown(html: str, url: str) -> tuple[str, str | None]:
    """Return (markdown, title); trafilatura first, html-to-markdown when code fences are lost."""
    import trafilatura  # noqa: PLC0415 - lazy heavy dep

    md = (
        trafilatura.extract(
            html,
            output_format='markdown',
            include_formatting=True,
            include_links=True,
            include_tables=True,
            include_comments=False,
            with_metadata=False,
            favor_recall=True,
        )
        or ''
    ).strip()
    if not md or len(_PRE.findall(html)) > _fences(md):
        alt = _via_html_to_markdown(html, url)
        if len(alt) >= len(md) // 2 or not md:
            md = alt
    md = resolve_links(md, url)
    return md, _title(html, md)


def _key(line: str) -> str:
    """A line's identity for repetition: link targets ignored, so a per-page 'report an issue'
    link still counts as the same footer line."""
    return _LINK_TARGET.sub('](_)', line.strip())


def find_boilerplate(
    docs: dict[int, str],
    threshold: float = 0.5,
    min_docs: int = 5,
    edge_threshold: float = 0.3,
) -> tuple[set[str], set[str]]:
    """(anywhere, edge) line keys of one host's pages that are boilerplate.

    A prose line is boilerplate when it is on more than `threshold` of the pages, or, within
    the first EDGE_HEAD / last EDGE_TAIL prose lines (banners, footers), on at least
    `edge_threshold` of them. Headings and fenced code are exempt (a `}` or `## Parameters`
    legitimately repeats).
    """
    if len(docs) < min_docs:
        return set(), set()
    anywhere: Counter[str] = Counter()
    edges: Counter[str] = Counter()
    for md in docs.values():
        lines = _prose_lines(md)
        anywhere.update({_key(ln) for ln in lines})
        edges.update({_key(ln) for ln in _edge(lines)})
    return (
        {k for k, n in anywhere.items() if n / len(docs) > threshold},
        {k for k, n in edges.items() if _edge_repeated(k, n, len(docs), edge_threshold)},
    )


def _edge_repeated(key: str, pages: int, total: int, threshold: float) -> bool:
    """A linked line (a release banner) is site-wide on far fewer pages than a plain one:
    the extractor keeps it only where the page markup happens to place it inside the content."""
    if pages / total >= threshold:
        return True
    return (
        pages >= LINKED_EDGE_MIN_PAGES
        and pages / total >= LINKED_EDGE_THRESHOLD
        and bool(_LINK.search(key))
    )


def remove_boilerplate(
    docs: dict[int, str], anywhere: set[str], edge: set[str]
) -> dict[int, str]:
    """The documents that change once the given lines are dropped; edge lines only at an edge."""
    if not anywhere and not edge:
        return {}
    out = {}
    for key, md in docs.items():
        drop = anywhere | (edge & {_key(ln) for ln in _edge(_prose_lines(md))})
        kept, in_fence, changed = [], False, False
        for line in md.splitlines():
            if line.lstrip().startswith('```'):
                in_fence = not in_fence
            elif not in_fence and _is_prose(line.strip()) and _key(line) in drop:
                changed = True
                continue
            kept.append(line)
        if changed:
            out[key] = _collapse_blanks(kept)
    return out


def _collapse_blanks(lines: list[str]) -> str:
    """Join lines, squeezing 3+ newlines to 2 outside fenced code (a code sample's own blank
    runs are content)."""
    out, in_fence, blanks = [], False, 0
    for line in lines:
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
        if not in_fence and not line.strip():
            blanks += 1
            if blanks > 1:
                continue
        else:
            blanks = 0
        out.append(line)
    return '\n'.join(out).strip() + '\n'


def _nav_anchors(line: str) -> int:
    return sum(
        bool(_NAV_ANCHOR.fullmatch(m.group(1).strip())) for m in _LINK.finditer(line)
    )


def _nav_items(lines: list[str]) -> list[range]:
    """Line ranges that are page navigation: a table with two or more Prev/Up/Next/Home links
    (its title row repeats the page heading), or a one-line bar of such links plus a few words."""
    items, in_fence, i = [], False, 0
    while i < len(lines):
        line = lines[i].strip()
        fence = line.startswith('```')
        in_fence ^= fence
        if in_fence or fence:
            i += 1
        elif line.startswith('|'):
            end = i
            while end < len(lines) and lines[end].strip().startswith('|'):
                end += 1
            if sum(_nav_anchors(ln) for ln in lines[i:end]) >= 2:  # noqa: PLR2004
                items.append(range(i, end))
            i = end
        else:
            if (
                _is_prose(line)
                and _nav_anchors(line)
                and not line.endswith(('.', '!', '?'))  # a nav bar is not a sentence
                and len(_LINK.sub('', line)) <= NAV_TEXT_MAX
            ):
                items.append(range(i, i + 1))
            i += 1
    return items


def strip_nav(md: str) -> str:
    """Drop Prev/Up/Next/Home navigation near the top or bottom of a page, plus the rule that
    separated it from the content. Judged per page, so no repetition threshold is needed."""
    lines = md.splitlines()
    items = _nav_items(lines)
    nav = {i for item in items for i in item}
    prose = [i for i, ln in enumerate(lines) if i not in nav and _is_prose(ln.strip())]
    drop = {
        i
        for item in items
        if sum(p < item.start for p in prose) < EDGE_HEAD
        or sum(p >= item.stop for p in prose) < EDGE_TAIL
        for i in item
    }
    if not drop:
        return md
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    while kept and (not kept[0].strip() or _RULE.fullmatch(kept[0].strip())):
        kept.pop(0)
    while kept and (not kept[-1].strip() or _RULE.fullmatch(kept[-1].strip())):
        kept.pop()
    return _collapse_blanks(kept)


def strip_host_boilerplate(store: Store) -> int:
    """Drop repeated nav/banner/footer lines, judged per host over every stored page (not just
    this run's, so multi-site workspaces are covered); returns pages changed.

    The lines found are remembered in the workspace meta and always re-applied: once a few
    pages are stripped they no longer look repeated, so a later run (or a page fetched after
    the others) would otherwise keep them. Idempotent, so the planner can call it again."""
    by_host: dict[str, dict[int, str]] = {}
    original: dict[int, str] = {}
    for unit in store.units(source='web', status='done'):
        if unit.md_path:
            host = urlsplit(unit.uri).netloc.lower()
            original[unit.id] = store.read_markdown(unit.id)
            by_host.setdefault(host, {})[unit.id] = strip_nav(original[unit.id])
    known = store.get_meta(BOILERPLATE_KEY, {})
    changed = 0
    for host, host_docs in by_host.items():
        docs = dict(host_docs)
        anywhere = set(known.get(host, {}).get('anywhere', []))
        edge = set(known.get(host, {}).get('edge', []))
        # Stripping shifts lines into the head/tail windows, so a line can become an edge
        # repeat only after a pass; iterate until stable to stay idempotent.
        for _ in range(MAX_STRIP_PASSES):
            found_anywhere, found_edge = find_boilerplate(docs)
            anywhere |= found_anywhere
            edge |= found_edge
            if not (dropped := remove_boilerplate(docs, anywhere, edge)):
                break
            docs = {**docs, **dropped}
        known[host] = {'anywhere': sorted(anywhere), 'edge': sorted(edge)}
        for unit_id, markdown in docs.items():
            if markdown != original[unit_id]:
                store.finish(unit_id, markdown)
                changed += 1
    store.set_meta(BOILERPLATE_KEY, known)
    return changed


def _edge(lines: list[str]) -> list[str]:
    return [*lines[:EDGE_HEAD], *lines[max(EDGE_HEAD, len(lines) - EDGE_TAIL) :]]


def _is_prose(line: str) -> bool:
    """Table rows (header and separator repeat on every table) and horizontal rules are
    structure, never boilerplate."""
    return (
        len(line) >= MIN_FENCE
        and not line.startswith(('#', '|'))
        and not _RULE.fullmatch(line)
    )


def _prose_lines(md: str) -> list[str]:
    lines, in_fence = [], False
    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith('```'):
            in_fence = not in_fence
        elif not in_fence and _is_prose(line):
            lines.append(line)
    return lines
