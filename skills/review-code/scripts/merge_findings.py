#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Merge per-lane review findings and build a GitHub review payload.

Usage: merge_findings.py --findings DIR --diff FILE --out DIR
       merge_findings.py --self-test

Writes merged.json and review-payload.json to --out.

Dedup: two findings are duplicates when they share a path, their lines are
within LINE_WINDOW of each other, and they share a dimension or a normalized
title. The highest severity wins as primary; the rest go in its duplicates[].
"""

# ruff: noqa: S101, T201, PLR2004, PT018, E501
# Asserts and prints are the --self-test contract; this file cannot edit pyproject ignores.
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

SEVERITIES = ['Critical', 'Major', 'Minor', 'Nit']
LINE_WINDOW = 2
HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')


def right_lines(diff: str) -> dict[str, set[int]]:
    """Map each path to the new-file lines a RIGHT-side comment may anchor to."""
    valid: dict[str, set[int]] = {}
    path, ln, left = None, 0, 0
    for row in diff.splitlines():
        if left == 0 and row.startswith('+++ '):
            tgt = row[4:].split('\t')[0]
            path = tgt[2:] if tgt.startswith('b/') else None
            if path:
                valid.setdefault(path, set())
            left = 0
        elif m := HUNK.match(row):
            ln, left = int(m[1]), int(m[2]) if m[2] is not None else 1
        elif path and left > 0:
            if row.startswith(('-', '\\')):
                continue
            valid[path].add(ln)
            ln += 1
            left -= 1
    return valid


def norm_title(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', title.lower()).strip()


def sev_rank(f: dict) -> int:
    return (
        SEVERITIES.index(f['severity'])
        if f['severity'] in SEVERITIES
        else len(SEVERITIES)
    )


def is_dup(a: dict, b: dict) -> bool:
    return (
        a['path'] == b['path']
        and abs((a.get('line') or 0) - (b.get('line') or 0)) <= LINE_WINDOW
        and (
            a['dimension'] == b['dimension']
            or norm_title(a['title']) == norm_title(b['title'])
        )
    )


def merge(findings: list[dict], valid: dict[str, set[int]]) -> list[dict]:
    live = [f for f in findings if f.get('verdict') != 'REJECTED']
    live.sort(key=lambda f: (sev_rank(f), f['path'], f.get('line') or 0, f['id']))
    merged: list[dict] = []
    for f in live:
        primary = next((m for m in merged if is_dup(m, f)), None)
        if primary:
            primary['duplicates'].append(f)
        else:
            merged.append({**f, 'duplicates': []})
    for m in merged:
        m['inline'] = (not m.get('preexisting')) and m.get('line') in valid.get(
            m['path'], set()
        )
    return merged


def text(f: dict) -> str:
    out = f'**{f["title"]}** ({f["severity"]}, {f["id"]})\n\n{f["body"]}'
    if f.get('verdict'):
        why = f' ({f["reason"]})' if f.get('reason') else ''
        out += f'\n\nVerification: {f["verdict"]}{why}'
    if f['duplicates']:
        ids = ', '.join(d['id'] for d in f['duplicates'])
        out += f'\n\n<details><summary>Also flagged by {ids}</summary>\n\n'
        out += '\n\n'.join(f'{d["title"]}: {d["body"]}' for d in f['duplicates'])
        out += '\n\n</details>'
    return out


def cell(s: str) -> str:
    return ' '.join(s.split()).replace('|', '\\|')


def payload(merged: list[dict]) -> dict:
    inline = [m for m in merged if m['inline']]
    rest = [m for m in merged if not m['inline']]
    body = f'{len(merged)} findings, {len(inline)} inline.'
    if rest:
        body += '\n\n| Severity | Location | Finding |\n|---|---|---|\n'
        body += '\n'.join(
            f'| {m["severity"]} | `{cell(m["path"])}:{m.get("line") or "-"}` | {cell(m["title"])}: {cell(m["body"])} |'
            for m in rest
        )
    return {
        'event': 'COMMENT',
        'body': body,
        'comments': [
            {'path': m['path'], 'line': m['line'], 'side': 'RIGHT', 'body': text(m)}
            for m in inline
        ],
    }


def load(findings_dir: Path) -> list[dict]:
    files = sorted(findings_dir.glob('*.json'))
    if not files:
        sys.exit(f'no *.json findings files in {findings_dir}')
    out = []
    for p in files:
        try:
            data = json.loads(p.read_text())
            items = data['findings']
        except (ValueError, KeyError, TypeError):
            sys.exit(f'{p}: invalid JSON or missing "findings" key')
        for f in items:
            try:
                f['line'] = int(f['line']) if f.get('line') is not None else None
            except (ValueError, TypeError):
                sys.exit(f'{p}: finding {f.get("id")}: line is not an integer')
        out += items
    return out


def run(findings_dir: Path, diff: Path, out: Path) -> None:
    if not diff.is_file():
        sys.exit(f'diff file not found: {diff}')
    merged = merge(load(findings_dir), right_lines(diff.read_text()))
    out.mkdir(parents=True, exist_ok=True)
    (out / 'merged.json').write_text(json.dumps(merged, indent=2))
    (out / 'review-payload.json').write_text(json.dumps(payload(merged), indent=2))


SELF_DIFF = """\
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 import os
+import sys
 x = 1
-y = 2
+y = 3
diff --git a/old.py b/old.py
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-gone
diff --git a/pp.py b/pp.py
--- a/pp.py
+++ b/pp.py
@@ -1 +1,2 @@
 keep
+++ not a header
"""


def self_test() -> None:
    v = right_lines(SELF_DIFF)
    assert v == {'app.py': {1, 2, 3, 4}, 'pp.py': {1, 2}}, v

    def f(i: str, line: int, sev: str, dim: str, title: str, **kw: object) -> dict:
        return {
            'id': i,
            'path': 'app.py',
            'line': line,
            'severity': sev,
            'dimension': dim,
            'title': title,
            'body': 'b',
            'preexisting': False,
            'verdict': None,
            **kw,
        }

    found = [
        f('CL-001', 2, 'Minor', 'CL', 'Unused import'),
        f('CS-001', 3, 'Major', 'CS', 'unused  import!'),
        f('PF-001', 4, 'Nit', 'PF', 'Slow'),
        f('EH-001', 9, 'Critical', 'EH', 'Outside hunk'),
        f('CL-002', 1, 'Critical', 'CL', 'False alarm', verdict='REJECTED'),
        f('CL-003', 4, 'Nit', 'CL', 'Old issue', preexisting=True),
    ]
    m = merge(found, v)
    assert [x['id'] for x in m] == ['EH-001', 'CS-001', 'CL-003', 'PF-001'], [
        x['id'] for x in m
    ]
    assert m[1]['duplicates'][0]['id'] == 'CL-001', 'same title, line 2 vs 3'
    assert [x['inline'] for x in m] == [False, True, False, True]
    p = payload(m)
    assert p['event'] == 'COMMENT' and len(p['comments']) == 2
    assert all(c['side'] == 'RIGHT' for c in p['comments'])
    nl = payload(
        [
            {
                **f('X-1', 9, 'Minor', 'CL', 'a|b', body='x\n\ny'),
                'duplicates': [],
                'inline': False,
            }
        ]
    )
    assert '| Minor | `app.py:9` | a\\|b: x y |' in nl['body'], nl['body']
    vr = text({**m[1], 'verdict': 'CONFIRMED', 'reason': 'traced'})
    assert 'Verification: CONFIRMED (traced)' in vr
    assert 'Outside hunk' in p['body'] and '<details>' in p['comments'][0]['body']

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / 'f').mkdir()
        (d / 'f' / 'core-cl.json').write_text(
            json.dumps({'lane': 'core', 'findings': found})
        )
        (d / 'd.patch').write_text(SELF_DIFF)
        run(d / 'f', d / 'd.patch', d / 'out')
        assert len(json.loads((d / 'out' / 'merged.json').read_text())) == 4
        assert (d / 'out' / 'review-payload.json').exists()
    print('OK')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--findings', type=Path)
    ap.add_argument('--diff', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if not (a.findings and a.diff and a.out):
        ap.error('--findings, --diff and --out are required')
    run(a.findings, a.diff, a.out)


if __name__ == '__main__':
    sys.exit(main())
