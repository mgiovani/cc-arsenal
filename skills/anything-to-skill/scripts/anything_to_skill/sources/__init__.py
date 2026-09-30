"""Lazy registry of source handlers.

Each name in NAMES is a subpackage with two modules kept apart on purpose:
``detect`` (stdlib only: NAME, detect(arg) -> int) and ``run`` (may pull heavy
dependencies: add_args(parser), run(ctx, args) -> RunSummary). Routing only ever
imports ``detect``, so a markdown folder never triggers an import of torch.
"""

import importlib
from types import ModuleType

# Tie-break order for equal scores; web is the fallback so it goes last.
NAMES = ('youtube', 'local', 'web')


def _module(name: str, part: str) -> ModuleType:
    if name not in NAMES:
        raise ValueError(f'unknown source {name!r}; expected one of {", ".join(NAMES)}')
    return importlib.import_module(f'anything_to_skill.sources.{name}.{part}')


def scores(arg: str) -> dict[str, int]:
    return {name: _module(name, 'detect').detect(arg) for name in NAMES}


def route(arg: str) -> tuple[str, int] | None:
    """Return (source name, score) of the highest scorer, or None when nothing matches."""
    ranked = scores(arg)
    best = max(NAMES, key=lambda n: ranked[n])
    return (best, ranked[best]) if ranked[best] > 0 else None


def load_run(name: str) -> ModuleType:
    return _module(name, 'run')
