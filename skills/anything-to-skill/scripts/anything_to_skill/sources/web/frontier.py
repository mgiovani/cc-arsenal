import importlib
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urldefrag, urljoin, urlsplit

MIN_STEM = 3
MIN_PREFIX = 4  # shortest word allowed to match by prefix (link "vacuum" vs "vacuumdb")
PRIORITY_SCALE = 10.0
MIN_IDF_DOCS = 20  # below this many candidates, document frequencies say nothing
_WORD = re.compile(r'[a-z0-9]{3,}')
_STOP = frozenset(
    [
        'the',
        'and',
        'for',
        'with',
        'best',
        'practice',
        'practices',
        'how',
        'use',
        'using',
        'guide',
        'about',
        'from',
        'that',
        'this',
        'what',
        'your',
        'into',
        'are',
        'can',
        'you',
        'not',
        'all',
        'any',
        'get',
        'set',
    ]
)
_NON_DOC_EXT = frozenset(
    [
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.svg',
        '.webp',
        '.ico',
        '.css',
        '.js',
        '.json',
        '.xml',
        '.zip',
        '.gz',
        '.tar',
        '.tgz',
        '.pdf',
        '.mp4',
        '.mp3',
        '.woff',
        '.woff2',
        '.ttf',
        '.eot',
        '.map',
    ]
)
_DOC_EXT = frozenset(['', '.html', '.htm', '.md', '.txt', '.php', '.aspx'])
# Site chrome: never the knowledge a skill wants, so it is fetched after the content.
_CHROME = re.compile(
    r'^(?:contact(?:-us)?|legal|imprint|impressum|privacy(?:-policy)?|terms(?:-[a-z-]+)?|'
    r'shop|store|cart|checkout|about(?:-us)?|login|log-in|signin|sign-in|signup|sign-up|'
    r'register|account|tags?|authors?)(?:\.\w+)?$'
)
CHROME_PENALTY = 0.4


@dataclass
class Link:
    url: str
    anchor: str = ''
    heading: str = ''


class LinkScorer(Protocol):
    def score(
        self, goal: str, page_title: str, heading_path: str, candidates: list[Link]
    ) -> list[float]:
        """One probability-like score per candidate, same order; only affects fetch order."""
        ...


def keywords(goal: str) -> list[str]:
    return sorted({w for w in _WORD.findall(goal.lower()) if w not in _STOP})


def _stems(goal: str) -> list[str]:
    return sorted({_stem(k) for k in keywords(goal)})


def _ext(path: str) -> str:
    leaf = path.rsplit('/', 1)[-1]
    return '.' + leaf.rsplit('.', 1)[-1].lower() if '.' in leaf else ''


def _stem(word: str) -> str:
    """Strip a plural/participle suffix so 'indexing', 'indexes' and 'index' meet."""
    for suffix, tail in (('ies', 'y'), ('ing', ''), ('es', ''), ('ed', ''), ('s', '')):
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
            return word[: -len(suffix)] + tail
    return word


def _matches(keyword: str, words: set[str]) -> bool:
    """Word match on stems: 'indexing' hits 'indexes', 'sql' does not hit 'mysql'."""
    return any(
        w.startswith(keyword) or (len(w) >= MIN_PREFIX and keyword.startswith(w))
        for w in words
    )


def _weights(kws: list[str], docs: list[set[str]]) -> dict[str, float]:
    """BM25 idf of each keyword over the candidates: 'sql' in most URLs of a SQL docs site
    weighs almost nothing, 'performance' in a few weighs a lot. Keywords no candidate contains
    are left out, so they cannot dilute the ones that can discriminate."""
    n = len(docs)
    if n < MIN_IDF_DOCS:
        return dict.fromkeys(kws, 1.0)
    out = {}
    for k in kws:
        if df := sum(_matches(k, words) for words in docs):
            out[k] = math.log(1 + (n - df + 0.5) / (df + 0.5))
    return out


def is_doc_url(url: str) -> bool:
    return _ext(urlsplit(url).path) not in _NON_DOC_EXT


class RulesScorer:
    """Cheap deterministic ranking: goal keywords, scope prefix, path depth, content type."""

    def __init__(self, goal: str, scope: str | None = None) -> None:
        self.goal = goal
        self.scope = scope or '/'
        self._kw = _stems(goal)

    def hits(self, goal: str, candidates: list[Link]) -> list[float]:
        """Share (0..1) of the goal's terms in each candidate's anchor, path and heading,
        weighted by how rare each term is among these candidates."""
        kws = _stems(goal) if goal and goal != self.goal else self._kw
        words = [
            {
                _stem(w)
                for w in _WORD.findall(
                    f'{c.anchor} {urlsplit(c.url).path} {c.heading}'.lower()
                )
            }
            for c in candidates
        ]
        weights = _weights(kws, words)
        total = sum(weights.values())
        if not total:
            return [0.0] * len(candidates)
        return [
            sum(w for k, w in weights.items() if _matches(k, found)) / total
            for found in words
        ]

    def score(
        self,
        goal: str,
        page_title: str,  # noqa: ARG002 - context for model-backed scorers; rules ignore it
        heading_path: str,  # noqa: ARG002
        candidates: list[Link],
    ) -> list[float]:
        base = self.scope.strip('/').count('/') + 1 if self.scope.strip('/') else 0
        out = []
        for c, hit in zip(candidates, self.hits(goal, candidates), strict=True):
            path = urlsplit(c.url).path
            ext = _ext(path)
            if ext in _NON_DOC_EXT:
                out.append(0.0)
                continue
            extra = (
                max(0, path.strip('/').count('/') + 1 - base) if path.strip('/') else 0
            )
            in_scope = path.startswith(self.scope)
            chrome = hit == 0 and any(
                _CHROME.match(seg) for seg in path.lower().strip('/').split('/')
            )
            score = (
                0.5 * hit
                + 0.2 * in_scope
                + 0.2 / (1 + extra)
                + (0.1 if ext in _DOC_EXT else 0.0)
                - (CHROME_PENALTY if chrome else 0.0)
            )
            out.append(round(max(0.0, min(1.0, score)), 4))
        return out


class GuardedScorer:
    """Runs a model-backed scorer but degrades to rules on any error: order-only, so benign."""

    def __init__(
        self, primary: LinkScorer, fallback: LinkScorer, log: Callable[[str], None]
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.log = log
        self.failed = False

    def score(
        self, goal: str, page_title: str, heading_path: str, candidates: list[Link]
    ) -> list[float]:
        if not self.failed:
            try:
                scores = self.primary.score(goal, page_title, heading_path, candidates)
                if len(scores) == len(candidates):
                    return scores
                raise ValueError('scorer returned a wrong number of scores')
            except Exception as exc:  # noqa: BLE001 - any brain failure must not stop a crawl
                self.failed = True
                self.log(f'warning: --brain scorer failed ({exc!r}); using rules')
        return self.fallback.score(goal, page_title, heading_path, candidates)


def make_scorer(
    goal: str, brain: str, scope: str | None, log: Callable[[str], None]
) -> LinkScorer:
    """RulesScorer, or Laya wrapped in a guard; a missing Laya falls back with a warning."""
    rules = RulesScorer(goal, scope)
    if brain != 'laya':
        return rules
    try:
        laya = importlib.import_module('anything_to_skill.laya.brain')
        return GuardedScorer(laya.LayaScorer(goal), rules, log)
    except Exception as exc:  # noqa: BLE001 - laya is optional and heavy
        log(f'warning: --brain laya unavailable ({exc!r}); using rules')
        return rules


def priority(score: float) -> float:
    return round(score * PRIORITY_SCALE, 3)


class _Links(HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__()
        self.base = base
        self.links: dict[str, Link] = {}
        self._heading = ''
        self._in_heading = False
        self._href: str | None = None
        self._anchor: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ('h1', 'h2', 'h3'):
            self._in_heading, self._heading = True, ''
        elif tag == 'a':
            self._href = dict(attrs).get('href')
            self._anchor = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ('h1', 'h2', 'h3'):
            self._in_heading = False
        elif tag == 'a' and self._href:
            try:
                url = urldefrag(urljoin(self.base, self._href))[0]
                scheme = urlsplit(url).scheme
            except ValueError:  # e.g. href="//[oops": one bad link must not fail the page
                self._href = None
                return
            anchor = ' '.join(''.join(self._anchor).split())
            known = self.links.get(url)
            # A page links the same URL as "Next" in its nav bar and by name in its
            # contents; the name is the one worth scoring.
            if scheme in ('http', 'https') and (
                known is None or len(anchor) > len(known.anchor)
            ):
                self.links[url] = Link(url, anchor, self._heading.strip())
            self._href = None

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading += data
        if self._href is not None:
            self._anchor.append(data)


def extract_links(html: str, base_url: str) -> list[Link]:
    """Absolute, fragment-free links with anchor text and the nearest preceding heading."""
    parser = _Links(base_url)
    parser.feed(html)
    return list(parser.links.values())
