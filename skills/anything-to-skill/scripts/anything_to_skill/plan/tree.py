import argparse
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from anything_to_skill.core.models import EFFORT_BUDGET, Unit
from anything_to_skill.core.store import USER_DROPS_KEY
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.plan.pack import HARD_MAX, Namer, chapters_of, pack_files
from anything_to_skill.plan.priority import goal_keywords, hints, priority, slugify
from anything_to_skill.sources.web.extract import strip_host_boilerplate

MIN_SECTION_FILES = 3
MAX_SECTION_FILES = 25
MAX_SECTIONS = 15
MIN_SUBSECTIONS = 2
NESTED_HINTS = 2
GENERAL = 'general'
VIDEOS = 'videos'
DROP_LIST_MAX = 30
BOILERPLATE_HEAD_LINES = 30
BOILERPLATE_MIN_PAGES = 3
BOILERPLATE_SHARE = 0.25
AUTHORED = [
    {'path': 'SKILL.md', 'purpose': 'hub: when to use, core workflow, routing table'},
    {
        'path': 'references/best-practices.md',
        'purpose': 'top best practices with sources',
    },
    {'path': 'references/examples/*.md', 'purpose': 'grounded worked examples'},
    {'path': 'evals/evals.json', 'purpose': 'task-completion evals'},
    {'path': 'evals/trigger-eval.json', 'purpose': 'description-triggering evals'},
]
LICENSE_NOTE = 'Verbatim mirrored pages are for private use; check each source license before sharing.'


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--overrides', help='judge.json to apply (drops, section moves, kinds)'
    )
    parser.add_argument(
        '--skill-name', help='skill name (default: init --name, else the slug)'
    )
    parser.add_argument(
        '--json', action='store_true', help='print plan.json instead of the tree'
    )


def _int_keys(mapping: dict[str, Any] | None) -> dict[int, Any]:
    return {int(k): v for k, v in (mapping or {}).items()}


def _select(
    units: list[Unit], rank: dict[int, float], effort: str
) -> tuple[list[Unit], list[dict[str, Any]]]:
    """Keep units in rank order until the effort's token budget is spent; smaller ones may still fit."""
    budget = EFFORT_BUDGET.get(effort)
    ordered = sorted(units, key=lambda u: (-rank[u.id], u.id))
    kept: list[Unit] = []
    dropped: list[dict[str, Any]] = []
    used = 0
    for u in ordered:
        if budget is not None and used + u.tokens > budget:
            dropped.append({'id': u.id, 'reason': f'over {effort} budget ({budget} tok)'})
            continue
        used += u.tokens
        kept.append(u)
    return kept, dropped


def _dedupe(
    units: list[Unit], rank: dict[int, float]
) -> tuple[list[Unit], list[dict[str, Any]]]:
    # ponytail: exact-SHA duplicates only, near-duplicate detection (simhash) if mirrors turn out noisy
    best: dict[str, Unit] = {}
    for u in sorted(units, key=lambda u: (-rank[u.id], u.id)):
        if u.sha:
            best.setdefault(u.sha, u)
    dropped = [
        {'id': u.id, 'reason': f'duplicate of {best[u.sha].id}'}
        for u in units
        if u.sha and best[u.sha].id != u.id
    ]
    gone = {d['id'] for d in dropped}
    return [u for u in units if u.id not in gone], dropped


def _video_names(units: list[Unit]) -> dict[int, str]:
    """Unique short name per video: its file stem (or, with chapters, its folder) and frame folder."""
    seen: Counter[str] = Counter()
    out: dict[int, str] = {}
    for u in units:
        if u.kind == 'video':
            stem = hints(u)[-1]
            seen[stem] += 1
            out[u.id] = stem if seen[stem] == 1 else f'{stem}-{seen[stem]}'
    return out


def _sorted(units: list[Unit]) -> list[Unit]:
    return sorted(units, key=lambda u: (hints(u), u.source, u.id))


def _titled(slug: str) -> str:
    return slug.replace('-', ' ').replace('_', ' ').title()


def _host(u: Unit) -> str:
    """Slug of the web host a unit came from, 'www' and the TLD dropped; '' for local files and
    videos (a video merges with docs on the same topic instead of qualifying as another site)."""
    if u.kind == 'video':
        return ''
    host = urlsplit(u.uri).netloc.rpartition('@')[2].split(':')[0]
    labels = [p for p in host.split('.') if p and p != 'www']
    return slugify('-'.join(labels[:-1] or labels))


def _join(prefix: str, name: str) -> str:
    """`prefix-name`, never `x-x` or `x-x-y` when name already starts with the prefix."""
    return name if name == prefix or name.startswith(f'{prefix}-') else f'{prefix}-{name}'


def _inside(parent: str, seg: str) -> bool:
    """Whether path segment `seg` is the section's own key (host-qualified or not)."""
    return parent == seg or parent.endswith(f'-{seg}')


def _subkey(u: Unit, parent: str) -> str:
    """Second-level cluster of a unit inside an oversize section.

    A huge page (it packs into several files) is its own cluster; otherwise the next path
    segment, else the page name's prefix. A page sitting directly under the section's own
    segment belongs to no cluster.
    """
    h = hints(u)
    if u.tokens > HARD_MAX:
        return h[-1]
    if len(h) > 1:
        if not _inside(parent, h[0]):
            return h[0]
        return h[1] if len(h) > NESTED_HINTS else ''
    return h[-1].split('-')[0] if '-' in h[-1] else ''


def _sub_name(
    slug: str, key: str, units: list[Unit], taken: set[str], leftovers: set[str]
) -> str:
    """Name of one cluster of an oversize section.

    A cluster of leftover pages keeps its bare hint; when another section already holds it, that
    is another site's meaning of the same word, so the host qualifies it. Anything else is
    qualified by its parent.
    """
    options = []
    if slug in leftovers:
        hosts = {_host(u) for u in units} - {''}
        options = [key, *(_join(h, key) for h in hosts if len(hosts) == 1)]
    options.append(_join(slug, key))
    return next((n for n in options if n not in taken), options[-1])


def _subsections(
    slug: str,
    units: list[Unit],
    taken: set[str],
    room: int,
    pack: Callable[[list[Unit]], list[dict[str, Any]]],
    leftovers: set[str],
) -> dict[str, list[Unit]] | None:
    """Split an oversize section into clusters worth a folder (3+ files); None when none exist."""
    by_key: dict[str, list[Unit]] = {}
    for u in units:
        by_key.setdefault(_subkey(u, slug), []).append(u)
    big = sorted(
        (k for k, us in by_key.items() if k and len(pack(us)) >= MIN_SECTION_FILES),
        key=lambda k: (-len(by_key[k]), k),
    )[:room]
    if len(big) < MIN_SUBSECTIONS:
        return None
    out: dict[str, list[Unit]] = {}
    for k in sorted(big):
        name = _sub_name(slug, k, by_key[k], taken | set(out), leftovers)
        out[name] = by_key[k]
    rest = [u for u in units if _subkey(u, slug) not in big]
    if rest:
        out[slug] = rest
    return out


def _layout(
    units: list[Unit],
    sections_of: dict[int, str],
    texts: dict[int, str],
    boilerplate: frozenset[str] = frozenset(),
    keywords: frozenset[str] = frozenset(),
    names: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """Group by first hint segment, fold thin sections into general, cap section count, split big ones.

    A video with chapters is set apart: it gets a folder of its own (never folded or merged), one
    file per chapter. A chapterless video is an ordinary page whose leftover section is `videos`.

    Sites are kept apart where words collide: two web hosts sharing a first segment (or both
    leaving pages to `general`) each get a host-qualified section. Judge moves and non-web
    sources still merge by slug.
    """

    def pack(us: list[Unit]) -> list[dict[str, Any]]:
        return pack_files(
            us, texts, names=names, boilerplate=boilerplate, keywords=keywords
        )

    owned = [u for u in units if u.kind == 'video' and chapters_of(texts[u.id])]
    units = [u for u in units if u not in owned]
    multi_host = len({_host(u) for u in units} - {''}) > 1

    def leftover(u: Unit) -> str:
        if u.kind == 'video':
            return VIDEOS
        return _join(_host(u), GENERAL) if multi_host and _host(u) else GENERAL

    leftovers = {leftover(u) for u in units}
    keys = {
        u.id: sections_of.get(u.id) or (hints(u)[0] if len(hints(u)) > 1 else leftover(u))
        for u in units
    }
    hosts_of: dict[str, set[str]] = {}
    for u in units:
        hosts_of.setdefault(keys[u.id], set()).add(_host(u))
    explicit = set(sections_of.values())
    groups: dict[str, list[Unit]] = {}
    for u in units:
        key = keys[u.id]
        if key not in explicit | leftovers and len(hosts_of[key] - {''}) > 1 and _host(u):
            key = _join(_host(u), key)
        groups.setdefault(key, []).append(u)
    packed = {s: pack(us) for s, us in groups.items()}

    def total() -> int:
        return sum(math.ceil(len(f) / MAX_SECTION_FILES) for f in packed.values())

    while True:
        others = [s for s in packed if s not in leftovers]
        fold = [s for s in others if len(packed[s]) < MIN_SECTION_FILES]
        if not fold and others and total() > MAX_SECTIONS:
            fold = [min(others, key=lambda s: (len(packed[s]), s))]
        if not fold:
            break
        for s in fold:
            for u in groups.pop(s):
                groups.setdefault(leftover(u), []).append(u)
            del packed[s]
        for g in leftovers & groups.keys():
            groups[g] = _sorted(groups[g])
            packed[g] = pack(groups[g])

    for slug in [s for s in packed if len(packed[s]) > MAX_SECTION_FILES]:
        room = max(MAX_SECTIONS - len(packed), 0)
        subs = _subsections(slug, groups[slug], set(packed), room, pack, leftovers)
        if subs:
            del packed[slug], groups[slug]
            for name, us in subs.items():
                groups[name] = us
                packed[name] = pack(us)

    def section(
        slug: str, title: str, files: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        chunks = [
            files[i : i + MAX_SECTION_FILES]
            for i in range(0, len(files), MAX_SECTION_FILES)
        ]
        return [
            {
                'slug': f'{slug}-{i}' if len(chunks) > 1 else slug,
                'title': f'{title} {i}' if len(chunks) > 1 else title,
                'files': chunk,
            }
            for i, chunk in enumerate(chunks, 1)
        ]

    sections = []
    for slug in sorted(s for s in packed if s not in leftovers):
        sections += section(slug, _titled(slug), packed[slug])
    taken = set(packed)
    folders = []
    for u in owned:
        slug = (names or {}).get(u.id) or hints(u)[-1]
        while slug in taken:
            slug += '-video'
        taken.add(slug)
        folders += section(slug, u.title or _titled(slug), pack([u]))
    sections += sorted(folders, key=lambda s: s['slug'])
    for slug in sorted(leftovers & packed.keys()):
        sections += section(slug, _titled(slug), packed[slug])
    return sections


def _finish_files(sections: list[dict[str, Any]]) -> None:
    """Give every file its path; a name that starts with its folder's whole name drops that prefix
    (`app-psql/app-psql-usage.md` reads `app-psql/usage.md`)."""
    for section in sections:
        folder = section['slug']
        name_for = Namer()
        for f in section['files']:
            stem = f.pop('name').removesuffix('.md')
            f['path'] = f'{folder}/{name_for(stem.removeprefix(folder + "-") or stem)}'


def _repeated_lines(units: list[Unit], texts: dict[int, str]) -> frozenset[str]:
    """Top-of-page lines that repeat across one host's pages: banners, nav, version pickers."""
    by_host: dict[str, list[Unit]] = {}
    for u in units:
        by_host.setdefault(urlsplit(u.uri).netloc or u.source, []).append(u)
    out: set[str] = set()
    for group in by_host.values():
        need = max(BOILERPLATE_MIN_PAGES, math.ceil(BOILERPLATE_SHARE * len(group)))
        seen: Counter[str] = Counter()
        for u in group:
            lines = texts[u.id].splitlines()[:BOILERPLATE_HEAD_LINES]
            seen.update({' '.join(ln.split()) for ln in lines if ln.strip()})
        out |= {ln for ln, n in seen.items() if n >= need}
    return frozenset(out)


def build_plan(
    units: list[Unit],
    goal: str,
    effort: str,
    overrides: dict[str, Any] | None = None,
    *,
    texts: dict[int, str],
    user_drops: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Pure function: units (+ judge overrides) to plan.json content. See plan.md for the schema.

    `texts` maps unit id to its stored markdown. Only kind != 'seed' units are planned. Units not
    yet `done` are counted per source and status in `not_ingested`; `dropped` holds only
    deliberate drops (user, judge, duplicate, budget). `user_drops` (id to reason) are honoured at
    every effort and even in annotate-only mode, whether or not the page was fetched.
    """
    ov = overrides or {}
    user_drops = user_drops or {}
    annotate_only = bool(ov.get('annotate_only'))
    judge_drop = (
        {}
        if annotate_only or effort == 'complete'
        else {d['id']: d['reason'] for d in ov.get('drop', [])}
    )
    moves = {} if annotate_only else _int_keys(ov.get('section'))
    kinds = _int_keys(ov.get('kind'))

    corpus = [u for u in units if u.kind != 'seed']
    dropped = [
        {'id': u.id, 'reason': f'dropped: {user_drops[u.id]}'}
        for u in corpus
        if u.id in user_drops
    ]
    corpus = [u for u in corpus if u.id not in user_drops]
    not_ingested: dict[str, dict[str, int]] = {}
    for u in corpus:
        if u.status != 'done' or u.id not in texts:
            by = not_ingested.setdefault(u.source, {})
            by[u.status] = by.get(u.status, 0) + 1
    live = [u for u in corpus if u.status == 'done' and u.id in texts]
    dropped += [
        {'id': u.id, 'reason': f'judge: {judge_drop[u.id]}'}
        for u in live
        if u.id in judge_drop
    ]
    live = [u for u in live if u.id not in judge_drop]
    boilerplate = _repeated_lines(live, texts)

    keywords = goal_keywords(goal)
    rank = {
        u.id: u.priority + priority(u, keywords, bool(u.hint.get('llms'))) for u in live
    }
    live, dup = _dedupe(live, rank)
    kept, over = _select(live, rank, effort)
    dropped += dup + over
    kept = _sorted(
        [
            replace(u, hint={**u.hint, 'kind': kinds[u.id]}) if u.id in kinds else u
            for u in kept
        ]
    )

    videos = _video_names(kept)
    sections = _layout(kept, moves, texts, boilerplate, frozenset(keywords), videos)
    _finish_files(sections)

    files = [f for s in sections for f in s['files']]
    by_source: dict[str, dict[str, int]] = {}
    for u in kept:
        info = by_source.setdefault(u.source, {'units': 0, 'tokens': 0})
        info['units'] += 1
        info['tokens'] += u.tokens
    return {
        'version': 1,
        'goal': goal,
        'effort': effort,
        'sections': sections,
        'videos': {str(uid): slug for uid, slug in videos.items()},
        'dropped': sorted(dropped, key=lambda d: d['id']),
        'not_ingested': not_ingested,
        'authored': AUTHORED,
        'stats': {
            'units_kept': len(kept),
            'units_dropped': len(dropped),
            'units_not_ingested': sum(sum(by.values()) for by in not_ingested.values()),
            'sections': len(sections),
            'files': len(files),
            'tokens': sum(f['tokens'] for f in files),
            'budget': EFFORT_BUDGET.get(effort),
            'by_source': by_source,
        },
    }


def _plural(n: int, word: str) -> str:
    return f'{n} {word}' if n == 1 else f'{n} {word}s'


def drop_kind(reason: str) -> str:
    """Reason without its per-unit detail: 'duplicate of 9' and 'duplicate of 4' both read 'duplicate'."""
    return re.sub(r'\s+of \d+|\s*[:(].*', '', reason).strip()


def drop_lines(
    dropped: list[dict[str, Any]], label: Callable[[int], str], limit: int = DROP_LIST_MAX
) -> list[str]:
    """One line per drop up to `limit`, then per-kind counts for the rest."""
    lines = [f'{label(d["id"])}: {d["reason"]}' for d in dropped[:limit]]
    rest = Counter(drop_kind(d['reason']) for d in dropped[limit:])
    if rest:
        lines.append(
            f'... and {sum(rest.values())} more ('
            + ', '.join(f'{n} {k}' for k, n in rest.most_common())
            + ')'
        )
    return lines


def not_ingested_lines(plan: dict[str, Any]) -> list[str]:
    return [
        f'{source}: ' + ', '.join(f'{n} {status}' for status, n in sorted(by.items()))
        for source, by in sorted(plan.get('not_ingested', {}).items())
    ]


def render_tree(plan: dict[str, Any], units: dict[int, Unit] | None = None) -> str:
    """Human view for the approve-tree gate: folders, files with token counts, drops, authored files."""
    stats = plan['stats']
    lines = [
        f'skill name: {plan.get("skill_name", "?")}',
        f'{_plural(stats["files"], "file")} in {_plural(stats["sections"], "section")}, ~{stats["tokens"]} tok'
        f' ({_plural(stats["units_kept"], "page")} kept, {stats["units_dropped"]} dropped), effort={plan["effort"]}',
        '',
        'references/',
    ]
    for s in plan['sections']:
        lines.append(
            f'  {s["slug"]}/ ({len(s["files"])} files, ~{sum(f["tokens"] for f in s["files"])} tok)'
        )
        lines += [
            f'    {f["path"].rsplit("/", 1)[-1]}  ~{f["tokens"]} tok [{f["kind"]}]'
            for f in s['files']
        ]
    if plan['dropped']:
        lines += ['', 'dropped:']
        lines += [
            f'  {ln}'
            for ln in drop_lines(
                plan['dropped'],
                lambda i: units[i].uri if units and i in units else f'#{i}',
            )
        ]
    if plan.get('not_ingested'):
        lines += ['', 'not ingested (never fetched, not in the skill):']
        lines += [f'  {ln}' for ln in not_ingested_lines(plan)]
    lines += [
        '',
        'to be authored:',
        *(f'  {a["path"]}  {a["purpose"]}' for a in plan['authored']),
    ]
    lines += ['', f'note: {LICENSE_NOTE}']
    return '\n'.join(lines)


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py plan`: read the store, call build_plan, write ws.plan_path."""
    try:
        overrides = (
            json.loads(Path(args.overrides).read_text('utf-8'))
            if args.overrides
            else None
        )
    except (OSError, ValueError) as exc:
        print(f'a2s: cannot read --overrides {args.overrides}: {exc}', file=sys.stderr)
        return 2
    with ws.open_store() as store:
        strip_host_boilerplate(store)
        units = store.units()
        texts = {
            u.id: store.read_markdown(u.id)
            for u in units
            if u.status == 'done' and u.kind != 'seed'
        }
        plan = build_plan(
            units,
            store.get_meta('goal', ''),
            store.get_meta('effort', 'standard'),
            overrides,
            texts=texts,
            user_drops=_int_keys(store.get_meta(USER_DROPS_KEY)),
        )
        plan['skill_name'] = args.skill_name or store.get_meta('name') or ws.slug
    ws.plan_path.write_text(json.dumps(plan, indent=2) + '\n', 'utf-8')
    print(
        json.dumps(plan, indent=2)
        if args.json
        else render_tree(plan, {u.id: u for u in units})
    )
    return 0
