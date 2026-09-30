import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from anything_to_skill.core.models import EFFORT_BUDGET
from anything_to_skill.core.store import Store

_SLUG = re.compile(r'^[a-z0-9][a-z0-9._-]*$')


class WorkspaceError(Exception):
    pass


@dataclass(frozen=True)
class Workspace:
    """A skill build's working directory: .cc-arsenal/a2s/<slug>/ under the project."""

    dir: Path

    @property
    def slug(self) -> str:
        return self.dir.name

    @property
    def plan_path(self) -> Path:
        return self.dir / 'plan.json'

    @property
    def judge_path(self) -> Path:
        return self.dir / 'judge.json'

    @property
    def review_path(self) -> Path:
        return self.dir / 'review.md'

    @property
    def verify_path(self) -> Path:
        return self.dir / 'verify.json'

    @property
    def authored_dir(self) -> Path:
        return self.dir / 'authored'

    @property
    def compact_dir(self) -> Path:
        return self.dir / 'compact'

    @property
    def full_dir(self) -> Path:
        return self.dir / 'full'

    @property
    def compact_brief_path(self) -> Path:
        return self.dir / 'compact-brief.md'

    @property
    def compact_verify_path(self) -> Path:
        return self.dir / 'compact-verify.json'

    @property
    def compact_gate_path(self) -> Path:
        return self.dir / 'compact-gate.json'

    @property
    def eval_prompts_path(self) -> Path:
        return self.dir / 'eval-prompts.json'

    @property
    def evals_frozen_path(self) -> Path:
        return self.dir / 'evals.frozen.json'

    @staticmethod
    def base_dir(base: Path | None = None) -> Path:
        return Path(base) if base else Path.cwd() / '.cc-arsenal' / 'a2s'

    @classmethod
    def create(cls, slug: str, base: Path | None = None) -> 'Workspace':
        if not _SLUG.match(slug):
            raise WorkspaceError(
                f'invalid slug {slug!r}: use lowercase letters, digits, . _ -'
            )
        ws = cls(cls.base_dir(base) / slug)
        ws.authored_dir.mkdir(parents=True, exist_ok=True)
        (ws.dir / 'md').mkdir(exist_ok=True)
        return ws

    @classmethod
    def find(cls, slug: str | None = None, base: Path | None = None) -> 'Workspace':
        root = cls.base_dir(base)
        if slug:
            if not _SLUG.match(slug) or not (root / slug / 'state.db').exists():
                raise WorkspaceError(
                    f'no workspace {slug!r} under {root}; run init first'
                )
            return cls(root / slug)
        found = sorted(p.parent for p in root.glob('*/state.db'))
        if len(found) != 1:
            raise WorkspaceError(
                f'{len(found)} workspaces under {root}; pass --slug'
                if found
                else f'no workspace under {root}; run init first'
            )
        return cls(found[0])

    def open_store(self) -> Store:
        return Store(self.dir)


@dataclass
class Ctx:
    """Everything a source's run(ctx, args) needs; goal/effort come from `a2s.py init`."""

    ws: Workspace
    store: Store
    goal: str = ''
    effort: str = 'standard'
    max_pages: int | None = None
    allow_private: bool = False

    @classmethod
    def open(
        cls,
        ws: Workspace,
        store: Store,
        max_pages: int | None = None,
        *,
        allow_private: bool = False,
    ) -> 'Ctx':
        return cls(
            ws=ws,
            store=store,
            goal=store.get_meta('goal', ''),
            effort=store.get_meta('effort', 'standard'),
            max_pages=max_pages,
            allow_private=allow_private,
        )

    @property
    def token_budget(self) -> int | None:
        return EFFORT_BUDGET.get(self.effort)

    def dropped_ids(self) -> set[int]:
        """Units the plan will not keep: `a2s drop` and judge.json's drops, which plan honors at
        every effort but `complete` (no budget there) and annotate-only."""
        ids = self.store.user_drops()
        try:
            judge = json.loads(self.ws.judge_path.read_text('utf-8'))
        except (OSError, ValueError):
            return ids
        if isinstance(judge, dict) and not judge.get('annotate_only'):
            ids |= {int(d['id']) for d in judge.get('drop', [])}
        return ids

    def spent_tokens(self) -> int:
        """Corpus tokens that count against the budget: dropped pages were fetched but the plan
        never keeps them, so they must not stop a crawl before the wanted pages arrive."""
        return self.store.token_total(exclude=self.dropped_ids())

    def over_budget(self) -> bool:
        budget = self.token_budget
        return budget is not None and self.spent_tokens() >= budget

    def log(self, message: str) -> None:
        print(message, file=sys.stderr)
