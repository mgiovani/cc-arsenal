"""Evals are frozen before compaction so no-skill, full and compact runs are graded on one set."""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from anything_to_skill.compact import layout
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.emit.verify import _skill_dir, process_assertions


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--force',
        action='store_true',
        help='replace the frozen set, after strengthening the evals of the full skill',
    )


def cases(raw: str) -> list[dict[str, Any]]:
    """The eval cases of an evals.json text; ValueError when it is not one."""
    try:
        items = json.loads(raw)['evals']
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError('not a valid evals file: expected {"evals": [...]}') from exc
    if not isinstance(items, list) or not all(isinstance(c, dict) for c in items):
        raise ValueError('not a valid evals file: "evals" must be a list of objects')
    return items


def load(ws: Workspace) -> str | None:
    try:
        return ws.evals_frozen_path.read_text('utf-8')
    except OSError:
        return None


def sync(ws: Workspace, source: Path, *, force: bool = False) -> str | None:
    """Freeze `source`'s evals.json (once, or again with `force`) and copy it verbatim into compact/.

    Also writes eval-prompts.json (ids and prompts only): eval executors read that, never the assertions.
    Returns the frozen text, or None when there is nothing to freeze.
    """
    src = source / 'evals' / 'evals.json'
    if (force or load(ws) is None) and src.is_file():
        text = src.read_text('utf-8')
        cases(text)
        ws.evals_frozen_path.write_text(text, 'utf-8')
    frozen = load(ws)
    if frozen is None:
        return None
    prompts = [{'id': c.get('id'), 'prompt': c.get('prompt')} for c in cases(frozen)]
    ws.eval_prompts_path.write_text(json.dumps({'evals': prompts}, indent=2), 'utf-8')
    dest = ws.compact_dir / 'evals'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'evals.json').write_text(frozen, 'utf-8')
    trigger = source / 'evals' / 'trigger-eval.json'
    if trigger.is_file() and not (dest / 'trigger-eval.json').exists():
        shutil.copyfile(trigger, dest / 'trigger-eval.json')
    return frozen


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py evals-freeze`: freeze the emitted skill's evals for the compaction gate."""
    source = layout.original_dir(ws, _skill_dir(ws, None))
    src = source / 'evals' / 'evals.json'
    old = load(ws)
    if (
        not args.force
        and old is not None
        and src.is_file()
        and src.read_text('utf-8') != old
    ):
        print(
            'evals-freeze: kept the existing frozen set; the emitted evals differ '
            '(pass --force to replace it)',
            file=sys.stderr,
        )
    try:
        frozen = sync(ws, source, force=args.force)
    except ValueError as exc:
        print(f'evals-freeze: {src}: {exc}', file=sys.stderr)
        return 2
    if frozen is None:
        print(f'evals-freeze: no evals/evals.json under {source}', file=sys.stderr)
        return 2
    for f in process_assertions(frozen, 'warn'):
        print(f'WARN {f.message}', file=sys.stderr)
    print(
        f'{ws.evals_frozen_path}: {len(cases(frozen))} evals frozen, '
        f'copied to {ws.compact_dir / "evals" / "evals.json"}; '
        f'executor prompts (no assertions): {ws.eval_prompts_path}'
    )
    return 0
