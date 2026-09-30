import argparse
from pathlib import Path

from anything_to_skill.core.models import RunSummary, Unit
from anything_to_skill.core.workspace import Ctx
from anything_to_skill.sources.local.convert import convert, outline
from anything_to_skill.sources.local.walk import CONVERT, walk

MAX_BYTES = 5_000_000
MARKDOWN = {'.md', '.markdown'}


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--convert',
        action='store_true',
        help='also convert PDF/DOCX/PPTX/EPUB/HTML/images with docling',
    )


def _expand(ctx: Ctx, seed: Unit, summary: RunSummary) -> None:
    root = Path(seed.uri).expanduser().resolve()
    files = walk(root)
    for path in files:
        rel = path.relative_to(root) if root.is_dir() else Path(path.name)
        # file:// URIs keep a single-file seed from colliding with its own child unit
        ctx.store.add_unit(
            'local',
            path.as_uri(),
            kind='file',
            parent=seed.id,
            depth=len(rel.parts) - 1,
            hint={'path': rel.as_posix()},
            meta={'path': str(path)},
        )
    if files:
        ctx.store.mark(seed.id, 'skipped')  # expanded: children carry the content
        return
    reason = 'no supported files'
    ctx.store.mark(seed.id, 'skipped', reason)
    summary.skipped += 1
    summary.note(f'{seed.uri}: {reason}')


def _swapped(path: Path) -> bool:
    """walk() only kept real files; a symlink that appeared since would escape the seed."""
    return path.resolve() != path


def _read_text(path: Path) -> tuple[str, str | None]:
    """(text, skip reason); raises OSError when the file cannot be read."""
    if path.stat().st_size > MAX_BYTES:
        return '', 'file too large'
    raw = path.read_bytes()
    if b'\0' in raw[:8192]:
        return '', 'binary content'
    text = raw.decode('utf-8', errors='replace')
    return text, (None if text.strip() else 'empty file')


def _ingest_file(ctx: Ctx, unit: Unit, summary: RunSummary) -> None:
    path = Path(unit.meta['path'])
    suffix = path.suffix.lower()
    if _swapped(path):
        ctx.store.mark(unit.id, 'skipped', 'path now goes through a symlink')
        summary.skipped += 1
        return
    if suffix in CONVERT:
        ctx.store.mark(unit.id, 'needs_convert')
        return
    try:
        text, skip = _read_text(path)
    except OSError as exc:
        ctx.store.mark(unit.id, 'failed', str(exc))
        summary.failed += 1
        summary.note(f'{path}: {exc}')
        return
    if skip:
        ctx.store.mark(unit.id, 'skipped', skip)
        summary.skipped += 1
        return
    headings = outline(text) if suffix in MARKDOWN else []
    ctx.store.finish(
        unit.id,
        text,
        title=(headings[0] if headings else path.stem),
        hint={'headings': headings},
    )
    summary.done += 1


def _ingest(ctx: Ctx, summary: RunSummary) -> None:
    # Seeds carry priority 100, so they are claimed first and their children follow.
    n = 0
    while ctx.max_pages is None or n < ctx.max_pages:
        if ctx.over_budget() or not (claimed := ctx.store.claim('local')):
            return
        unit = claimed[0]
        if unit.kind == 'seed':
            _expand(ctx, unit, summary)
        else:
            _ingest_file(ctx, unit, summary)
            n += 1


def _convert(ctx: Ctx, summary: RunSummary) -> None:
    n = 0
    while ctx.max_pages is None or n < ctx.max_pages:
        if ctx.over_budget():
            return
        if not (claimed := ctx.store.claim('local', status='needs_convert')):
            return
        unit = claimed[0]
        n += 1
        path = Path(unit.meta['path'])
        if _swapped(path):
            ctx.store.mark(unit.id, 'skipped', 'path now goes through a symlink')
            summary.skipped += 1
            continue
        try:
            markdown, title = convert(path)
        except Exception as exc:  # noqa: BLE001
            summary.note(f'{path}: {exc}')
            if ctx.store.fail(unit.id, str(exc)) == 'failed':
                summary.failed += 1
            continue
        ctx.store.finish(
            unit.id,
            markdown,
            title=title or path.stem,
            hint={'headings': outline(markdown)},
        )
        summary.done += 1


def run(ctx: Ctx, args: argparse.Namespace) -> RunSummary:
    summary = RunSummary()
    _ingest(ctx, summary)
    if args.convert:
        _convert(ctx, summary)
    summary.needs_convert = len(ctx.store.units('local', 'needs_convert'))
    return summary
