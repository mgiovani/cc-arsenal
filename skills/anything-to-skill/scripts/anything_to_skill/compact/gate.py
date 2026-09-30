"""The compaction eval gate: the one place the accept rule lives."""

import argparse
import json
import sys
from typing import Any

from anything_to_skill.core.workspace import Workspace

MAX_NONE = 0.8
MAX_LOSS = 0.05
MIN_GAIN = 0.1
_EPS = 1e-9


def add_args(parser: argparse.ArgumentParser) -> None:
    for name in ('none', 'full', 'compact'):
        parser.add_argument(
            f'--{name}',
            type=float,
            required=True,
            metavar='RATE',
            help=f'pass rate (0-1) of the {name} run on the frozen evals',
        )
    parser.add_argument(
        '--lost',
        action='append',
        default=[],
        metavar='TEXT',
        help='an assertion the full skill passed and compact failed (repeatable)',
    )


def decide(none: float, full: float, compact: float) -> dict[str, Any]:
    """Accept iff compact is within 0.05 of full and at least 0.1 above no skill."""
    if none > MAX_NONE + _EPS:
        decision = 'strengthen-evals'
    elif compact < full - MAX_LOSS - _EPS:
        decision = 'reject-lost-too-much'
    elif compact - none < MIN_GAIN - _EPS:
        decision = 'reject-no-gain-over-none'
    else:
        decision = 'accept'
    return {
        'decision': decision,
        'accepted': decision == 'accept',
        'pass_rates': {'none': none, 'full': full, 'compact': compact},
    }


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py compact-gate`: print and record the accept decision; non-zero unless accepted."""
    rates = (args.none, args.full, args.compact)
    if not all(0 <= r <= 1 for r in rates):
        print('compact-gate: pass rates are fractions between 0 and 1', file=sys.stderr)
        return 2
    report = decide(*rates)
    report['lost_assertions'] = args.lost
    try:
        report['tokens'] = json.loads(ws.compact_verify_path.read_text('utf-8'))['tokens']
    except (OSError, ValueError, KeyError):
        report['tokens'] = None
    ws.compact_gate_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    tokens = report['tokens']
    saved = (
        f'tokens {tokens["before"]} -> {tokens["after"]} ({tokens["saved_pct"]}% saved)'
        if tokens
        else 'tokens: run compact-verify for the savings'
    )
    print(
        f'compact-gate: {report["decision"]} '
        f'(none {args.none}, full {args.full}, compact {args.compact}); '
        f'{len(args.lost)} lost assertion(s); {saved} -> {ws.compact_gate_path}'
    )
    for text in args.lost:
        print(f'  lost: {text}')
    if report['decision'] == 'strengthen-evals':
        print(
            f'compact-gate: no-skill pass rate above {MAX_NONE}: the evals do not measure '
            'the skill; strengthen them, evals-freeze --force, re-run all three',
            file=sys.stderr,
        )
    return 0 if report['accepted'] else 1
