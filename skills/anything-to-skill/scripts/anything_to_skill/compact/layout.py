"""What counts as mirror versus authored inside an emitted skill, and its token sizes."""

from pathlib import Path

from anything_to_skill.core.tokens import count
from anything_to_skill.core.workspace import Workspace

TEXT_SUFFIXES = ('.md', '.json')
MIRROR_EXEMPT = frozenset(
    {'references/INDEX.md', 'references/SOURCES.md', 'references/best-practices.md'}
)
MAX_REFERENCE_SHARE = 0.25
MAX_HUB_LINES = 150


def read_tree(root: Path) -> dict[str, str]:
    """Text of every markdown and JSON file under `root`, keyed by posix path."""
    return {
        p.relative_to(root).as_posix(): p.read_text('utf-8')
        for p in sorted(root.rglob('*'))
        if p.is_file() and p.suffix in TEXT_SUFFIXES
    }


def is_mirror(rel: str) -> bool:
    """A reference page copied from a source, as opposed to authored or generated files."""
    return (
        rel.startswith('references/')
        and rel.endswith('.md')
        and rel not in MIRROR_EXEMPT
        and not rel.startswith('references/examples/')
    )


def sizes(tree: dict[str, str]) -> dict[str, int]:
    tokens = {rel: count(text) for rel, text in tree.items() if rel.endswith('.md')}
    return {
        'total': sum(tokens.values()),
        'hub': tokens.get('SKILL.md', 0),
        'references': sum(t for r, t in tokens.items() if r.startswith('references/')),
        'mirror': sum(t for r, t in tokens.items() if is_mirror(r)),
    }


def original_dir(ws: Workspace, emitted: Path) -> Path:
    """The full emitted skill: its backup once a compaction was applied, else the live directory."""
    return ws.full_dir if ws.full_dir.is_dir() else emitted
