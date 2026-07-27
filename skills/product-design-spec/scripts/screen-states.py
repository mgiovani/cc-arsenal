#!/usr/bin/env python3
"""Lint the critical screen specs in a design spec.

A "critical screen" is any section whose heading carries a screen id (SCR-NN).
For each one this checks that it:

  - covers the commonly-forgotten state trio — an empty state, an error state
    (validation-error or recoverable-error), and a permission-denied state —
    each either documented or explicitly marked N/A (MAJOR if simply absent);
  - carries an accessibility/keyboard field, a responsive field, and an
    acceptance-criteria field (MAJOR if missing);
  - traces to at least one PRD requirement id (MAJOR if it traces to nothing).

Plus one advisory: more than 3 full screen specs trips a MINOR "over-spec" note,
because lean-by-default expects only the 2-3 most critical screens to be specced
in full — the rest stay one-line inventory rows.

Inventory rows (table cells, not headings) are not screen blocks and are skipped,
so the same file holds a big inventory and a few full specs without noise.

Findings print as `SEVERITY  file:line  message`; exits nonzero on any MAJOR.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_DIR = 'docs/specs/design'
MAX_FULL_SPECS = 3

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
# A full screen spec is a heading that carries a screen id, e.g. "### SCR-01 — Login".
SCREEN_HEADING_RE = re.compile(r'\bSCR-[A-Za-z0-9]+\b')
REQUIREMENT_ID_RE = re.compile(r'\bPRD-(FR|NFR|UX|SEC|DATA|DES)-\d{3,}\b')

# State keywords (searched case-insensitively over the block body). "N/A" next to
# a state keyword still counts as covered — the author consciously addressed it.
EMPTY_RE = re.compile(r'\bempty\b', re.IGNORECASE)
ERROR_RE = re.compile(
    r'\b(validation[\s-]?error|recoverable[\s-]?error|error)\b', re.IGNORECASE
)
PERMISSION_RE = re.compile(r'\bpermission(?:[\s-]?denied|s)?\b', re.IGNORECASE)

A11Y_RE = re.compile(r'\b(accessibility|keyboard|a11y)\b', re.IGNORECASE)
RESPONSIVE_RE = re.compile(r'\b(responsive|breakpoint|size class)\b', re.IGNORECASE)
ACCEPTANCE_RE = re.compile(r'acceptance criteria', re.IGNORECASE)

SEVERITY_ORDER = {'MAJOR': 0, 'MINOR': 1}


def find_screen_blocks(lines: list[str]) -> list[dict]:
    """Split into blocks that start at a heading carrying a screen id (SCR-NN).

    A block's body runs until the next heading of any level, so bold-label fields
    (**States**, **Responsive**, ...) inside the screen stay attached to it.
    Non-screen headings close any open block without opening a new one.
    """
    blocks: list[dict] = []
    current: dict | None = None
    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            if current is not None:
                blocks.append(current)
                current = None
            sid_match = SCREEN_HEADING_RE.search(m.group(2))
            if sid_match:
                current = {
                    'line': i,
                    'id': sid_match.group(0),
                    'heading': m.group(2).strip(),
                    'body': [],
                }
            continue
        if current is not None:
            current['body'].append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def lint_block(path: Path, block: dict) -> list[tuple]:
    findings: list[tuple] = []
    sid, line, body = block['id'], block['line'], '\n'.join(block['body'])

    def major(msg: str) -> None:
        findings.append(('MAJOR', path, line, f'{sid}: {msg}'))

    if not EMPTY_RE.search(body):
        major('no empty state — document it or mark it N/A with a reason')
    if not ERROR_RE.search(body):
        major('no error state (validation or recoverable) — document it or mark N/A')
    if not PERMISSION_RE.search(body):
        major('no permission-denied state — document it or mark it N/A with a reason')
    if not A11Y_RE.search(body):
        major('missing accessibility/keyboard field')
    if not RESPONSIVE_RE.search(body):
        major('missing responsive field')
    if not ACCEPTANCE_RE.search(body):
        major('missing acceptance-criteria field')
    if not REQUIREMENT_ID_RE.search(body):
        major('traces to no PRD requirement id (PRD-<CAT>-NNN)')
    return findings


def lint_tree(target_dir: Path) -> list[tuple]:
    findings: list[tuple] = []
    if not target_dir.is_dir():
        return findings
    full_specs = 0
    first_path: Path | None = None
    for path in sorted(target_dir.rglob('*.md')):
        lines = path.read_text(errors='replace').splitlines()
        blocks = find_screen_blocks(lines)
        for block in blocks:
            findings.extend(lint_block(path, block))
        full_specs += len(blocks)
        if blocks and first_path is None:
            first_path = path
    if full_specs > MAX_FULL_SPECS and first_path is not None:
        findings.append(
            (
                'MINOR',
                first_path,
                1,
                f'{full_specs} full screen specs — lean-by-default expects only the 2-3 most '
                'critical screens get full specs; keep the rest as one-line inventory rows',
            )
        )
    return findings


def format_findings(findings: list[tuple], root: Path) -> tuple[str, dict]:
    ordered = sorted(findings, key=lambda f: (SEVERITY_ORDER[f[0]], str(f[1]), f[2]))
    lines = [
        f'{sev:<6} {path.relative_to(root)}:{line}  {msg}'
        for sev, path, line, msg in ordered
    ]
    counts = {'MAJOR': 0, 'MINOR': 0}
    for sev, *_ in findings:
        counts[sev] += 1
    lines.append('')
    lines.append(f'MAJOR={counts["MAJOR"]}  MINOR={counts["MINOR"]}')
    lines.append('READY' if counts['MAJOR'] == 0 else 'NOT READY')
    return '\n'.join(lines), counts


def _selftest() -> bool:
    expected_major, expected_minor = 6, 0
    good = """# Design Spec

## Screen inventory

| Screen ID | Name | Traces to |
|---|---|---|
| SCR-03 | Settings | PRD-UX-004 |

## Critical screen specs

### SCR-01 — Login

**States**

| State | Behaviour |
|---|---|
| loading | spinner |
| empty | first-load prompt |
| populated | credential form |
| validation-error | inline field errors |
| permission-denied | locked-account notice |
| success | redirect to dashboard |

**Accessibility / keyboard** — full keyboard nav, visible focus, 24px targets.
**Responsive** — mobile 360 / tablet / desktop.
**Acceptance criteria** — Given valid creds, when submit, then logged in.
**Traces to** — PRD-FR-001, PRD-UX-002.

### SCR-02 — Dashboard

**States**

| State | Behaviour |
|---|---|
| loading | skeleton |
| populated | widgets |

**Acceptance criteria** — Given data, when loaded, then widgets shown.
"""
    # SCR-03 is a table row (inventory), not a heading -> skipped.
    # SCR-01 is complete -> 0 findings.
    # SCR-02 is missing empty, error, permission, a11y, responsive, traces -> 6 MAJOR.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / 'design'
        d.mkdir()
        (d / 'design-spec.md').write_text(good)
        findings = lint_tree(d)
        sevs = [f[0] for f in findings]
        assert sevs.count('MAJOR') == expected_major, findings
        assert sevs.count('MINOR') == expected_minor, findings
        scr2 = [f for f in findings if 'SCR-02' in f[3]]
        assert len(scr2) == expected_major, scr2
        assert all('SCR-01' not in f[3] for f in findings), findings
        text, _ = format_findings(findings, d)
        assert 'NOT READY' in text

    # Over-spec: 4 complete screens -> 0 MAJOR, 1 MINOR advisory.
    one = """### SCR-{n} — Screen {n}

**States**: loading, empty, populated, validation-error, permission-denied, success.
**Accessibility / keyboard** — keyboard nav.
**Responsive** — mobile / desktop.
**Acceptance criteria** — Given x, when y, then z.
**Traces to** — PRD-FR-00{n}.
"""
    screens = '\n'.join(one.replace('{n}', str(k)) for k in range(1, 5))
    over = '# Design Spec\n\n' + screens
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / 'design'
        d.mkdir()
        (d / 'design-spec.md').write_text(over)
        findings = lint_tree(d)
        sevs = [f[0] for f in findings]
        assert sevs.count('MAJOR') == 0, findings
        assert sevs.count('MINOR') == 1, findings
        assert any('full screen specs' in f[3] for f in findings), findings

    sys.stdout.write('OK\n')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', default=DEFAULT_DIR, help='design-spec dir to lint')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1

    target = Path(args.dir)
    findings = lint_tree(target)
    text, counts = format_findings(findings, target)
    sys.stdout.write(text + '\n')
    return 1 if counts['MAJOR'] else 0


if __name__ == '__main__':
    sys.exit(main())
