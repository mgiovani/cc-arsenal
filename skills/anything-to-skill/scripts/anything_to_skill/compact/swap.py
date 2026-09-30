import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from anything_to_skill.compact import verify
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.emit.verify import _skill_dir


def add_args(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        '--apply',
        action='store_true',
        help='back up the emitted skill, then swap the compact one in',
    )
    mode.add_argument(
        '--revert', action='store_true', help='restore the full skill saved by --apply'
    )
    parser.add_argument('--out', help='skill directory (default: the init --out answer)')


def _is_full(skill: Path) -> bool:
    return (skill / 'references' / 'SOURCES.md').is_file()


def _swap_in(out: Path, source: Path) -> None:
    """Replace `out` by a copy of `source`: copy beside it, rename the old one away, rename in."""
    stage = out.with_name(f'.{out.name}.a2s-compact-stage')
    old = out.with_name(f'.{out.name}.a2s-compact-old')
    for leftover in (stage, old):
        if os.path.lexists(leftover):
            raise FileExistsError(
                f'{leftover} is left over from an interrupted run; inspect it, remove it, retry'
            )
    shutil.copytree(source, stage, symlinks=True)
    moved = False
    try:
        if os.path.lexists(out):
            out.rename(old)
            moved = True
        stage.rename(out)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        if moved and not os.path.lexists(out):
            old.rename(out)
        raise
    shutil.rmtree(old, ignore_errors=True)


def _fail(message: str) -> int:
    print(f'compact: {message}', file=sys.stderr)
    return 1


def _apply(ws: Workspace, out: Path) -> int:
    if out.is_symlink():
        return _fail(f'{out} is a symlink; pass the real directory with --out')
    if os.path.lexists(ws.full_dir):
        return _fail(f'{ws.full_dir} exists: already compacted. Run --revert first')
    if not _is_full(out):
        return _fail(
            f'{out} is not a freshly emitted skill (no references/SOURCES.md); nothing changed'
        )
    report = verify.check(ws, ws.compact_dir)
    if not report['ok']:
        for r in report['findings']:
            if r['severity'] == 'hard':
                print(
                    f'HARD {r["file"]}:{r["line"] or "-"} {r["rule"]}: {r["message"]}',
                    file=sys.stderr,
                )
        return _fail('compact-verify has hard failures; nothing changed')
    partial = ws.full_dir.with_name('full.partial')
    shutil.rmtree(partial, ignore_errors=True)
    shutil.copytree(out, partial, symlinks=True)
    partial.rename(ws.full_dir)
    _swap_in(out, ws.compact_dir)
    print(
        json.dumps(
            {'skill': str(out), 'backup': str(ws.full_dir), 'tokens': report['tokens']}
        )
    )
    return 0


def _revert(ws: Workspace, out: Path) -> int:
    if not (ws.full_dir / 'SKILL.md').is_file() or not _is_full(ws.full_dir):
        return _fail(f'no full skill saved in {ws.full_dir}; nothing to revert')
    if out.is_symlink():
        return _fail(f'{out} is a symlink; pass the real directory with --out')
    if os.path.lexists(out) and _is_full(out):
        return _fail(f'{out} already holds the full skill; nothing changed')
    _swap_in(out, ws.full_dir)
    shutil.rmtree(ws.full_dir)
    print(json.dumps({'skill': str(out), 'restored': True}))
    return 0


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py compact --apply|--revert`: swap the verified compact skill in, or the full one back."""
    out = _skill_dir(ws, args.out)
    try:
        return _apply(ws, out) if args.apply else _revert(ws, out)
    except FileExistsError as exc:
        return _fail(str(exc))
