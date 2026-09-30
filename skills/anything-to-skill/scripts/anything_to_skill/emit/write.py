import argparse
import json
import os
import re
import shutil
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from anything_to_skill.core.models import Unit, source_label
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.emit.link import link_skill
from anything_to_skill.emit.templates import render
from anything_to_skill.plan.index import render_index
from anything_to_skill.plan.pack import render_file
from anything_to_skill.plan.priority import slugify
from anything_to_skill.plan.tree import drop_lines, not_ingested_lines
from anything_to_skill.scan import quotes

MAX_DESCRIPTION = 1024
ROUTING_ROWS = 25
ROUTING_FILES_SHOWN = 3
GENERIC_DESCRIPTION = re.compile(
    r'^Reference for .+, built from \d+ source pages\..* Use when the user asks about .+ or needs its documentation\.$'
)
NEGATIVE_TRIGGERS = [
    'write a python script that renames files by date',
    'fix the layout bug in this css grid',
    'summarize the attached meeting transcript',
]


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--out', help='skill directory (default: the init --out answer)')
    parser.add_argument(
        '--replace',
        action='store_true',
        help='overwrite an earlier emit (only dirs holding references/SOURCES.md)',
    )
    parser.add_argument(
        '--link-claude',
        action='store_true',
        help='also link .claude/skills/<name> to the emitted skill',
    )


def skill_name(ws: Workspace, meta_name: str | None) -> str:
    """plan --skill-name (what the approve-tree gate showed), else init --name, else the
    workspace slug; emit and verify must resolve the same directory."""
    plan_name = None
    if ws.plan_path.exists():
        plan_name = json.loads(ws.plan_path.read_text('utf-8')).get('skill_name')
    return slugify(plan_name or meta_name or ws.slug)[:64] or 'skill'


def _frontmatter_description(text: str) -> tuple[str | None, str]:
    """Split an authored SKILL.md into (description or None, body); other keys are dropped."""
    m = re.match(r'^---\n(.*?)\n---\n?', text, re.DOTALL)
    if not m:
        return None, text
    lines = m.group(1).split('\n')
    desc = None
    for i, line in enumerate(lines):
        if line.startswith('description:'):
            value = line.split(':', 1)[1].strip()
            continuation = []
            for nxt in lines[i + 1 :]:
                if nxt and not nxt.startswith((' ', '\t')):
                    break
                continuation.append(nxt.strip())
            if value in ('|', '>', '|-', '>-'):
                value = ''
            value = ' '.join(filter(None, [value, *continuation]))
            if len(value) > 1 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]
            desc = value
            break
    return desc, text[m.end() :].lstrip('\n')


def _clean_description(text: str) -> str:
    return ' '.join(text.replace('<', '').replace('>', '').split())[:MAX_DESCRIPTION]


def _unit_ids(entry: dict[str, Any]) -> list[int]:
    return [u['id'] if isinstance(u, dict) else int(u) for u in entry.get('units', [])]


def _ref_path(entry: dict[str, Any]) -> str:
    return str(entry['path']).removeprefix('references/').lstrip('/')


def _file_body(
    entry: dict[str, Any], units: dict[int, Unit], texts: dict[int, str]
) -> str:
    """One reference file, rendered from the plan's slices so split pages stay split."""
    ids = [i for i in _unit_ids(entry) if i in units]
    first = units[ids[0]]
    parts = entry.get('parts') or [
        {'unit': i, 'start': 0, 'end': len(texts[i])} for i in ids
    ]
    title = entry.get('title') or first.title or first.source_label()
    return render_file(
        {
            **entry,
            'parts': parts,
            'title': title,
            'summary': entry.get('summary') or title,
        },
        units,
        texts,
    )


_FRAME = re.compile(r'\]\(assets/frames/([^)\s]+)\)')
_FRAME_NAME = re.compile(r'(.+)-(\d+)\.png$')


def _frame_target(name: str, slugs: dict[str, str]) -> str:
    """Ingest names a frame `<video-id>-<seconds>.png`; the skill files it as `<video-slug>/<mm-ss>.png`."""
    m = _FRAME_NAME.match(name)
    if not m or m.group(1) not in slugs:
        return name
    minutes, seconds = divmod(int(m.group(2)), 60)
    return f'{slugs[m.group(1)]}/{minutes:02d}-{seconds:02d}.png'


def _frame_slugs(plan: dict[str, Any], units: dict[int, Unit]) -> dict[str, str]:
    """Video id to the plan's short video name, for every planned video that has an id."""
    return {
        str(units[int(uid)].meta['video_id']): slug
        for uid, slug in plan.get('videos', {}).items()
        if int(uid) in units and units[int(uid)].meta.get('video_id')
    }


def _relink_frames(text: str, rel: str, slugs: dict[str, str]) -> str:
    """Frame links are written skill-root-relative under ingest's names; point them at the renamed
    frames, relative to the file's folder."""
    prefix = os.path.relpath('assets/frames', str(Path(rel).parent))
    return _FRAME.sub(lambda m: f']({prefix}/{_frame_target(m.group(1), slugs)})', text)


def _routing_table(plan: dict[str, Any]) -> str:
    rows = ['| Topic | Read |', '|---|---|']
    for section in plan.get('sections', [])[:ROUTING_ROWS]:
        files = section.get('files', [])
        shown = ', '.join(
            f'`references/{_ref_path(f)}`' for f in files[:ROUTING_FILES_SHOWN]
        )
        more = (
            f' (+{len(files) - ROUTING_FILES_SHOWN} more in `references/INDEX.md`)'
            if len(files) > ROUTING_FILES_SHOWN
            else ''
        )
        rows.append(f'| {section.get("title") or section.get("slug")} | {shown}{more} |')
    return '\n'.join(rows)


def _default_body(name: str, topic: str, plan: dict[str, Any], has_best: bool) -> str:
    best = (
        '- `references/best-practices.md` holds the distilled guidance.\n'
        if has_best
        else ''
    )
    return (
        f'# {name}\n\n'
        f'Reference material on {topic}, mirrored from the sources in `references/SOURCES.md`.\n\n'
        '## How to use\n\n'
        '1. Read `references/INDEX.md` and pick the file whose summary matches the question.\n'
        '2. Open only that file; each is small enough to read whole.\n'
        f'{best}'
        '3. Quote or link the file you used when you answer.\n\n'
        '## Routing\n\n'
        f'{_routing_table(plan)}\n'
    )


def _default_description(topic: str, plan: dict[str, Any], count: int) -> str:
    titles = [s.get('title') or s.get('slug') for s in plan.get('sections', [])[:4]]
    covers = f' Covers {", ".join(t for t in titles if t)}.' if any(titles) else ''
    return (
        f'Reference for {topic}, built from {count} source pages.{covers} '
        f'Use when the user asks about {topic} or needs its documentation.'
    )


def _stage_scores(row: dict[str, Any]) -> str:
    """' (title 0.9, description 0.8, transcript 0.7)' once a video was read past its title."""
    stages = [
        f'{label} {row[key]}'
        for label, key in (
            ('title', 'laya'),
            ('description', 'meta'),
            ('transcript', 'transcript'),
        )
        if row.get(key) is not None
    ]
    return (
        f' ({", ".join(stages)})'
        if row.get('meta') is not None or row.get('transcript') is not None
        else ''
    )


def _funnel_line(rec: dict[str, Any]) -> str:
    funnel = rec.get('funnel') or {}
    parts = [
        f'{funnel[key]["scored"]} on {label}'
        for key, label in (
            ('meta', 'description and chapters'),
            ('transcripts', 'captions'),
        )
        if key in funnel
    ]
    if not parts:
        return ''
    note = (
        f'; {funnel["throttled"]} throttled, earlier stages kept'
        if funnel.get('throttled')
        else ''
    )
    return f' Also read past the title: {", ".join(parts)}{note}.'


def ranking_lines(
    ranking: dict[str, Any], dropped: frozenset[str] = frozenset()
) -> list[str]:
    """Why each channel or playlist kept the videos it did (Laya blended with keywords).

    `dropped` holds the video ids the user cut afterwards: they were chosen, but are not in the skill.
    """
    lines: list[str] = []
    for seed, rec in ranking.items():
        kept = sum(r.get('id') not in dropped for r in rec['chosen'])
        lines += [
            '',
            f'## Video ranking: {source_label(seed)}',
            '',
            f'{kept} of {rec["candidates"]} videos kept, ranked by Laya '
            f'blended with goal keywords (score 0-1).{_funnel_line(rec)}',
            '',
        ]
        lines += [
            f'- {"dropped" if r.get("id") in dropped else "kept"} {r["score"]}{_stage_scores(r)}: {r["title"]}'
            for r in rec['chosen']
        ]
        lines += [
            f'- skipped {r["score"]}{_stage_scores(r)}: {r["title"]}'
            for r in rec['skipped'][:5]
        ]
    return lines


def _sources_md(
    plan: dict[str, Any],
    units: dict[int, Unit],
    meta: dict[str, Any],
    files_by_unit: dict[int, list[str]],
    everything: dict[int, Unit] | None = None,
) -> str:
    """`everything` (every non-seed unit) labels dropped pages that were never fetched."""
    everything = everything or units
    dropped_videos = frozenset(
        str(everything[d['id']].meta.get('video_id'))
        for d in plan.get('dropped', [])
        if d['id'] in everything
    )
    lines = [
        '# Sources',
        '',
        f'Generated by anything-to-skill on {datetime.now(UTC):%Y-%m-%d}.'
        + (f' Goal: {meta["goal"]}' if meta.get('goal') else ''),
        '',
        'Reference files mirror the source material. Check each source license before '
        'redistributing; treat verbatim mirrors as private-use.',
        '',
        '## Inputs',
        '',
    ]
    for item in meta.get('inputs', []):
        lines.append(f'- {item["source"]}: {source_label(item["input"])}')
    by_source: dict[str, list[Unit]] = {}
    for uid in files_by_unit:
        if uid in units:
            by_source.setdefault(units[uid].source, []).append(units[uid])
    for source, group in sorted(by_source.items()):
        lines += ['', f'## {source} ({len(group)} units)', '']
        for unit in sorted(group, key=lambda u: u.id):
            where = ', '.join(f'`references/{p}`' for p in files_by_unit[unit.id])
            label = unit.source_label()
            lines.append(f'- {unit.title or label} ({label}): {where}')
    lines += ranking_lines(meta.get('youtube.ranking', {}), dropped_videos)
    if plan.get('dropped'):
        lines += ['', '## Dropped', '']
        lines += [
            f'- {ln}'
            for ln in drop_lines(
                plan['dropped'],
                lambda i: everything[i].source_label()
                if i in everything
                else f'unit {i}',
            )
        ]
    if plan.get('not_ingested'):
        lines += [
            '',
            '## Not ingested',
            '',
            'Discovered but never fetched, so not in this skill:',
            '',
        ]
        lines += [f'- {ln}' for ln in not_ingested_lines(plan)]
    return '\n'.join(lines) + '\n'


def _eval_files(name: str, topic: str, plan: dict[str, Any]) -> tuple[str, str]:
    top = sorted(
        plan.get('sections', []),
        key=lambda s: -sum(f.get('tokens', 0) for f in s.get('files', [])),
    )[:3]
    cases = [
        {
            'id': f'route-{s.get("slug", i)}',
            'prompt': f'Using the {name} skill, explain what the reference says about {s.get("title") or s.get("slug")}.',
            'assertions': [
                'Reads references/INDEX.md before opening any reference file',
                f'Opens a file under references/ that covers {s.get("title") or s.get("slug")}',
                'Names the reference file the answer came from',
            ],
        }
        for i, s in enumerate(top)
    ] or [
        {
            'id': 'basic-lookup',
            'prompt': f'Using the {name} skill, answer a question about {topic}.',
            'assertions': ['Reads references/INDEX.md before opening any reference file'],
        }
    ]
    queries = [{'query': f'help me with {topic}', 'should_trigger': True}]
    queries += [
        {
            'query': f'what does the documentation say about {s.get("title") or s.get("slug")}',
            'should_trigger': True,
        }
        for s in top
    ]
    queries += [{'query': q, 'should_trigger': False} for q in NEGATIVE_TRIGGERS]

    def dump(data: object) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)

    return (
        render('evals.json.tmpl', skill=json.dumps(name), evals=dump(cases)),
        render('trigger-eval.json.tmpl', queries=dump(queries)),
    )


def _read_authored(ws: Workspace) -> dict[str, str]:
    """Authored files keyed by their path inside the emitted skill."""
    out: dict[str, str] = {}
    root = ws.authored_dir
    if (root / 'SKILL.md').exists():
        out['SKILL.md'] = (root / 'SKILL.md').read_text('utf-8')
    if (root / 'best-practices.md').exists():
        out['references/best-practices.md'] = (root / 'best-practices.md').read_text(
            'utf-8'
        )
    for path in sorted((root / 'examples').glob('*.md')):
        out[f'references/examples/{path.name}'] = path.read_text('utf-8')
    return out


def _put(stage: Path, rel: str, text: str) -> None:
    dest = (stage / rel).resolve()
    if not dest.is_relative_to(stage.resolve()):
        raise ValueError(f'path escapes the skill directory: {rel}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding='utf-8')


def _check_json(path: Path) -> str:
    text = path.read_text('utf-8')
    json.loads(text)
    return text


def _build(
    stage: Path,
    ws: Workspace,
    store: Store,
    plan: dict[str, Any],
    meta: dict[str, Any],
    name: str,
    authored: dict[str, str],
) -> dict[str, Any]:
    everything = {u.id: u for u in store.units() if u.kind != 'seed'}
    units = {i: u for i, u in everything.items() if u.status == 'done'}
    planned = {
        uid
        for section in plan.get('sections', [])
        for entry in section.get('files', [])
        for uid in _unit_ids(entry)
    }
    texts = {uid: store.read_markdown(uid) for uid in units if uid in planned}
    topic = meta.get('goal') or name
    slugs = _frame_slugs(plan, units)
    files_by_unit: dict[int, list[str]] = {}
    bodies: dict[str, str] = {}
    for section in plan.get('sections', []):
        for entry in section.get('files', []):
            rel = _ref_path(entry)
            bodies[f'references/{rel}'] = _relink_frames(
                _file_body(entry, units, texts), f'references/{rel}', slugs
            )
            for uid in _unit_ids(entry):
                files_by_unit.setdefault(uid, []).append(rel)

    def locate_for(from_rel: str) -> Callable[[int, str], str | None]:
        def locate(uid: int, quote: str) -> str | None:
            cands = files_by_unit.get(uid, [])
            if not cands:
                return None
            needle = quotes.normalize(quote)
            pick = next(
                (
                    c
                    for c in cands
                    if len(cands) == 1
                    or needle in quotes.normalize(bodies[f'references/{c}'])
                ),
                cands[0],
            )
            return os.path.relpath(f'references/{pick}', str(Path(from_rel).parent))

        return locate

    for rel, text in bodies.items():
        _put(stage, rel, text)

    kinds: dict[int, str] | None = None
    if ws.judge_path.exists():
        kinds = {
            int(k): v
            for k, v in json.loads(ws.judge_path.read_text('utf-8'))
            .get('kind', {})
            .items()
        }
    _put(stage, 'references/INDEX.md', render_index(plan, kinds))
    _put(
        stage,
        'references/SOURCES.md',
        _sources_md(plan, units, meta, files_by_unit, everything),
    )

    hub = authored.get('SKILL.md')
    description, body = _frontmatter_description(hub) if hub else (None, '')
    if not hub:
        body = _default_body(
            name, topic, plan, 'references/best-practices.md' in authored
        )
    if not description:
        print(
            'emit: warning: authored/SKILL.md has no description in its frontmatter; '
            'using the generic default',
            file=sys.stderr,
        )
    description = _clean_description(
        description or _default_description(topic, plan, len(units))
    )
    authored = {
        **authored,
        'SKILL.md': render(
            'SKILL.md.tmpl',
            name=name,
            description=json.dumps(description, ensure_ascii=False),
            body=body.rstrip() + '\n',
        ),
    }
    written: list[str] = []
    for rel, text in authored.items():
        linked = _relink_frames(
            quotes.rewrite_markers(text, {}, locate_for(rel)), rel, slugs
        )
        written.append(linked)
        _put(stage, rel, linked)

    evals, trigger = _eval_files(name, topic, plan)
    for fname, generated in (('evals.json', evals), ('trigger-eval.json', trigger)):
        custom = ws.authored_dir / fname
        _put(
            stage, f'evals/{fname}', _check_json(custom) if custom.exists() else generated
        )

    frames = ws.dir / 'frames'
    on_disk = (
        {_frame_target(p.name, slugs): p for p in frames.iterdir() if p.is_file()}
        if frames.is_dir()
        else {}
    )
    used = {
        m.group(1)
        for text in (*bodies.values(), *written)
        for m in re.finditer(r'\]\([./]*assets/frames/([^)\s]+)\)', text)
    }
    for target in sorted(used & on_disk.keys()):
        dest = stage / 'assets' / 'frames' / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(on_disk[target], dest)
    return {'reference_files': len(bodies), 'units': len(files_by_unit)}


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py emit`: stage the skill from plan.json + authored/, then move it into place."""
    if not ws.plan_path.exists():
        print('emit: no plan.json; run `a2s.py plan` first', file=sys.stderr)
        return 2
    plan = json.loads(ws.plan_path.read_text('utf-8'))
    with ws.open_store() as store:
        meta = store.all_meta()
        name = skill_name(ws, meta.get('name'))
        out_arg = args.out or meta.get('out')
        out = Path(out_arg).expanduser() if out_arg else Path('.agents/skills') / name
        out = out.resolve() if out.is_absolute() else (Path.cwd() / out).resolve()

        if os.path.lexists(out):
            if not args.replace:
                print(
                    f'emit: {out} exists; pass --replace to overwrite an earlier emit',
                    file=sys.stderr,
                )
                return 1
            if not (out / 'references' / 'SOURCES.md').exists():
                print(
                    f'emit: {out} was not generated by emit; refusing to replace it',
                    file=sys.stderr,
                )
                return 1

        authored = _read_authored(ws)
        corpus = quotes.load_corpus(store)
        findings = [
            (rel, f)
            for rel, text in authored.items()
            for f in quotes.verify(text, store, corpus)
        ]
        for rel, f in findings:
            if f.severity != 'hard':
                print(
                    f'emit: warning: {rel}:{f.line or "-"} {f.rule}: {f.message}',
                    file=sys.stderr,
                )
        problems = [(rel, f) for rel, f in findings if f.severity == 'hard']
        if problems:
            for rel, f in problems:
                print(
                    f'emit: {rel}:{f.line or "-"} {f.rule}: {f.message}', file=sys.stderr
                )
            print(
                'emit: fix the authored files and re-run; nothing was written',
                file=sys.stderr,
            )
            return 1

        stage = out.with_name(f'.{out.name}.a2s-stage')
        backup = out.with_name(f'.{out.name}.a2s-old')
        shutil.rmtree(stage, ignore_errors=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        moved = False
        try:
            stats = _build(stage, ws, store, plan, meta, name, authored)
            if os.path.lexists(out):
                shutil.rmtree(backup, ignore_errors=True)
                out.rename(backup)
                moved = True
            stage.rename(out)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            if moved:
                backup.rename(out)
            raise
        shutil.rmtree(backup, ignore_errors=True)

    result = {'skill': str(out), 'name': name, **stats}
    code = 0
    if args.link_claude:
        try:
            result['link'] = str(
                link_skill(out, Path.cwd() / '.claude' / 'skills' / name)
            )
        except FileExistsError as exc:
            print(f'emit: {exc}', file=sys.stderr)
            code = 1  # the skill is emitted, but the requested link was refused
    print(json.dumps(result))
    return code
