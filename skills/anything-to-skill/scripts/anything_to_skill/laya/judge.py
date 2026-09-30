import argparse
import json
import re
import sys
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

from anything_to_skill.cli import run_command
from anything_to_skill.core.models import Unit
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.laya import apply, client
from anything_to_skill.laya.questions import ask_many
from anything_to_skill.plan.priority import goal_keywords
from anything_to_skill.plan.tree import GENERAL, USER_DROPS_KEY, VIDEOS

PREVIEW_CHARS = 800  # ~200 tokens
CALIBRATION_SIZE = 20
CALIBRATION_MIN_URL_TYPED = 5
MIN_AGREEMENT = 0.7
ORPHAN_SECTIONS = (GENERAL, VIDEOS)

KINDS = {
    'reference': 'lookup material: API, options, commands, tables',
    'tutorial': 'step-by-step guide that teaches a task',
    'example': 'worked example, recipe or code sample',
    'concept': 'explanation of ideas, design or background',
}
ON_TOPIC = ['The page is about the goal.', 'The page is unrelated to the goal.']
COHESIVE = ['The page covers one topic.', 'The page covers several unrelated topics.']
URL_KIND = (
    ('tutorial', re.compile(r'/tutorials?/')),
    ('reference', re.compile(r'/(?:api|reference)/')),
    ('example', re.compile(r'/examples?/')),
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--tau',
        type=float,
        default=apply.DEFAULT_TAU,
        help='minimum confidence before a page may be dropped',
    )


def _url_kind(uri: str) -> str | None:
    path = urlparse(uri).path
    return next((kind for kind, rx in URL_KIND if rx.search(path)), None)


def _section_options(ws: Workspace) -> tuple[list[tuple[str, str]], set[int]]:
    """Real sections (slug, title) and the ids of orphans: units the plan put in 'general' or 'videos'."""
    if not ws.plan_path.exists():
        return [], set()
    sections = json.loads(ws.plan_path.read_text('utf-8')).get('sections', [])
    named = [
        (s['slug'], s.get('title') or s['slug'])
        for s in sections
        if s['slug'] not in ORPHAN_SECTIONS
    ]
    orphans = {
        int(uid)
        for s in sections
        if s['slug'] in ORPHAN_SECTIONS
        for f in s.get('files', [])
        for uid in f.get('units', [])
    }
    return named, orphans


def _judge_unit(
    unit: Unit,
    goal: str,
    words: set[str],
    text: str,
    sections: list[tuple[str, str]],
) -> dict[str, Any]:
    preview = text[:PREVIEW_CHARS]
    state = f'Goal: {goal}\nTitle: {unit.title or ""}\nPath: {urlparse(unit.uri).path}\n{preview}'
    labels = {
        'on_topic': ['on', 'off'],
        'kind': list(KINDS),
        'cohesive': ['one', 'several'],
    }
    specs = {
        'on_topic': ('Is the page about the goal?', ON_TOPIC),
        'kind': ('What kind of page is this?', list(KINDS.values())),
        'cohesive': ('Does the page stay on one topic?', COHESIVE),
    }
    if sections:
        # More than 10 sections lands in laya's uncalibrated `choice:11+` bucket: the pick
        # counts only because both option orders agreed, and no tau reads its confidence.
        labels['section'] = [slug for slug, _ in sections]
        specs['section'] = (
            'Which section does the page belong in?',
            [title for _, title in sections],
        )
    haystack = f'{unit.title or ""} {unit.uri} {preview}'.lower()
    judgment: dict[str, Any] = {'disagree': []}
    if words:  # no count means unknown, which blocks a drop (laya.apply._drop_blocker)
        judgment['kw'] = sum(w in haystack for w in words)
    for name, picked in ask_many(state, specs).items():
        if picked is None:
            judgment['disagree'].append(name)
        else:
            idx, conf = picked
            judgment[name] = {'label': labels[name][idx], 'conf': conf}
    return judgment


def calibration_sample(units: list[Unit]) -> list[Unit]:
    """Pages whose kind the URL already tells us; only these can check the model's answers."""
    typed = [u for u in units if _url_kind(u.uri)]
    step = max(1, len(typed) // CALIBRATION_SIZE)
    return typed[::step][:CALIBRATION_SIZE]


def _judge_all(
    ws: Workspace, store: Store, units: list[Unit], tau: float
) -> dict[str, Any]:
    goal = store.get_meta('goal', '')
    effort = store.get_meta('effort', 'standard')
    words = goal_keywords(goal)
    named, orphans = _section_options(ws)
    judgments: dict[int, dict[str, Any]] = {}

    def judge(unit: Unit) -> None:
        judgments[unit.id] = _judge_unit(
            unit,
            goal,
            words,
            store.read_markdown(unit.id),
            named if unit.id in orphans else [],
        )

    sample = calibration_sample(units)
    for unit in sample:
        judge(unit)
    # Too few URL-typed pages means the guard cannot measure anything: stay annotate-only.
    measured = len(sample) >= CALIBRATION_MIN_URL_TYPED
    right = sum(
        judgments[u.id].get('kind', {}).get('label') == _url_kind(u.uri) for u in sample
    )
    agreement = right / len(sample) if measured else None
    for unit in units:
        if unit.id not in judgments:
            judge(unit)
    result = apply.apply_rules(
        judgments,
        units,
        effort,
        orphans=orphans if named else (),
        annotate_only=agreement is None or agreement < MIN_AGREEMENT,
        agreement=agreement,
        tau=tau,
    )
    result['order_agreement'] = (
        round(sum('kind' in judgments[u.id] for u in sample) / len(sample), 3)
        if sample
        else None
    )
    return result


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """Judge pages, write ws.judge_path (schema in apply.py); skip with a warning if Laya is unavailable."""
    with ws.open_store() as store:
        dropped = {int(k) for k in store.get_meta(USER_DROPS_KEY, {})}
        units = [
            u
            for u in store.units(status='done')
            if u.kind != 'seed' and u.id not in dropped
        ]
        if not units:
            print('judge: no fetched pages to judge', file=sys.stderr)
            return 0
        try:
            client.get_router()
        except client.LayaUnavailableError as exc:
            print(f'judge: skipped, {exc}', file=sys.stderr)
            return 0
        result = _judge_all(ws, store, units, args.tau)
    ws.judge_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(
        json.dumps(
            {
                'judged': len(units),
                'agreement': result['agreement'],
                'annotate_only': result['annotate_only'],
                'drop': len(result['drop']),
                'section': len(result['section']),
                'deferred': len(result['deferred']),
            }
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_command('judge', argv, add_args, run)
