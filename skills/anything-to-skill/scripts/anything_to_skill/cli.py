import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from urllib.parse import urldefrag, urlsplit

from anything_to_skill import sources
from anything_to_skill.compact import (
    brief as compact_brief,
    freeze as compact_freeze,
    gate as compact_gate,
    swap as compact_swap,
    verify as compact_verify,
)
from anything_to_skill.core.models import EFFORT_BUDGET, Unit, source_label
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Ctx, Workspace, WorkspaceError
from anything_to_skill.emit import verify, write
from anything_to_skill.plan import brief, tree

DEFAULT_TOKENS = {'page': 2500, 'video': 6000, 'file': 4000}
RECENT_THROTTLE_EVENTS = 50
AUTHORING_TOKENS = {'quick': 6000, 'standard': 12000, 'complete': 20000}
DOWNLOADS = {
    'youtube': 'whisper model (0.1-3 GB), only for videos without captions',
    'local': 'docling models (~1 GB), only for PDF/DOCX/PPTX/EPUB/images',
}
REQUEUE_STATUSES = ('pending', 'needs_asr')
LAYA_DOWNLOAD = 'Laya model (843 MB), only for the judge, --brain laya and verify --laya'


def _workspace_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--slug', help='workspace name; optional when only one exists')
    parser.add_argument(
        '--base', type=Path, help='workspaces dir (default ./.cc-arsenal/a2s)'
    )


def _find(args: argparse.Namespace) -> Workspace:
    return Workspace.find(args.slug, args.base)


def _emit(data: object, as_json: bool, text: str) -> None:
    print(json.dumps(data, indent=2) if as_json else text)


def cmd_init(args: argparse.Namespace) -> int:
    ws = Workspace.create(args.slug, args.base)
    with ws.open_store() as store:
        if store.get_meta('effort') is None:
            store.set_meta('effort', 'standard')
        for key in ('goal', 'effort', 'out', 'name', 'instructions'):
            value = getattr(args, key)
            if value is not None:
                store.set_meta(key, value)
    print(json.dumps({'slug': ws.slug, 'dir': str(ws.dir)}))
    return 0


def cmd_detect(args: argparse.Namespace) -> int:
    rows = []
    for arg in args.inputs:
        hit = sources.route(arg)
        rows.append(
            {
                'input': arg,
                'source': hit[0] if hit else None,
                'score': hit[1] if hit else 0,
            }
        )
    _emit(
        rows,
        args.json,
        '\n'.join(f'{r["source"] or "none"}\t{r["score"]}\t{r["input"]}' for r in rows),
    )
    return 0


def _normalize(source: str, arg: str) -> str:
    if source == 'local':
        return str(Path(arg).expanduser().resolve())
    return urldefrag(arg.strip())[0]


def cmd_seed(args: argparse.Namespace) -> int:
    inputs = list(args.inputs)
    if args.urls:
        try:
            text = (
                sys.stdin.read()
                if args.urls == '-'
                else Path(args.urls).read_text('utf-8')
            )
        except (OSError, ValueError) as exc:
            print(f'a2s: cannot read --urls {args.urls}: {exc}', file=sys.stderr)
            return 2
        inputs += [ln.strip() for ln in text.splitlines() if ln.strip() and ln[0] != '#']
    ws = _find(args)
    added, existing, rejected = 0, 0, []
    with ws.open_store() as store:
        recorded = store.get_meta('inputs', [])
        for arg in inputs:
            hit = sources.route(arg)
            # userinfo would be stored and mirrored into the emitted skill
            if not hit or (hit[0] != 'local' and urlsplit(arg).username):
                rejected.append(source_label(arg) if hit else arg)
                continue
            uri = _normalize(hit[0], arg)
            if store.get_by_uri(uri):
                existing += 1
                continue
            meta = {'scope': args.scope} if args.scope else {}
            store.add_unit(hit[0], uri, kind='seed', priority=100.0, meta=meta)
            recorded.append({'input': uri, 'source': hit[0]})
            added += 1
        store.set_meta('inputs', recorded)
    print(json.dumps({'added': added, 'existing': existing, 'rejected': rejected}))
    return 0


def _resolve_unit(store: Store, ref: str) -> Unit | None:
    unit = None
    if ref.isdigit():
        try:
            unit = store.get(int(ref))
        except KeyError:
            return None
    else:
        unit = store.get_by_uri(ref) or store.get_by_uri(urldefrag(ref.strip())[0])
    return unit if unit and unit.kind != 'seed' else None


def _resolve_ids(store: Store, refs: Sequence[str]) -> list[int] | None:
    """Unit ids for id-or-uri refs; None (after an error on stderr) when any ref is unknown."""
    found = {ref: _resolve_unit(store, ref) for ref in refs}
    if missing := [ref for ref, unit in found.items() if unit is None]:
        print(f'a2s: no such page (id or uri): {", ".join(missing)}', file=sys.stderr)
        return None
    return sorted({unit.id for unit in found.values() if unit})


def _edit_drops(args: argparse.Namespace, *, drop: bool) -> int:
    ws = _find(args)
    with ws.open_store() as store:
        if (ids := _resolve_ids(store, args.refs)) is None:
            return 2
        dropped = store.get_meta(tree.USER_DROPS_KEY, {})
        for uid in ids:
            if drop:
                dropped[str(uid)] = args.reason
            else:
                dropped.pop(str(uid), None)
        store.set_meta(tree.USER_DROPS_KEY, dropped)
    print(json.dumps({'drop' if drop else 'undrop': ids, 'now_dropped': len(dropped)}))
    return 0


def cmd_drop(args: argparse.Namespace) -> int:
    return _edit_drops(args, drop=True)


def cmd_undrop(args: argparse.Namespace) -> int:
    return _edit_drops(args, drop=False)


def cmd_requeue(args: argparse.Namespace) -> int:
    ws = _find(args)
    with ws.open_store() as store:
        if (ids := _resolve_ids(store, args.refs)) is None:
            return 2
        for uid in ids:
            store.mark(uid, args.status)
    print(json.dumps({'requeued': ids, 'status': args.status}))
    return 0


def _status_report(store: Store, ws: Workspace) -> dict:
    events = store.throttle_events(RECENT_THROTTLE_EVENTS)
    effort = store.get_meta('effort', 'standard')
    dropped = Ctx.open(ws, store).dropped_ids()
    return {
        'slug': ws.slug,
        'goal': store.get_meta('goal', ''),
        'effort': effort,
        'token_budget': EFFORT_BUDGET.get(effort),
        'corpus_tokens': store.token_total(exclude=dropped),
        'sources': {
            name: {
                'total': sum(by.values()),
                'tokens': store.token_total(name, dropped),
                'by_status': by,
            }
            for name, by in store.counts().items()
        },
        'throttle': {'events': events, 'per_host': store.throttle_counts()},
        'meta': store.all_meta(),
    }


def cmd_status(args: argparse.Namespace) -> int:
    ws = _find(args)
    with ws.open_store() as store:
        report = _status_report(store, ws)
    lines = [
        f'{report["slug"]}: effort={report["effort"]} goal={report["goal"]!r}',
        f'corpus tokens: {report["corpus_tokens"]} / {report["token_budget"] or "unbounded"}',
    ]
    for name, info in report['sources'].items():
        by = ' '.join(f'{k}={v}' for k, v in sorted(info['by_status'].items()))
        lines.append(f'  {name}: {info["total"]} units, {info["tokens"]} tok  ({by})')
    for host, evs in report['throttle']['per_host'].items():
        lines.append(
            f'  throttle {host}: ' + ' '.join(f'{k}={v}' for k, v in sorted(evs.items()))
        )
    _emit(report, args.json, '\n'.join(lines))
    return 0


def _estimate(store: Store, max_pages: int | None = None) -> dict:
    """What a crawl will actually fetch: pending pages, cut by the effort budget and --max-pages.

    Pages dropped with `a2s drop` are out of every count: the plan will not keep them.
    """
    effort = store.get_meta('effort', 'standard')
    dropped = store.user_drops()
    per_source: dict[str, dict] = {}
    for unit in store.units():
        if unit.id in dropped:
            continue
        info = per_source.setdefault(
            unit.source,
            {
                'units': 0,
                'done': 0,
                'pending': 0,
                'seeds_unexpanded': 0,
                'done_tokens': 0,
            },
        )
        if unit.kind == 'seed':
            info['seeds_unexpanded'] += unit.status == 'pending'
            continue
        info['units'] += 1
        if unit.status == 'done':
            info['done'] += 1
            info['done_tokens'] += unit.tokens
        elif unit.status in ('pending', 'needs_asr', 'needs_js', 'needs_convert'):
            info['pending'] += 1
    budget = EFFORT_BUDGET.get(effort)
    fetched = sum(info['done_tokens'] for info in per_source.values())
    room = None if budget is None else max(0, budget - fetched)
    capped_by: set[str] = set()
    totals = {
        'pending': 0,
        'will_fetch': 0,
        'uncapped_tokens': 0,
        'corpus_tokens': fetched,
    }
    for name, info in per_source.items():
        avg = info['done_tokens'] // info['done'] if info['done'] else None
        if avg is None:
            kinds = [u.kind for u in store.units(source=name) if u.kind != 'seed']
            avg = DEFAULT_TOKENS.get(kinds[0], 2500) if kinds else 0
        will = info['pending']
        if max_pages is not None and max_pages < will:
            will = max_pages
            capped_by.add('max_pages')
        if room is not None and avg and room // avg < will:
            will = room // avg
            capped_by.add('budget')
        if room is not None:
            room -= will * avg
        info.update(
            avg_tokens=avg,
            will_fetch=will,
            uncapped_tokens=info['done_tokens'] + info['pending'] * avg,
            corpus_tokens=info['done_tokens'] + will * avg,
        )
        totals['pending'] += info['pending']
        totals['will_fetch'] += will
        totals['uncapped_tokens'] += info['uncapped_tokens']
        totals['corpus_tokens'] += will * avg
    authoring = AUTHORING_TOKENS.get(effort, AUTHORING_TOKENS['standard'])
    return {
        'effort': effort,
        'sources': per_source,
        'fetched_tokens': fetched,
        **totals,
        'token_budget': budget,
        'max_pages': max_pages,
        'capped_by': sorted(capped_by),
        'projected_llm_tokens': {
            'brief': brief.TOTAL_TOKENS,
            'authoring': authoring,
            'total': brief.TOTAL_TOKENS + authoring,
        },
        'first_run_downloads': [DOWNLOADS[n] for n in per_source if n in DOWNLOADS]
        + [LAYA_DOWNLOAD],
    }


def cmd_estimate(args: argparse.Namespace) -> int:
    ws = _find(args)
    with ws.open_store() as store:
        report = _estimate(store, args.max_pages)
    lines = [f'effort={report["effort"]}']
    for name, info in report['sources'].items():
        lines.append(
            f'  {name}: {info["units"]} units ({info["done"]} done, {info["pending"]} pending), '
            f'will fetch {info["will_fetch"]} more (~{info["will_fetch"] * info["avg_tokens"]} tok), '
            f'{info["seeds_unexpanded"]} seeds not yet expanded'
        )
    cut = ' + '.join(
        {
            'budget': f'budget {report["token_budget"]}',
            'max_pages': f'--max-pages {report["max_pages"]}',
        }[c]
        for c in report['capped_by']
    )
    lines.append(
        f'fetched so far ~{report["fetched_tokens"]} tok; {report["will_fetch"]} of '
        f'{report["pending"]} pending pages will be fetched'
        + (f' (crawl stops at {cut})' if cut else '')
    )
    lines.append(
        f'corpus ~{report["corpus_tokens"]} tok projected'
        f' (budget {report["token_budget"] or "unbounded"};'
        f' mirroring every page would be ~{report["uncapped_tokens"]} tok)'
    )
    llm = report['projected_llm_tokens']
    lines.append(
        f'LLM pass ~{llm["total"]} tok (brief {llm["brief"]} + authoring {llm["authoring"]})'
    )
    lines.append('first-run downloads: ' + '; '.join(report['first_run_downloads']))
    _emit(report, args.json, '\n'.join(lines))
    return 0


def _dispatch(module: ModuleType) -> Callable[[argparse.Namespace], int]:
    def call(args: argparse.Namespace) -> int:
        return module.run(_find(args), args)

    return call


def run_command(
    prog: str,
    argv: Sequence[str] | None,
    add_args: Callable[[argparse.ArgumentParser], None],
    run: Callable[[Workspace, argparse.Namespace], int],
) -> int:
    """Entry-point helper for workspace-level tools (judge shim etc.)."""
    parser = argparse.ArgumentParser(prog=prog)
    _workspace_args(parser)
    add_args(parser)
    args = parser.parse_args(argv)
    try:
        return run(_find(args), args)
    except WorkspaceError as exc:
        print(f'{prog}: {exc}', file=sys.stderr)
        return 2


def run_source(name: str, argv: Sequence[str] | None) -> int:
    """Entry point behind every ingest shim: parse flags, open ctx, run the source."""
    module = sources.load_run(name)
    parser = argparse.ArgumentParser(prog=f'ingest-{name}')
    _workspace_args(parser)
    parser.add_argument('--max-pages', type=int, help='stop after this many units')
    parser.add_argument(
        '--allow-private', action='store_true', help='skip SSRF host checks'
    )
    module.add_args(parser)
    args = parser.parse_args(argv)
    try:
        ws = _find(args)
    except WorkspaceError as exc:
        print(f'ingest-{name}: {exc}', file=sys.stderr)
        return 2
    with ws.open_store() as store:
        ctx = Ctx.open(ws, store, args.max_pages, allow_private=args.allow_private)
        summary = module.run(ctx, args)
    print(summary.to_json())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='a2s', description='anything-to-skill pipeline')
    sub = parser.add_subparsers(dest='command', required=True)

    def add(
        name: str, func: Callable[[argparse.Namespace], int], help_: str
    ) -> argparse.ArgumentParser:
        sp = sub.add_parser(name, help=help_)
        sp.set_defaults(func=func)
        return sp

    sp = add('init', cmd_init, 'create a workspace and store the interview answers')
    sp.add_argument('slug')
    sp.add_argument('--base', type=Path)
    sp.add_argument('--goal')
    sp.add_argument('--effort', choices=list(EFFORT_BUDGET))
    sp.add_argument('--out', help='output skill directory')
    sp.add_argument('--name', help='skill name override')
    sp.add_argument('--instructions')

    sp = add('detect', cmd_detect, 'route each input to its source handler')
    sp.add_argument('inputs', nargs='+')
    sp.add_argument('--json', action='store_true')

    sp = add('seed', cmd_seed, 'add inputs (and URLs from --urls) as seed units')
    _workspace_args(sp)
    sp.add_argument('inputs', nargs='*')
    sp.add_argument(
        '--urls', metavar='FILE', help='file of URLs, one per line; - for stdin'
    )
    sp.add_argument('--scope', help='URL path prefix that limits the crawl')

    sp = add(
        'drop', cmd_drop, 'keep pages out of the skill (plan honors it at any effort)'
    )
    _workspace_args(sp)
    sp.add_argument('refs', nargs='+', metavar='id|uri')
    sp.add_argument(
        '--reason', required=True, help='why; shown in the plan and SOURCES.md'
    )

    sp = add('undrop', cmd_undrop, 'reverse a drop')
    _workspace_args(sp)
    sp.add_argument('refs', nargs='+', metavar='id|uri')

    sp = add(
        'requeue',
        cmd_requeue,
        'reset pages to pending (or needs_asr) with a fresh retry budget',
    )
    _workspace_args(sp)
    sp.add_argument('refs', nargs='+', metavar='id|uri')
    sp.add_argument('--status', choices=REQUEUE_STATUSES, default='pending')

    for name, func, help_ in (
        ('status', cmd_status, 'per-source totals and throttle events'),
        ('estimate', cmd_estimate, 'corpus tokens, projected LLM tokens, downloads'),
    ):
        sp = add(name, func, help_)
        _workspace_args(sp)
        sp.add_argument('--json', action='store_true')
        if name == 'estimate':
            sp.add_argument(
                '--max-pages',
                type=int,
                help='project the crawl as capped at this many pages',
            )

    for name, module, help_ in (
        ('plan', tree, 'build the reference tree (plan.json)'),
        ('brief', brief, 'write review.md for the LLM pass'),
        ('emit', write, 'write the skill to its output dir'),
        ('verify', verify, 'validate the emitted skill'),
        (
            'evals-freeze',
            compact_freeze,
            'freeze the evals every compaction run is graded on (--force to replace)',
        ),
        (
            'compact-brief',
            compact_brief,
            'write compact-brief.md for the optional compaction',
        ),
        (
            'compact-verify',
            compact_verify,
            'gate the staged compact skill (<ws>/compact)',
        ),
        (
            'compact-gate',
            compact_gate,
            'decide the three-way eval gate and record <ws>/compact-gate.json',
        ),
        (
            'compact',
            compact_swap,
            'swap the verified compact skill in (--apply) or back out (--revert)',
        ),
    ):
        sp = add(name, _dispatch(module), help_)
        _workspace_args(sp)
        module.add_args(sp)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except WorkspaceError as exc:
        print(f'a2s: {exc}', file=sys.stderr)
        return 2
