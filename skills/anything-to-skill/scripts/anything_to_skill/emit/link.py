import os
from pathlib import Path


def link_skill(target: Path, link: Path) -> Path:
    """Create a relative symlink link -> target; refuse to clobber an existing path."""
    target = Path(target).resolve()
    link = Path(link)
    link = link.parent.resolve() / link.name
    if os.path.lexists(link):
        if link.is_symlink() and link.resolve() == target:
            return link
        raise FileExistsError(f'refusing to clobber existing {link}')
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=True)
    return link
