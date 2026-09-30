import re
from http import HTTPStatus
from urllib.parse import urldefrag, urljoin, urlsplit

from defusedxml import ElementTree as SafeET

from anything_to_skill.core.models import Unit
from anything_to_skill.core.ssrf import SSRFError
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Ctx
from anything_to_skill.sources.web.fetch import (
    MAX_LIST_BYTES,
    FetchError,
    Net,
    RobotsDisallowedError,
)
from anything_to_skill.sources.web.frontier import (
    PRIORITY_SCALE,
    Link,
    LinkScorer,
    RulesScorer,
    is_doc_url,
    make_scorer,
    priority,
)
from anything_to_skill.sources.web.throttle import HostBlockedError

NAME = 'web'
LLMS_PATHS = ('/llms.txt', '/.well-known/llms.txt')
LLMS_PRIORITY = 50.0
MAX_SITEMAPS = 50
MAX_URLS = 20000
SCOPES_KEY = 'web.scopes'
LOCALE_SKIPPED_KEY = 'web.locale_skipped'
SITEMAP_RANK_KEY = 'web.sitemap_rank'
RANKED_BY_KEY = 'web.ranked_by'
LAYA_SHORTLIST = 100
RANK_N = 10
# Rank fusion 1/(RRF_K + rules rank) + LAYA_WEIGHT/(RRF_K + laya rank) inside the rules
# shortlist: Laya breaks the many rules ties and nudges, but a page has to be ranked twice
# as far by Laya as by rules to move, so it cannot outweigh them. On the 1148 postgres docs
# URLs the top 10 keeps 8 of the rules' 10; adding Laya's score (centred) at the same weight
# kept 4.
RRF_K = 10
LAYA_WEIGHT = 0.5
# Link-graph boost (see boost_linked). A link carries LINK_BASE of its page's relevance even
# with no goal term in its anchor ("Using EXPLAIN" from performance-tips), the rest when the
# anchor names one. Replaying the postgres docs crawl (rules ranking, real page links, 40 to
# 200 fetches over two seeds), power 3 and power 1 fetch the same share of relevant pages, but
# power 3 fetches using-explain 13th instead of 75th. A page linking more than
# FULL_SHARE_LINKS pending pages (a "see also" list) gives each of them proportionally less.
LINK_BASE = 0.85
MAX_BOOST = 0.97
BOOST_POWER = 3
FULL_SHARE_LINKS = 10
MAX_ANCHORS = 3
ANCHOR_CHARS = 80
# Nav-bar anchors say nothing about the target; a link that has only these is no evidence.
_NAV_ANCHORS = frozenset(['next', 'prev', 'previous', 'up', 'home', 'top', 'current'])
AFFINITY_WEIGHT = 0.05  # a tie-break between equally on-goal pages, never a match signal
# Path segments that are language codes on doc sites (a set, so "go" or "db" stay pages).
_LANGS = frozenset(
    [
        'ar',
        'bg',
        'bn',
        'ca',
        'cs',
        'da',
        'de',
        'el',
        'en',
        'es',
        'et',
        'fa',
        'fi',
        'fr',
        'he',
        'hi',
        'hr',
        'hu',
        'id',
        'it',
        'ja',
        'ko',
        'lt',
        'lv',
        'nl',
        'no',
        'pl',
        'pt',
        'ro',
        'ru',
        'sk',
        'sl',
        'sr',
        'sv',
        'th',
        'tr',
        'uk',
        'vi',
        'zh',
    ]
)
_LOCALE = re.compile(r'([a-z]{2})(?:[-_][a-z]{2,4})?')
_LEAF_NOISE = frozenset(['html', 'htm', 'php', 'md', 'index'])
_MD_LINK = re.compile(r'\[[^\]]*\]\(\s*<?([^)\s>]+)>?[^)]*\)')
_GROUP = re.compile(r'^#{1,6}\s+(.+?)\s*$')
_SOFT = (FetchError, RobotsDisallowedError, SSRFError, HostBlockedError)


def normalize(url: str, base: str = '') -> str:
    """Absolute, fragment-free, lowercase-host form; '' for a URL urllib cannot parse (a
    malformed bracketed host in a third-party sitemap, say), which callers drop."""
    try:
        parts = urlsplit(urldefrag(urljoin(base, url.strip()))[0])
    except ValueError:
        return ''
    return parts._replace(netloc=parts.netloc.lower()).geturl()


def normalize_scope(seed_uri: str, scope: str | None) -> str:
    """A path prefix. Default: the seed's directory, or the whole site for a bare origin."""
    if scope:
        path = urlsplit(scope).path if '://' in scope else scope
        return path if path.startswith('/') else f'/{path}'
    path = urlsplit(seed_uri).path
    if path in ('', '/'):
        return '/'
    return path if path.endswith('/') else path.rsplit('/', 1)[0] + '/'


def in_scope(url: str, host: str, scope: str) -> bool:
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return (
        parts.netloc.lower() == host and parts.path.startswith(scope) and is_doc_url(url)
    )


def locale_of(url: str) -> str | None:
    """The language code among a URL's first two path segments ('de', 'pt-br'), if any."""
    for seg in urlsplit(url).path.strip('/').lower().split('/')[:2]:
        if (m := _LOCALE.fullmatch(seg)) and m.group(1) in _LANGS:
            return seg.replace('_', '-')
    return None


def _language(locale: str | None) -> str:
    return (locale or 'en').split('-')[0]


def same_locale(url: str, seed_uri: str) -> bool:
    """A URL without a locale segment counts as English, so an /en/ page matches it."""
    return _language(locale_of(url)) == _language(locale_of(seed_uri))


def parse_alternate_langs(xml: str) -> dict[str, str]:
    """href -> hreflang of every xhtml:link alternate in a sitemap (x-default excluded)."""
    try:
        root = SafeET.fromstring(xml)
    except (SafeET.ParseError, ValueError):
        return {}
    return {
        el.get('href', '').strip(): el.get('hreflang', '').lower()
        for el in root.iter()
        if el.tag.rsplit('}', 1)[-1] == 'link'
        and el.get('href')
        and el.get('hreflang', 'x-default').lower() != 'x-default'
    }


def parse_llms(text: str, base: str) -> list[tuple[str, str]]:
    """(url, group heading) for each markdown link in an llms.txt, in file order."""
    out, group = [], ''
    for line in text.splitlines():
        if m := _GROUP.match(line):
            group = m.group(1)
        out += [
            (url, group) for u in _MD_LINK.findall(line) if (url := normalize(u, base))
        ]
    return out


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """(page urls, child sitemap urls); a sitemapindex yields only children."""
    try:
        root = SafeET.fromstring(xml)
    except (SafeET.ParseError, ValueError):
        return [], []
    locs = [
        (el.text or '').strip()
        for el in root.iter()
        if el.tag.rsplit('}', 1)[-1] == 'loc' and el.text
    ]
    if root.tag.rsplit('}', 1)[-1] == 'sitemapindex':
        return [], locs
    return locs, []


def crawl_scope(store: Store, uri: str) -> tuple[str, str] | None:
    """(scope prefix, discovery mode) of the seed crawl this uri belongs to."""
    parts = urlsplit(uri)
    site = f'{parts.scheme}://{parts.netloc.lower()}'
    for origin, scope, mode in store.get_meta(SCOPES_KEY, []):
        if site == origin and parts.path.startswith(scope):
            return scope, mode
    return None


def _record_scope(ctx: Ctx, origin: str, scope: str, mode: str) -> None:
    known = ctx.store.get_meta(SCOPES_KEY, [])
    entry = [origin, scope, mode]
    if entry not in known:
        ctx.store.set_meta(SCOPES_KEY, [*known, entry])


def _retype_seed(ctx: Ctx, seed_uri: str) -> None:
    """The seed URL is itself a page: turn its seed unit into a pending page unit.

    Units are unique by uri, so a separate page unit for the same URL would collide
    with the seed (and swallow it if a sitemap lists the same URL).
    """
    store = ctx.store
    unit = store.get_by_uri(seed_uri)
    if unit is None:
        store.add_unit('web', seed_uri, priority=100.0)
    elif unit.kind == 'seed':
        store.set_kind(unit.id, 'page')


async def _text(net: Net, url: str) -> str | None:
    try:
        res = await net.get(url, max_bytes=MAX_LIST_BYTES)
    except _SOFT:
        return None
    ctype = res.content_type.lower()
    if res.status != HTTPStatus.OK or 'html' in ctype:
        return None
    return res.body


async def _llms(net: Net, origin: str) -> list[tuple[str, str]]:
    for path in LLMS_PATHS:
        if (body := await _text(net, origin + path)) and (
            links := parse_llms(body, origin + path)
        ):
            return links
    return []


async def _sitemap_urls(net: Net, origin: str) -> tuple[list[str], dict[str, str]]:
    """(page urls, href -> hreflang of the sitemaps' language alternates)."""
    await net.ensure_robots(origin)
    queue = net.robots.sitemaps(origin) or [f'{origin}/sitemap.xml']
    seen, urls, alternates = set(), [], {}
    while queue and len(seen) < MAX_SITEMAPS and len(urls) < MAX_URLS:
        sitemap = queue.pop(0)
        if sitemap in seen:
            continue
        seen.add(sitemap)
        if body := await _text(net, sitemap):
            pages, children = parse_sitemap(body)
            urls += pages
            alternates |= {
                n: lang
                for h, lang in parse_alternate_langs(body).items()
                if (n := normalize(h))
            }
            queue += [n for c in children if (n := normalize(c, sitemap))]
    return urls, alternates


def _rank_priorities(n: int, base: float = 0.0) -> list[float]:
    """Priority by rank alone, so equal ranks of different seeds tie and the claim order
    round-robins between them instead of letting one seed's scores swamp the others."""
    return [round(base + PRIORITY_SCALE * (1 - i / MAX_URLS), 4) for i in range(n)]


def _seed_affinity(seed_uri: str, url: str, scope: str) -> float:
    """0..1 closeness of a page to the seed page: shared name tokens and shared sub-directory."""
    seed_path, path = urlsplit(seed_uri).path, urlsplit(url).path

    def tokens(p: str) -> set[str]:
        leaf = p.rstrip('/').rsplit('/', 1)[-1]
        return {
            t for t in re.split(r'[^a-z0-9]+', leaf.lower()) if len(t) > 1
        } - _LEAF_NOISE

    seed_tokens = tokens(seed_path)
    shared_name = (
        len(seed_tokens & tokens(path)) / len(seed_tokens) if seed_tokens else 0.0
    )
    seed_dir, own_dir = seed_path.rsplit('/', 1)[0], path.rsplit('/', 1)[0]
    shared_dir = own_dir.startswith(seed_dir) and len(seed_dir) > len(scope.rstrip('/'))
    return 0.5 * shared_name + 0.5 * shared_dir


def unit_link(unit: Unit) -> Link:
    """A pending page as the scorers see it: its URL plus the anchors pages linked it with."""
    return Link(unit.uri, ' / '.join(unit.hint.get('anchors', [])))


def _rank_sitemap(
    ctx: Ctx, links: list[Link], seed_uri: str, scope: str, brain: str
) -> list[str]:
    """Sitemap urls best first: goal keywords and closeness to the seed page, plus Laya
    re-ordering the rules shortlist with --brain laya. Logs how the two rankings compare
    (overlap only: nothing here knows which pages are truly relevant) in the workspace meta."""
    urls = [link.url for link in links]
    rules = RulesScorer(ctx.goal, scope).score(ctx.goal, '', '', links)
    blended = [
        s + AFFINITY_WEIGHT * _seed_affinity(seed_uri, u, scope)
        for s, u in zip(rules, urls, strict=True)
    ]
    order = sorted(range(len(urls)), key=lambda i: (-blended[i], i))
    by_rules = [urls[i] for i in order]
    scorer = make_scorer(ctx.goal, brain, scope, ctx.log)
    if brain != 'laya' or isinstance(scorer, RulesScorer):
        _record_ranked_by(ctx, seed_uri, 'rules')
        return by_rules
    short = order[:LAYA_SHORTLIST]
    laya = scorer.score(ctx.goal, '', '', [links[i] for i in short])
    laya_rank = {
        p: r for r, p in enumerate(sorted(range(len(short)), key=lambda p: -laya[p]))
    }
    fused = sorted(
        range(len(short)),
        key=lambda p: (-(1 / (RRF_K + p) + LAYA_WEIGHT / (RRF_K + laya_rank[p])), p),
    )
    by_laya = [urls[order[p]] for p in fused] + by_rules[len(short) :]
    ctx.store.set_meta(
        SITEMAP_RANK_KEY,
        {
            **(ctx.store.get_meta(SITEMAP_RANK_KEY) or {}),
            seed_uri: {
                'n': RANK_N,
                'candidates': len(urls),
                'shortlist': len(short),
                'overlap': len(set(by_rules[:RANK_N]) & set(by_laya[:RANK_N])) / RANK_N,
            },
        },
    )
    _record_ranked_by(ctx, seed_uri, 'laya')
    return by_laya


def _record_ranked_by(ctx: Ctx, seed_uri: str, brain: str) -> None:
    known = ctx.store.get_meta(RANKED_BY_KEY) or {}
    ctx.store.set_meta(RANKED_BY_KEY, {**known, seed_uri: brain})


def rerank_pending(ctx: Ctx, brain: str) -> int:
    """Re-rank each seed's still-pending sitemap pages with `brain` when they were ranked by
    the cheaper rules (discover-only ran without Laya). Returns the number of seeds re-ranked.

    Priorities restart at the top rank of the pending set, like a fresh discovery, so seeds
    keep round-robining. Pages already fetched are left alone.
    """
    if brain != 'laya':
        return 0
    store = ctx.store
    ranked_by = {
        # workspaces discovered before ranked_by existed: every sitemap seed was ranked by rules
        **{
            i['input']: 'rules'
            for i in store.get_meta('inputs', [])
            if i['source'] == 'web'
            and (found := crawl_scope(store, i['input']))
            and found[1] == 'sitemap'
        },
        **(store.get_meta(RANKED_BY_KEY) or {}),
    }
    redone = 0
    for seed_uri, used in ranked_by.items():
        if used == brain or not (seed := store.get_by_uri(seed_uri)):
            continue
        host = urlsplit(seed_uri).netloc.lower()
        scope = normalize_scope(seed_uri, seed.meta.get('scope'))
        pending = [
            u
            for u in store.units(source='web', status='pending')
            if u.hint.get('sitemap') and in_scope(u.uri, host, scope)
        ]
        if not pending:
            continue
        by_uri = {u.uri: u for u in pending}
        ranked = _rank_sitemap(
            ctx, [unit_link(u) for u in pending], seed_uri, scope, brain
        )
        for uri, prio in zip(ranked, _rank_priorities(len(ranked)), strict=True):
            store.set_priority(by_uri[uri].id, prio)
        redone += 1
    return redone


def _add_ranked(ctx: Ctx, items: list[tuple[str, dict]], *, base: float = 0.0) -> int:
    """Add (url, hint) units in the given order, which becomes their priority (per seed)."""
    items = list({url: (url, hint) for url, hint in items}.values())[:MAX_URLS]
    added = 0
    for (url, hint), prio in zip(items, _rank_priorities(len(items), base), strict=True):
        added += ctx.store.get_by_uri(url) is None
        ctx.store.add_unit('web', url, priority=prio, hint=hint)
    return added


def _drop_other_locales(
    ctx: Ctx, seed_uri: str, urls: list[str], alternates: dict[str, str]
) -> list[str]:
    """Keep the seed's language: no other locale path segment, no hreflang alternate of another
    language. The skipped count is recorded per seed."""
    seed_lang = _language(locale_of(seed_uri))
    kept = [
        u
        for u in urls
        if same_locale(u, seed_uri)
        and _language(alternates.get(u) or seed_lang) == seed_lang
    ]
    if skipped := len(urls) - len(kept):
        ctx.log(f'seed {seed_uri}: skipped {skipped} other-locale pages')
        known = ctx.store.get_meta(LOCALE_SKIPPED_KEY) or {}
        ctx.store.set_meta(LOCALE_SKIPPED_KEY, {**known, seed_uri: skipped})
    return kept


async def discover(
    ctx: Ctx, seed_uri: str, scope: str | None, net: Net, brain: str = 'rules'
) -> int:
    """Expand a seed into pending page units (llms.txt, sitemap, then BFS); return count added.

    The first source that yields in-scope URLs wins. With none, the crawl falls back to
    BFS: only the seed page is queued here and run() feeds the frontier from each
    fetched page's links. Raises SSRFError when the seed itself is not fetchable.
    """
    await net.check(seed_uri)
    parts = urlsplit(seed_uri)
    host = parts.netloc.lower()
    origin = f'{parts.scheme}://{host}'
    scope = normalize_scope(seed_uri, scope)

    groups = dict(await _llms(net, origin))
    llms = _drop_other_locales(
        ctx, seed_uri, [u for u in groups if in_scope(u, host, scope)], {}
    )
    if llms:
        hints = [
            (u, {'llms': True, 'group': groups[u]} if groups[u] else {'llms': True})
            for u in llms
        ]
        added = _add_ranked(ctx, hints, base=LLMS_PRIORITY)
        _record_scope(ctx, origin, scope, 'llms')
        _retype_seed(ctx, seed_uri)
        return added
    urls, alternates = await _sitemap_urls(net, origin)
    pages = _drop_other_locales(
        ctx,
        seed_uri,
        [u for u in map(normalize, urls) if in_scope(u, host, scope)],
        alternates,
    )
    if pages:
        ranked = _rank_sitemap(
            ctx, [Link(u) for u in dict.fromkeys(pages)], seed_uri, scope, brain
        )
        added = _add_ranked(ctx, [(u, {'sitemap': True}) for u in ranked])
        _record_scope(ctx, origin, scope, 'sitemap')
        _retype_seed(ctx, seed_uri)
        return added
    _record_scope(ctx, origin, scope, 'bfs')
    _retype_seed(ctx, seed_uri)
    return 0


def follow_links(
    ctx: Ctx,
    parent_id: int,
    depth: int,
    links: list[Link],
    scorer: LinkScorer,
    scope: str,
    page_title: str,
    *,
    max_depth: int,
    max_queue: int,
) -> int:
    """BFS step: queue a page's unseen in-scope links, best-scored first in the frontier."""
    if depth >= max_depth:
        return 0
    store = ctx.store
    parent_uri = store.get(parent_id).uri
    host = urlsplit(parent_uri).netloc.lower()
    candidates = {
        n: Link(n, link.anchor, link.heading)
        for link in links
        if in_scope(link.url, host, scope)
        and same_locale(link.url, parent_uri)
        and (n := normalize(link.url))
    }
    fresh = [link for url, link in candidates.items() if store.get_by_uri(url) is None]
    room = max_queue - store.counts().get('web', {}).get('pending', 0)
    fresh = fresh[: max(0, room)]
    if not fresh:
        return 0
    scores = scorer.score(ctx.goal, page_title, page_title, fresh)
    for link, score in zip(fresh, scores, strict=True):
        store.add_unit(
            'web',
            link.url,
            depth=depth + 1,
            parent=parent_id,
            priority=priority(score),
            hint={'bfs': True},
        )
    return len(fresh)


def _anchor(text: str) -> str:
    anchor = ' '.join(text.split())[:ANCHOR_CHARS]
    return '' if anchor.lower() in _NAV_ANCHORS else anchor


def boost_linked(
    ctx: Ctx, page: Unit, page_title: str, links: list[Link], scope: str
) -> int:
    """Promote the pending listed pages (sitemap or llms.txt) that a fetched page links to,
    and remember the anchor texts on them for the scorers. Returns how many were linked.

    Sitemap ranking sees only URLs, so a page like using-explain (linked from
    performance-tips, no goal word in its URL) starts hundreds of places down. Evidence is
    the linking page's relevance (share of the goal's terms in its title and URL, relative to
    the best page in the list, squared so a mediocre parent counts little), spread over its
    links, times the link's own (LINK_BASE plus the share its anchor and URL carry). Evidence
    accumulates per page and shrinks its place in its own seed's list to a power of what is
    left. The list's priorities are only permuted, so seeds keep their fair share of the crawl.
    """
    store = ctx.store
    host = urlsplit(page.uri).netloc.lower()
    group = sorted(
        (
            u
            for u in store.units(source='web', status='pending')
            if (u.hint.get('sitemap') or u.hint.get('llms'))
            and u.id != page.id
            and in_scope(u.uri, host, scope)
        ),
        key=lambda u: (-u.priority, u.id),
    )
    best: dict[str, str] = {}
    for link in links:
        target = normalize(link.url)
        if (anchor := _anchor(link.anchor)) and target != page.uri:
            best[target] = max(best.get(target, ''), anchor, key=len)
    linked = [i for i, u in enumerate(group) if u.uri in best]
    if not linked:
        return 0
    names = [list(u.hint.get('anchors', [])) for u in group]
    for i in linked:
        names[i] = [*dict.fromkeys([*names[i], best[group[i].uri]])][:MAX_ANCHORS]
    pool = [Link(page.uri, '', page_title)] + [
        Link(u.uri, ' / '.join(n)) for u, n in zip(group, names, strict=True)
    ]
    hits = RulesScorer(ctx.goal, scope).hits(ctx.goal, pool)
    top = max(hits) or 1.0
    share = min(1.0, FULL_SHARE_LINKS / len(linked))
    place = [float(i + 1) for i in range(len(group))]
    for i in linked:
        u = group[i]
        before = u.hint.get('boost', 0.0)
        evidence = (
            share
            * (hits[0] / top) ** 2
            * (LINK_BASE + (1 - LINK_BASE) * hits[i + 1] / top)
        )
        after = max(before, min(MAX_BOOST, 1 - (1 - before) * (1 - evidence)))
        place[i] = (i + 1) * ((1 - after) / (1 - before)) ** BOOST_POWER
        store.set_hint(u.id, {**u.hint, 'anchors': names[i], 'boost': round(after, 4)})
    moved = sorted(range(len(group)), key=lambda i: (place[i], i))
    for i, priority_ in zip(moved, (u.priority for u in group), strict=True):
        if group[i].priority != priority_:
            store.set_priority(group[i].id, priority_)
    return len(linked)
