import re
from collections.abc import Callable
from pathlib import Path

from anything_to_skill.core.models import Finding
from anything_to_skill.core.store import Store

MAX_QUOTE_WORDS = 20
MIN_QUOTE_CHARS = 8
MIN_QUOTE_WORDS = 5

_PUNCT = str.maketrans({'\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"'})
_MARKER = re.compile(r'\(src:\s*(\d+)\s+["\u201c]([\s\S]+?)["\u201d]\)')
_MARKER_OPEN = re.compile(r'\(src:')
_LINK = re.compile(r'\("(.+?)" \[source\]\(([^)\s]+)\)\)')
_BULLET = re.compile(r'^[ \t]*(?:[-*+]|\d+[.)])[ \t]', re.MULTILINE)
_FENCE_OPEN = re.compile(r'^[\s>]*(`{3,}|~{3,})')
_QUOTE_LEAD = re.compile(r'^[ \t]*(?:>[ \t]?)+', re.MULTILINE)
_MD_LINK = re.compile(r'\[[^\]]*\]\([^)]*\)|`[^`]*`|https?://\S+|[\w./-]+\.md\b')
_NAV_VERB = re.compile(
    r'^(?:read|see|open|check|consult|refer|go|continue|start|visit|follow|next|back)\b',
    re.I,
)
_FILLER = frozenset(
    [
        'a',
        'an',
        'and',
        'are',
        'at',
        'for',
        'from',
        'here',
        'in',
        'into',
        'is',
        'it',
        'more',
        'of',
        'on',
        'or',
        'page',
        'pages',
        'file',
        'files',
        'section',
        'sections',
        'reference',
        'references',
        'doc',
        'docs',
        'documentation',
        'guide',
        'details',
        'detail',
        'information',
        'info',
        'about',
        'below',
        'above',
        'the',
        'this',
        'that',
        'then',
        'to',
        'with',
        'also',
        'next',
    ]
)
_NAV_TARGET = re.compile(
    r'\b(?:section|page|file|guide|chapter|below|above|references?|docs?)\b', re.I
)
MAX_NAV_CONTENT_WORDS = 2


def normalize(text: str) -> str:
    """Collapse whitespace, curly quotes and blockquote `> ` markers so verbatim checks ignore reflow."""
    return ' '.join(_QUOTE_LEAD.sub('', text.translate(_PUNCT)).split())


def is_connective(sentence: str) -> bool:
    """Navigation or transition prose ("See `x.md` for details.") that carries no claim to source."""
    rest = _MD_LINK.sub(' ', sentence)
    content = [w for w in re.findall(r"[a-z][a-z'-]+", rest.lower()) if w not in _FILLER]
    if len(content) <= MAX_NAV_CONTENT_WORDS:
        return True
    starts_nav = _NAV_VERB.match(sentence.strip().lstrip('>*-# '))
    return bool(starts_nav) and (rest != sentence or bool(_NAV_TARGET.search(sentence)))


def load_corpus(store: Store) -> dict[int, str]:
    """Normalized markdown of every finished unit, keyed by unit id."""
    return {
        u.id: normalize(store.read_markdown(u.id))
        for u in store.units(status='done')
        if u.kind != 'seed' and u.md_path
    }


def _split_fences(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Return (text with fenced lines blanked so line numbers hold, [(start line, body)])."""
    prose: list[str] = []
    blocks: list[tuple[int, str]] = []
    fence = ''
    start = 0
    body: list[str] = []
    for i, line in enumerate(text.split('\n'), 1):
        if not fence:
            opened = _FENCE_OPEN.match(line)
            if opened:
                fence, start, body = opened.group(1), i, []
                prose.append('')
            else:
                prose.append(line)
            continue
        stripped = line.lstrip('> \t').strip()
        if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
            blocks.append((start, '\n'.join(body)))
            fence = ''
        else:
            body.append(line)
        prose.append('')
    if fence:
        blocks.append((start, '\n'.join(body)))
    return '\n'.join(prose), blocks


def _quote_problem(quote: str) -> str | None:
    if len(quote.split()) > MAX_QUOTE_WORDS:
        return f'quote is longer than {MAX_QUOTE_WORDS} words'
    if len(quote.strip()) < MIN_QUOTE_CHARS:
        return 'quote is too short to be evidence'
    return None


def _claim_before(prose: str, start: int) -> str:
    """The list item or paragraph a marker closes, up to the marker."""
    para = prose[prose.rfind('\n\n', 0, start) + 1 : start]
    last = list(_BULLET.finditer(para))
    return para[last[-1].start() :] if last else para


def _style(prose: str, start: int, quote: str, line: int) -> list[Finding]:
    """Warnings for a legal marker that is weak evidence: cut mid-clause, or echoing its own claim."""
    out = []
    if len(quote.split()) < MIN_QUOTE_WORDS:
        out.append(
            Finding(
                'quote-short',
                f'quote is under {MIN_QUOTE_WORDS} words; quote the whole clause',
                line,
            )
        )
    needle = normalize(quote).casefold().strip('.!?…" ')
    if needle and needle in normalize(_claim_before(prose, start)).casefold():
        out.append(
            Finding(
                'quote-duplicates-claim',
                'the claim already contains the quote verbatim; state it in your own words',
                line,
            )
        )
    return out


def verify(
    text: str, store: Store, corpus: dict[int, str] | None = None
) -> list[Finding]:
    """Check code blocks and `(src: <id> "quote")` markers verbatim against stored units.

    Hard findings block emit; `warn` ones flag quotes that are legal but weak.
    """
    if corpus is None:
        corpus = load_corpus(store)
    prose, blocks = _split_fences(text)
    findings: list[Finding] = []
    for line, body in blocks:
        needle = normalize(body)
        if needle and not any(needle in hay for hay in corpus.values()):
            findings.append(
                Finding(
                    'code-not-verbatim',
                    'code block does not appear verbatim in any source unit',
                    line,
                    'hard',
                )
            )
    for m in _MARKER.finditer(prose):
        line = prose.count('\n', 0, m.start()) + 1
        uid, quote = int(m.group(1)), m.group(2)
        problem = _quote_problem(quote)
        if problem is None and uid not in corpus:
            problem = f'unit {uid} does not exist or has no content'
        if problem is None and normalize(quote) not in corpus[uid]:
            problem = f'quote not found verbatim in unit {uid}'
        if problem:
            findings.append(Finding('quote-unverified', problem, line, 'hard'))
        else:
            findings += _style(prose, m.start(), quote, line)
    leftover = _MARKER_OPEN.findall(_MARKER.sub('', prose))
    if leftover:
        findings.append(
            Finding(
                'src-malformed',
                f'{len(leftover)} malformed (src: ...) marker(s); use (src: <id> "quote")',
                None,
                'hard',
            )
        )
    return findings


def verify_links(text: str, base_dir: Path) -> list[Finding]:
    """Re-check rewritten markers: the linked file must exist and contain the quote."""
    prose, _ = _split_fences(text)
    findings: list[Finding] = []
    for m in _LINK.finditer(prose):
        line = prose.count('\n', 0, m.start()) + 1
        quote, link = m.groups()
        target = (base_dir / link).resolve()
        problem = _quote_problem(quote)
        if problem is None and not target.is_file():
            problem = f'linked file {link} does not exist'
        if problem is None and normalize(quote) not in normalize(
            target.read_text(encoding='utf-8')
        ):
            problem = f'quote not found in {link}'
        if problem:
            findings.append(Finding('quote-unverified', problem, line, 'hard'))
        else:
            findings += _style(prose, m.start(), quote, line)
    leftover = _MARKER_OPEN.findall(prose)
    if leftover:
        findings.append(
            Finding('src-unrewritten', 'src marker left in emitted skill', None, 'hard')
        )
    return findings


def rewrite_markers(
    text: str,
    links: dict[int, str],
    locate: Callable[[int, str], str | None] | None = None,
) -> str:
    """Rewrite src markers to relative links; `locate(id, quote)` beats `links[id]`.

    Markers with no known target stay as they are so verify reports them.
    """

    def swap(m: re.Match[str]) -> str:
        uid, quote = int(m.group(1)), m.group(2)
        target = locate(uid, quote) if locate else None
        target = target or links.get(uid)
        if not target:
            return m.group()
        return f'("{" ".join(quote.split())}" [source]({target}))'

    return _MARKER.sub(swap, text)
