#!/usr/bin/env python3
"""Validate a PRD: bad/duplicate IDs, missing acceptance criteria, leftover
placeholders, dangling links, vague requirement terms, a missing Non-Goals
section (mandatory at medium+), unresolved [NEEDS CLARIFICATION] tags, and
compound requirements that pack multiple behaviours into one statement.
Findings print as `SEVERITY  file:line  message`; exits nonzero on
CRITICAL/MAJOR."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_DIR = 'docs/specs/prd'

# Six categories only: FR/NFR/UX/SEC/DATA here, plus DES owned by product-design-spec.
REQUIREMENT_ID_RE = re.compile(r'PRD-(FR|NFR|UX|SEC|DATA|DES)-\d{3,}')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
# Brief (SMALL) tier states each requirement as a list item led by a bold ID,
# e.g. `1. **PRD-FR-001** (Given ...)`; register those as requirement blocks too.
LIST_ITEM_ID_RE = re.compile(
    r'^\s*(?:[-*+]|\d+[.)])\s+\*\*(PRD-(?:FR|NFR|UX|SEC|DATA|DES)-\d{3,})\*\*'
)
PLACEHOLDER_RE = re.compile(r'\{\{[^}]*\}\}')
TODO_RE = re.compile(r'\b(TODO|TBD|FIXME)\b')
# The full eight-term vague-word blocklist (kept in sync with requirement-hygiene.md).
VAGUE_TERM_RE = re.compile(
    r'\b(fast|scalable|intuitive|robust|secure|seamless|user-friendly|performant)\b',
    re.IGNORECASE,
)
NEEDS_CLARIFICATION_RE = re.compile(r'\[NEEDS CLARIFICATION', re.IGNORECASE)
# Obligation keywords, longest-form first so "MUST NOT" counts as one, not two.
OBLIGATION_RE = re.compile(r'\b(MUST NOT|MUST|SHALL NOT|SHALL|SHOULD NOT|SHOULD)\b')
COMMA_CONNECTOR_RE = re.compile(r',\s+(and|or)\s+', re.IGNORECASE)
NON_GOALS_HEADING_RE = re.compile(r'non[\s-]?goals?', re.IGNORECASE)
LINK_RE = re.compile(r'\]\(([^)]+)\)')
URL_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*:')
GWT_KEYWORDS = ('given', 'when', 'then')

SEVERITY_ORDER = {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}


def _is_requirement_file(path: Path) -> bool:
    """Files where a bare (no-ID) H3 heading counts as a broken requirement."""
    name = path.name.lower()
    return name == 'prd.md' or 'functional-requirements' in name


def find_requirement_blocks(lines: list[str]) -> list[dict]:
    """Split into blocks starting at each H3 heading (only H1-H3 close a block, so
    an H4+ subheading stays part of the requirement body). Brief-tier requirements
    written as bold-ID list items become their own single-line blocks."""
    blocks: list[dict] = []
    current: dict | None = None
    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) <= 3:
            if current is not None:
                blocks.append(current)
                current = None
            if len(m.group(1)) == 3:
                current = {'line': i, 'heading': m.group(2).strip(), 'body': []}
            continue
        # H4+ headings and normal lines are body content of the open block.
        if current is not None:
            current['body'].append((i, line))
        elif LIST_ITEM_ID_RE.match(line):
            blocks.append({'line': i, 'heading': line.strip(), 'body': [(i, line)]})
    if current is not None:
        blocks.append(current)
    return blocks


def check_placeholders(path: Path, lines: list[str]) -> list[tuple]:
    findings = []
    for i, line in enumerate(lines, start=1):
        if PLACEHOLDER_RE.search(line):
            findings.append(
                ('CRITICAL', path, i, 'leftover template placeholder {{...}}')
            )
        if TODO_RE.search(line):
            findings.append(('CRITICAL', path, i, 'leftover TODO/TBD/FIXME marker'))
        if NEEDS_CLARIFICATION_RE.search(line):
            findings.append(
                (
                    'MAJOR',
                    path,
                    i,
                    'unresolved [NEEDS CLARIFICATION] tag — resolve before hand-off',
                )
            )
    return findings


def check_links(path: Path, lines: list[str]) -> list[tuple]:
    findings = []
    for i, line in enumerate(lines, start=1):
        for m in LINK_RE.finditer(line):
            target = m.group(1).strip()
            if not target or target.startswith('#') or URL_SCHEME_RE.match(target):
                continue
            target_path = target.split('#', 1)[0].strip()
            if not target_path:
                continue
            resolved = (path.parent / target_path).resolve()
            if not resolved.is_file():
                findings.append(('MAJOR', path, i, f'dangling link -> {target}'))
    return findings


def check_requirement_blocks(
    path: Path, lines: list[str]
) -> tuple[list[tuple], list[tuple[str, Path, int]]]:
    """Returns (findings, [(req_id, path, line), ...]) for duplicate-ID tracking."""
    findings = []
    id_hits: list[tuple[str, Path, int]] = []
    is_req_file = _is_requirement_file(path)
    for block in find_requirement_blocks(lines):
        m = REQUIREMENT_ID_RE.search(block['heading'])
        if not m:
            if is_req_file:
                findings.append(
                    (
                        'CRITICAL',
                        path,
                        block['line'],
                        f'requirement heading with no valid ID: {block["heading"]!r}',
                    )
                )
            continue
        req_id = m.group(0)
        id_hits.append((req_id, path, block['line']))
        body_text = '\n'.join(text for _, text in block['body'])
        # AC present via the explicit label OR a label-less Given/When/Then
        # criterion (the condensed requirement shape used by the templates).
        has_label = bool(re.search(r'acceptance criteria', body_text, re.IGNORECASE))
        has_gwt = all(
            re.search(rf'\b{kw}\b', body_text, re.IGNORECASE) for kw in GWT_KEYWORDS
        )
        if not has_label and not has_gwt:
            findings.append(
                (
                    'MAJOR',
                    path,
                    block['line'],
                    f'{req_id}: missing Acceptance Criteria section',
                )
            )
        elif not has_gwt:
            findings.append(
                (
                    'MAJOR',
                    path,
                    block['line'],
                    f'{req_id}: acceptance criteria missing Given/When/Then',
                )
            )
        for line_no, text in block['body']:
            for vm in VAGUE_TERM_RE.finditer(text):
                findings.append(
                    ('MINOR', path, line_no, f'{req_id}: vague term {vm.group(0)!r}')
                )
            # Compound-requirement detection, scoped to normative (obligation) lines.
            obligations = OBLIGATION_RE.findall(text)
            if len(obligations) >= 2:
                findings.append(
                    (
                        'MAJOR',
                        path,
                        line_no,
                        f'{req_id}: compound requirement — {len(obligations)} obligations in one statement; split them',
                    )
                )
            elif obligations and COMMA_CONNECTOR_RE.search(text):
                findings.append(
                    (
                        'MINOR',
                        path,
                        line_no,
                        f'{req_id}: possible compound requirement (comma-joined clauses); consider splitting',
                    )
                )
    return findings, id_hits


def check_non_goals(
    md_paths: list[Path], texts: dict[Path, str], tier: str | None
) -> list[tuple]:
    """A Non-Goals section is mandatory at medium+; MINOR-only at the small tier."""
    if not md_paths:
        return []
    for text in texts.values():
        for line in text.splitlines():
            hm = HEADING_RE.match(line)
            if hm and NON_GOALS_HEADING_RE.search(hm.group(2)):
                return []
    severity = 'MINOR' if tier == 'small' else 'MAJOR'
    return [
        (
            severity,
            md_paths[0],
            1,
            'no Non-Goals section found — non-goals are mandatory at medium+ and expected at every tier',
        )
    ]


def validate_tree(target_dir: Path, tier: str | None = None) -> list[tuple]:
    findings: list[tuple] = []
    id_locations: dict[str, list[tuple[Path, int]]] = {}
    if not target_dir.is_dir():
        return findings

    md_paths = sorted(target_dir.rglob('*.md'))
    texts: dict[Path, str] = {}
    for path in md_paths:
        text = path.read_text(errors='replace')
        texts[path] = text
        lines = text.splitlines()
        findings.extend(check_placeholders(path, lines))
        findings.extend(check_links(path, lines))
        block_findings, id_hits = check_requirement_blocks(path, lines)
        findings.extend(block_findings)
        for req_id, hit_path, line in id_hits:
            id_locations.setdefault(req_id, []).append((hit_path, line))

    findings.extend(check_non_goals(md_paths, texts, tier))

    for req_id, locations in id_locations.items():
        if len(locations) > 1:
            first_path, first_line = locations[0]
            for hit_path, line in locations[1:]:
                findings.append(
                    (
                        'CRITICAL',
                        hit_path,
                        line,
                        f'duplicate requirement ID {req_id} (first seen {first_path.name}:{first_line})',
                    )
                )
    return findings


def format_findings(findings: list[tuple], root: Path) -> tuple[str, dict]:
    ordered = sorted(findings, key=lambda f: (SEVERITY_ORDER[f[0]], str(f[1]), f[2]))
    lines = [
        f'{sev:<8} {path.relative_to(root)}:{line}  {msg}'
        for sev, path, line, msg in ordered
    ]

    counts = {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0}
    for sev, *_ in findings:
        counts[sev] += 1
    lines.append('')
    lines.append(
        f'CRITICAL={counts["CRITICAL"]}  MAJOR={counts["MAJOR"]}  MINOR={counts["MINOR"]}'
    )
    lines.append(
        'READY' if counts['CRITICAL'] == 0 and counts['MAJOR'] == 0 else 'NOT READY'
    )
    return '\n'.join(lines), counts


def _selftest() -> bool:
    good = """# PRD

## Non-Goals

- Offline mode is out of scope for v1.

## Functional Requirements

### PRD-FR-001: User login

The system MUST authenticate the user via email and password.

**Acceptance criteria**

1. Given a registered user, when they submit valid credentials, then they are logged in.

### PRD-FR-002: Password reset

The system MUST send a password-reset email on request.

#### Detail notes

1. Given a registered user, when they request a reset, then an email is sent.
"""
    bad = """# PRD

## Functional Requirements

### PRD-FR-001: Login and notify

The system MUST log the user in and MUST send a confirmation email.
This should be fast and scalable. [NEEDS CLARIFICATION: which provider?]

**Acceptance criteria**

1. Given a user, when they log in, then a session starts.

### Bare Heading

Some text with a {{placeholder}} and a link to [notes](missing-notes.md).
"""
    with tempfile.TemporaryDirectory() as tmp:
        good_dir = Path(tmp) / 'good'
        good_dir.mkdir()
        (good_dir / 'PRD.md').write_text(good)
        good_findings = validate_tree(good_dir)
        good_counts = {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0}
        for sev, *_ in good_findings:
            good_counts[sev] += 1
        assert good_counts == {'CRITICAL': 0, 'MAJOR': 0, 'MINOR': 0}, good_findings

        bad_dir = Path(tmp) / 'bad'
        bad_dir.mkdir()
        (bad_dir / 'PRD.md').write_text(bad)
        bad_findings = validate_tree(bad_dir)
        bad_sevs = [f[0] for f in bad_findings]
        # CRITICAL: {{placeholder}} + bare no-ID heading = 2
        assert bad_sevs.count('CRITICAL') == 2, bad_findings
        # MAJOR: dangling link + compound (2 MUST) + [NEEDS CLARIFICATION] + missing Non-Goals = 4
        assert bad_sevs.count('MAJOR') == 4, bad_findings
        # MINOR: vague 'fast' + vague 'scalable' = 2
        assert bad_sevs.count('MINOR') == 2, bad_findings
        text, counts = format_findings(bad_findings, bad_dir)
        assert 'NOT READY' in text

        # small tier downgrades the missing-Non-Goals finding to MINOR
        small_findings = validate_tree(bad_dir, tier='small')
        assert [f for f in small_findings if 'Non-Goals' in f[3]][0][0] == 'MINOR', (
            small_findings
        )

        # brief (SMALL) tier: requirements are bold-ID list items, not H3 headings.
        # Label-less GWT satisfies AC presence; a non-goal that only mentions an ID
        # is NOT a requirement; a list-item requirement with no GWT is still caught.
        brief = """# Feature brief

## Non-Goals

- Bulk import lives in PRD-FR-050.

## Acceptance criteria

1. **PRD-FR-001** - Given a user, when they click export, then a CSV downloads.
2. **PRD-FR-002** - the system exports data.
"""
        brief_dir = Path(tmp) / 'brief'
        brief_dir.mkdir()
        (brief_dir / 'PRD.md').write_text(brief)
        brief_findings = validate_tree(brief_dir, tier='small')
        assert [f[0] for f in brief_findings].count('CRITICAL') == 0, brief_findings
        # Only PRD-FR-002 (no GWT) trips missing-AC; PRD-FR-001 passes on label-less
        # GWT, and the PRD-FR-050 non-goal reference is never treated as an ID hit.
        major = [f for f in brief_findings if f[0] == 'MAJOR']
        assert len(major) == 1, brief_findings
        assert 'PRD-FR-002' in major[0][3], major
        assert not any('PRD-FR-050' in f[3] for f in brief_findings), brief_findings

    print('OK')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', default=DEFAULT_DIR, help='PRD directory to validate')
    parser.add_argument(
        '--tier',
        choices=['small', 'medium', 'big'],
        default=None,
        help='downgrades the missing-Non-Goals finding to MINOR at the small tier',
    )
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()

    if args.selftest:
        return 0 if _selftest() else 1

    target = Path(args.dir)
    findings = validate_tree(target, tier=args.tier)
    text, counts = format_findings(findings, target)
    print(text)
    return 1 if (counts['CRITICAL'] or counts['MAJOR']) else 0


if __name__ == '__main__':
    sys.exit(main())
