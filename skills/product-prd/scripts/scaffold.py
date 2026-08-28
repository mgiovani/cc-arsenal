#!/usr/bin/env python3
"""Scaffold the PRD output.

DEFAULT: writes a single `docs/specs/prd/PRD.md`, seeded from
../assets/templates/prd-root.md when present, else a minimal stub. This is
the lean-by-default path — one file, split only when a section outgrows it.

--enterprise <tier>: opt in to the legacy multi-file tree (small=1, medium=12,
big=37 files) for platform-scale programs that genuinely need the split. Only
reach for this when a single PRD.md has demonstrably outgrown itself.

Idempotent: never overwrites a file that already exists and is non-empty.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_DIR = 'docs/specs/prd'
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'templates'

# 00..27 — the full "big" enterprise document set (order matches the numbering).
_BIG_NUMBERED = [
    '00-executive-summary',
    '01-product-context',
    '02-problem-and-opportunity',
    '03-users-personas-and-jobs',
    '04-market-and-competitive-landscape',
    '05-goals-success-and-non-goals',
    '06-product-principles',
    '07-scope-and-release-boundaries',
    '08-user-journeys-and-experience',
    '09-functional-requirements',
    '10-non-functional-requirements',
    '11-domain-model-and-business-rules',
    '12-system-architecture',
    '13-data-architecture',
    '14-apis-events-and-integrations',
    '15-security-privacy-and-compliance',
    '16-observability-reliability-and-operations',
    '17-ai-and-automation-requirements',
    '18-platform-and-client-requirements',
    '19-accessibility-and-internationalization',
    '20-analytics-metrics-and-experimentation',
    '21-rollout-migration-and-adoption',
    '22-testing-and-quality-strategy',
    '23-risks-dependencies-and-mitigations',
    '24-decisions-assumptions-and-open-questions',
    '25-roadmap-and-delivery-phases',
    '26-acceptance-criteria-and-launch-readiness',
    '27-glossary',
]

_BIG_APPENDICES = [
    'appendices/repository-discovery.md',
    'appendices/research-plan.md',
    'appendices/research-ledger.md',
    'appendices/competitor-analysis.md',
    'appendices/technical-options-analysis.md',
    'appendices/requirements-traceability.md',
    'appendices/current-vs-target-state.md',
    'appendices/source-index.md',
]


def enterprise_tier_files(tier: str) -> list[str]:
    """The relative file list an --enterprise size tier produces."""
    if tier == 'small':
        return ['PRD.md']
    if tier == 'medium':
        return [
            'PRD.md',
            '01-product-context.md',
            '03-users-personas-and-jobs.md',
            '05-goals-success-and-non-goals.md',
            '07-scope-and-release-boundaries.md',
            '09-functional-requirements.md',
            '10-non-functional-requirements.md',
            '12-system-architecture.md',
            '23-risks-dependencies-and-mitigations.md',
            '24-decisions-assumptions-and-open-questions.md',
            'appendices/research-ledger.md',
            'appendices/requirements-traceability.md',
        ]
    if tier == 'big':
        return ['PRD.md'] + [f'{name}.md' for name in _BIG_NUMBERED] + _BIG_APPENDICES
    raise ValueError(f'unknown tier: {tier!r}')


def target_files(enterprise: bool, tier: str | None) -> list[str]:
    """Resolve the file list. Default (not enterprise) is always a single PRD.md."""
    if not enterprise:
        return ['PRD.md']
    return enterprise_tier_files(tier or 'big')


def derive_heading(relpath: str) -> str:
    """Filename -> heading: strip NN- prefix, '-' -> space, title-case."""
    if relpath == 'PRD.md':
        return 'PRD'
    stem = re.sub(r'^\d+-', '', Path(relpath).stem)
    return stem.replace('-', ' ').title()


def seed_content(relpath: str, enterprise: bool) -> str:
    """Seed a file. The lean default PRD.md is a clean stub the agent fills from
    the tier template (brief/one-pager/prfaq/prd-full). Only the --enterprise
    PRD.md is seeded from prd-root.md, which is the multi-file index root."""
    if relpath == 'PRD.md' and enterprise:
        template = TEMPLATES_DIR / 'prd-root.md'
        if template.is_file():
            try:
                return template.read_text()
            except OSError as exc:
                # Template exists but isn't readable (permissions, a race with
                # a concurrent delete, etc.) -- note it on stderr and fall
                # through to the generic stub below rather than crash the
                # whole scaffold over one unreadable template.
                sys.stderr.write(f'warning: could not read {template}: {exc}\n')
    heading = derive_heading(relpath)
    return f'# {heading}\n\n<!-- scaffolded by product-prd -->\n'


def scaffold(
    target_dir: Path, *, enterprise: bool = False, tier: str | None = None
) -> tuple[list[str], list[str]]:
    """Create the target files under target_dir. Returns (created, skipped) relpaths."""
    created: list[str] = []
    skipped: list[str] = []
    for relpath in target_files(enterprise, tier):
        path = target_dir / relpath
        if path.is_file() and path.stat().st_size > 0:
            skipped.append(relpath)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(seed_content(relpath, enterprise))
        created.append(relpath)
    return created, skipped


def _selftest() -> bool:
    # Default path is always ONE file.
    assert target_files(enterprise=False, tier=None) == ['PRD.md']
    # tier ignored without --enterprise
    assert target_files(enterprise=False, tier='big') == ['PRD.md']
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / 'prd'
        created, skipped = scaffold(target)
        assert created == ['PRD.md'], created
        assert skipped == []
        created2, skipped2 = scaffold(target)
        assert created2 == [], created2
        assert skipped2 == ['PRD.md'], skipped2

    # --enterprise trees keep the legacy counts.
    expected_counts = {'small': 1, 'medium': 12, 'big': 37}
    for tier, expected in expected_counts.items():
        assert len(enterprise_tier_files(tier)) == expected, (
            tier,
            len(enterprise_tier_files(tier)),
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'prd'
            created, skipped = scaffold(target, enterprise=True, tier=tier)
            assert len(created) == expected, (
                f'{tier}: expected {expected}, got {len(created)}'
            )
            assert skipped == []
            created2, skipped2 = scaffold(target, enterprise=True, tier=tier)
            assert created2 == [], f'{tier}: second run created {created2}'
            assert len(skipped2) == expected
    print('OK')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'tier',
        nargs='?',
        choices=['small', 'medium', 'big'],
        help='only meaningful with --enterprise',
    )
    parser.add_argument(
        '--enterprise',
        action='store_true',
        help='opt in to the legacy multi-file tree (default: one PRD.md)',
    )
    parser.add_argument('--dir', default=DEFAULT_DIR, help='target PRD directory')
    parser.add_argument(
        '--title', default=None, help='unused placeholder for future seeding'
    )
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1

    if args.enterprise and not args.tier:
        parser.error('--enterprise requires a tier (small|medium|big)')

    target = Path(args.dir)
    created, skipped = scaffold(target, enterprise=args.enterprise, tier=args.tier)
    mode = f'enterprise/{args.tier}' if args.enterprise else 'default (single PRD.md)'
    print(f'Scaffolded {mode} into {target}')
    print(f'  created ({len(created)}):')
    for r in created:
        print(f'    + {r}')
    print(f'  skipped, already present ({len(skipped)}):')
    for r in skipped:
        print(f'    = {r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
