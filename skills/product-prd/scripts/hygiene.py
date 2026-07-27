#!/usr/bin/env python3
"""Advisory requirement-hygiene helper (companion to validate.py).

Two lints, both advisory (always exits 0 — these are suggestions, not gates):

  SPLIT  — INVEST 'Small/Estimable' self-check: a normative statement that
           packs multiple obligations, comma-joins independent clauses, or runs
           long is flagged with a split suggestion.
  EARS   — for non-UI requirements (NFR/SEC/DATA) where Gherkin's user framing
           fits poorly, suggests an EARS rewrite (When/While/Where/If ... the
           system shall ...) when a trigger is buried mid-sentence or the
           normative verb is missing.

Findings print as `LABEL  file:line  message`. See references/requirement-hygiene.md.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

# Shared verbatim with validate.py (same directory, always shipped together): import
# rather than re-type so the six-category ID scheme and block parsing can never drift.
from validate import (
    COMMA_CONNECTOR_RE,
    OBLIGATION_RE,
    REQUIREMENT_ID_RE,
    find_requirement_blocks,
)

DEFAULT_DIR = 'docs/specs/prd'
MAX_STATEMENT_WORDS = 30

EARS_LEAD_RE = re.compile(r'^\s*(When|While|Where|If)\b', re.IGNORECASE)
TRIGGER_RE = re.compile(
    r'\b(when|if|while|after|before|upon|once|during)\b', re.IGNORECASE
)

# Categories whose behaviour is system/non-UI, where EARS beats Gherkin.
NON_UI_CATEGORIES = {'NFR', 'SEC', 'DATA'}


def statement_of(block: dict) -> tuple[int, str] | None:
    """The normative statement = first body line carrying an obligation keyword.
    (Acceptance-criteria lines use Given/When/Then without MUST, so they are skipped.)"""
    for line_no, text in block['body']:
        if OBLIGATION_RE.search(text):
            return line_no, text
    return None


def lint_block(path: Path, block: dict) -> list[tuple]:
    findings: list[tuple] = []
    m = REQUIREMENT_ID_RE.search(block['heading'])
    if not m:
        return findings
    req_id, category = m.group(0), m.group(1)
    stmt = statement_of(block)

    if stmt is not None:
        line_no, text = stmt
        obligations = OBLIGATION_RE.findall(text)
        if len(obligations) >= 2:
            findings.append(
                (
                    'SPLIT',
                    path,
                    line_no,
                    f'{req_id}: {len(obligations)} obligations in one statement — split into {len(obligations)} requirements',
                )
            )
        elif COMMA_CONNECTOR_RE.search(text):
            findings.append(
                (
                    'SPLIT',
                    path,
                    line_no,
                    f'{req_id}: comma-joined clauses — split into independent requirements',
                )
            )
        elif len(text.split()) > MAX_STATEMENT_WORDS:
            findings.append(
                (
                    'SPLIT',
                    path,
                    line_no,
                    f'{req_id}: statement is {len(text.split())} words — likely not Small/Estimable, consider splitting',
                )
            )

    if category in NON_UI_CATEGORIES:
        if stmt is None:
            findings.append(
                (
                    'EARS',
                    path,
                    block['line'],
                    f"{req_id}: non-UI requirement has no normative verb — state it with 'shall'/'must' in an EARS clause",
                )
            )
        else:
            line_no, text = stmt
            if not EARS_LEAD_RE.match(text) and TRIGGER_RE.search(text):
                findings.append(
                    (
                        'EARS',
                        path,
                        line_no,
                        f"{req_id}: buried trigger — lead with EARS 'When <trigger>, the system shall <response>'",
                    )
                )
    return findings


def lint_tree(target_dir: Path) -> list[tuple]:
    findings: list[tuple] = []
    if not target_dir.is_dir():
        return findings
    for path in sorted(target_dir.rglob('*.md')):
        lines = path.read_text(errors='replace').splitlines()
        for block in find_requirement_blocks(lines):
            findings.extend(lint_block(path, block))
    return findings


def format_findings(findings: list[tuple], root: Path) -> str:
    ordered = sorted(findings, key=lambda f: (f[0], str(f[1]), f[2]))
    out = [
        f'{label:<6} {path.relative_to(root)}:{line}  {msg}'
        for label, path, line, msg in ordered
    ]
    splits = sum(1 for f in findings if f[0] == 'SPLIT')
    ears = sum(1 for f in findings if f[0] == 'EARS')
    out.append('')
    out.append(f'SPLIT={splits}  EARS={ears}  (advisory)')
    return '\n'.join(out)


def _selftest() -> bool:
    fixture = """# PRD

## Functional Requirements

### PRD-FR-001: Clean login

The system MUST authenticate the user via email and password.

### PRD-FR-002: Compound

The system MUST log the user in and MUST send a confirmation email.

## Non-Functional Requirements

### PRD-NFR-001: Buried trigger

The system MUST respond within 200 ms when the cache is warm.
"""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / 'prd'
        target.mkdir()
        (target / 'PRD.md').write_text(fixture)
        findings = lint_tree(target)
        labels = [f[0] for f in findings]
        # FR-001 clean -> nothing; FR-002 two MUST -> 1 SPLIT; NFR-001 buried 'when' -> 1 EARS
        assert labels.count('SPLIT') == 1, findings
        assert labels.count('EARS') == 1, findings
        assert any('PRD-FR-002' in f[3] for f in findings if f[0] == 'SPLIT'), findings
        assert any('PRD-NFR-001' in f[3] for f in findings if f[0] == 'EARS'), findings
        format_findings(findings, target)  # must not raise
    print('OK')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', default=DEFAULT_DIR, help='PRD directory to lint')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1

    findings = lint_tree(Path(args.dir))
    print(format_findings(findings, Path(args.dir)))
    return 0  # advisory: never fails the build


if __name__ == '__main__':
    sys.exit(main())
