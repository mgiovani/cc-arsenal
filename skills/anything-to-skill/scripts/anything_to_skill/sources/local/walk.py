import os
from pathlib import Path

PASSTHROUGH = {'.md', '.markdown', '.txt', '.rst'}
CONVERT = {'.pdf', '.docx', '.pptx', '.epub', '.html', '.htm', '.png', '.jpg', '.jpeg'}

SKIP_DIRS = {'node_modules', '__pycache__'}


def walk(root: Path) -> list[Path]:
    """Supported files under root (or root itself), deterministic order.

    Hidden entries, dependency dirs and symlinks are skipped so a folder crawl never
    escapes the tree it was pointed at; an explicitly named file is always accepted.
    """
    root = root.expanduser().resolve()
    supported = PASSTHROUGH | CONVERT
    if root.is_file():
        return [root] if root.suffix.lower() in supported else []
    found = []
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
        for name in names:
            path = Path(dirpath) / name
            if (
                not name.startswith('.')
                and path.suffix.lower() in supported
                and not path.is_symlink()
            ):
                found.append(path)
    return sorted(found)
