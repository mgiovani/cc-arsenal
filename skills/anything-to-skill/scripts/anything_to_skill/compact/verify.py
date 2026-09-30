import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from anything_to_skill.compact import freeze, layout
from anything_to_skill.core.models import Finding
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.emit.verify import (
    ALLOWED_KEYS,
    MAX_SKILL_LINES,
    _frontmatter_keys,
    _images,
    _quick_validate,
    _routing,
    _skill_dir,
    process_assertions,
)
from anything_to_skill.emit.write import skill_name
from anything_to_skill.scan import credentials, injection, quotes, unicode

AUTHORED_MARK = 'authored'
MAX_AUTHORED_BLOCKS = 5
_FENCE_OPEN = re.compile(r'^[\s>]*(`{3,}|~{3,})(.*)$')
_LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)[^)]*\)')
_SRC_MARKER = re.compile(r'\(src:')
_SRC_LINK = re.compile(r'\[source\]\(')
_MIRROR_NAME = re.compile(r'\b(?:SOURCES|INDEX)\.md\b')
_COMMENT = re.compile(r'^(?:#|//|--|;|%|/\*|\*|<!--)(?:\s|$)')
_REF_PATH = re.compile(r'references/[\w\-./]*[\w/]')


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--dir', help='staged skill (default: <workspace>/compact)')
    parser.add_argument(
        '--laya',
        action='store_true',
        help='also flag prose sentences the corpus does not back (advisory)',
    )


def code_blocks(text: str) -> Iterator[tuple[int, str, str]]:
    """(line, info string, body) per fenced block."""
    fence = ''
    start, info, body = 0, '', []
    for n, line in enumerate(text.split('\n'), 1):
        m = _FENCE_OPEN.match(line)
        if not fence:
            if m:
                fence, start, info, body = m.group(1), n, m.group(2).strip(), []
        elif (
            m
            and m.group(1)[0] == fence[0]
            and len(m.group(1)) >= len(fence)
            and not m.group(2).strip()
        ):
            yield start, info, '\n'.join(body)
            fence = ''
        else:
            body.append(line)
    if fence:
        yield start, info, '\n'.join(body)


def corpus_lines(store: Store) -> set[str]:
    """Every whitespace-collapsed line of every finished unit."""
    lines: set[str] = set()
    for unit in store.units(status='done'):
        if unit.kind != 'seed' and unit.md_path:
            lines.update(
                ' '.join(ln.split()) for ln in store.read_markdown(unit.id).split('\n')
            )
    return lines


def _lines_verbatim(body: str, lines: set[str]) -> bool:
    """A block trimmed or spliced from source code: every code line exists in the corpus.

    Comment-only and punctuation-only lines are exempt, but at least one real code line must match.
    """
    matched = False
    for raw in body.split('\n'):
        line = ' '.join(raw.split())
        if not line or not re.search(r'\w', line) or _COMMENT.match(line):
            continue
        if line not in lines:
            return False
        matched = True
    return matched


def _code(
    text: str, corpus: dict[int, str], lines: set[str]
) -> tuple[list[Finding], list[int]]:
    findings: list[Finding] = []
    authored: list[int] = []
    for line, info, body in code_blocks(text):
        needle = quotes.normalize(body)
        if not needle:
            continue
        if AUTHORED_MARK in info.split():
            authored.append(line)
        elif not any(needle in hay for hay in corpus.values()) and not _lines_verbatim(
            body, lines
        ):
            findings.append(
                Finding(
                    'code-not-verbatim',
                    'code block is not in the corpus, even line by line; copy it from a source '
                    f'or mark the fence `{AUTHORED_MARK}` (max {MAX_AUTHORED_BLOCKS} in the skill)',
                    line,
                    'hard',
                )
            )
    return findings, authored


def _links(rel: str, text: str, root: Path) -> list[Finding]:
    prose, _ = quotes._split_fences(text)  # noqa: SLF001
    out = []
    for m in _LINK.finditer(prose):
        target = m.group(1).split('#')[0]
        if not target or '://' in target or target.startswith('mailto:'):
            continue
        if not (root / rel).parent.joinpath(target).resolve().exists():
            line = prose.count('\n', 0, m.start()) + 1
            out.append(Finding('link-missing', f'{target} does not exist', line, 'hard'))
    return out


def _attribution(text: str, uris: list[str]) -> list[Finding]:
    out = []
    if _SRC_MARKER.search(text) or _SRC_LINK.search(text):
        out.append(
            Finding(
                'source-marker',
                'src marker or [source] link left in the skill',
                None,
                'hard',
            )
        )
    if _MIRROR_NAME.search(text):
        out.append(
            Finding(
                'source-mention',
                'mentions SOURCES.md or INDEX.md, which a compact skill drops',
                None,
                'hard',
            )
        )
    out += [
        Finding('source-url', f'mentions a source URL: {uri[:80]}', None, 'warn')
        for uri in uris
        if uri in text
    ]
    return out


def _file(
    rel: str,
    text: str,
    root: Path,
    ctx: tuple[dict[int, str], set[str], list[str]],
) -> tuple[list[Finding], list[int]]:
    corpus, lines, uris = ctx
    hard = rel == 'SKILL.md'
    findings = unicode.scan(text) + injection.scan(text)
    if not hard:
        findings = [replace(f, severity='warn') for f in findings]
    findings += credentials.scan(text)
    findings += (
        _attribution(text, uris)
        + _links(rel, text, root)
        + _images(rel, text, root, 'hard')
    )
    code, authored = _code(text, corpus, lines)
    findings += code
    if hard:
        findings += _routing(rel, text, root, 'hard')
    return findings, authored


def _hub(text: str, expected: str) -> list[Finding]:
    keys = _frontmatter_keys(text)
    out: list[Finding] = []
    if keys is None:
        return [Finding('frontmatter', 'SKILL.md has no frontmatter', 1, 'hard')]
    if extra := sorted(set(keys) - ALLOWED_KEYS):
        out.append(
            Finding(
                'frontmatter',
                f'unexpected frontmatter keys: {", ".join(extra)}',
                1,
                'hard',
            )
        )
    fm_name = re.search(r'^name:\s*(\S+)', text, re.MULTILINE)
    if not fm_name or fm_name.group(1).strip('"\'') != expected:
        out.append(Finding('name', f'frontmatter name must stay {expected!r}', 1, 'hard'))
    lines = text.count('\n') + 1
    if lines >= MAX_SKILL_LINES:
        out.append(
            Finding(
                'limits',
                f'SKILL.md has {lines} lines (max {MAX_SKILL_LINES - 1})',
                None,
                'hard',
            )
        )
    elif lines > layout.MAX_HUB_LINES:
        out.append(
            Finding(
                'hub-long',
                f'SKILL.md has {lines} lines (target {layout.MAX_HUB_LINES})',
                None,
                'warn',
            )
        )
    return out


def _evals(tree: dict[str, str], frozen: str | None) -> list[Finding]:
    """The compact skill carries exactly the frozen evals, and none of them grades file reads."""
    raw = tree.get('evals/evals.json')
    if raw is None:
        return [Finding('evals-missing', 'evals/evals.json is missing', None, 'hard')]
    try:
        cases = freeze.cases(raw)
        want = freeze.cases(frozen) if frozen else []
    except ValueError as exc:
        return [Finding('evals-invalid', f'evals/evals.json: {exc}', None, 'hard')]
    out = process_assertions(raw, 'hard')
    have = {c.get('id'): c for c in cases}
    if len(have) != len(cases):
        out.append(
            Finding('eval-changed', 'evals/evals.json repeats an eval id', None, 'hard')
        )
    for case in want:
        got = have.pop(case.get('id'), None)
        if got is None:
            out.append(
                Finding(
                    'eval-dropped',
                    f'frozen eval {case.get("id")!r} is missing; evals are never edited during compaction',
                    None,
                    'hard',
                )
            )
        elif (got.get('prompt'), got.get('assertions')) != (
            case.get('prompt'),
            case.get('assertions'),
        ):
            out.append(
                Finding(
                    'eval-changed',
                    f'eval {case.get("id")!r} differs from the frozen set (prompt or assertions); '
                    'restore compact/evals/evals.json with `compact-brief` or `evals-freeze`',
                    None,
                    'hard',
                )
            )
    out += [
        Finding(
            'eval-added',
            f'eval {i!r} is not in the frozen set; evals are never edited during compaction',
            None,
            'hard',
        )
        for i in have
    ]
    stale = set(_REF_PATH.findall(tree.get('evals/trigger-eval.json', '')))
    out += [
        Finding(
            'eval-stale-ref',
            f'trigger-eval mentions {path}, which is not in the compact skill',
            None,
            'hard',
        )
        for path in sorted(stale)
        if path not in tree
        and not any(rel.startswith(path.rstrip('/') + '/') for rel in tree)
    ]
    if 'evals/trigger-eval.json' not in tree:
        out.append(
            Finding(
                'trigger-eval-missing', 'evals/trigger-eval.json is missing', None, 'warn'
            )
        )
    return out


def _laya(root: Path, store: Store) -> list[Finding]:
    from anything_to_skill.laya import client, factcheck  # noqa: PLC0415

    client.get_router()
    findings: list[Finding] = []
    check_attribution = factcheck._check_attribution  # noqa: SLF001
    tally = factcheck._Tally()  # noqa: SLF001
    check_attribution(sorted(root.rglob('*.md')), store, tally, findings)
    return [f for f in findings if f.rule == 'laya-unsupported']


def check(ws: Workspace, root: Path, *, laya: bool = False) -> dict[str, Any]:
    """Findings, token sizes and a hard/warn count for a staged compact skill."""
    rows: list[dict[str, Any]] = []

    def add(rel: str, findings: list[Finding]) -> None:
        rows.extend({'file': rel, **asdict(f)} for f in findings)

    tree = layout.read_tree(root)
    if 'SKILL.md' not in tree:
        add(
            'SKILL.md',
            [Finding('hub-missing', f'no SKILL.md under {root}', None, 'hard')],
        )
        return _report(root, rows, {}, [])
    emitted = _skill_dir(ws, None)
    baseline = layout.read_tree(layout.original_dir(ws, emitted))
    authored: list[tuple[str, int]] = []
    with ws.open_store() as store:
        expected = skill_name(ws, store.get_meta('name'))
        corpus = quotes.load_corpus(store)
        uris = sorted(
            {
                u.uri
                for u in store.units()
                if u.kind != 'seed' and u.uri.startswith('http')
            }
        )
        ctx = (corpus, corpus_lines(store), uris)
        for rel, text in tree.items():
            if rel.endswith('.md'):
                findings, marked = _file(rel, text, root, ctx)
                add(rel, findings)
                authored += [(rel, line) for line in marked]
        if laya:
            try:
                add('(laya)', _laya(root, store))
            except Exception as exc:  # noqa: BLE001 - advisory only
                add(
                    '(laya)',
                    [
                        Finding(
                            'laya-unavailable', f'fact-check skipped: {exc}', None, 'warn'
                        )
                    ],
                )
    add('SKILL.md', _hub(tree['SKILL.md'], expected))
    for rel in tree:
        if Path(rel).name in ('SOURCES.md', 'INDEX.md'):
            add(
                rel,
                [
                    Finding(
                        'mirror-file',
                        'a compact skill carries no source mirror files',
                        None,
                        'hard',
                    )
                ],
            )
    add('SKILL.md', _authored_cap(authored))
    add('evals', _evals(tree, freeze.load(ws) or baseline.get('evals/evals.json')))
    qv = _quick_validate(root)
    add(
        'SKILL.md',
        [Finding('quick_validate', e, None, 'hard') for e in qv.get('errors', [])],
    )
    add(
        'SKILL.md',
        [Finding('quick_validate', w, None, 'warn') for w in qv.get('warnings', [])],
    )
    before, after = layout.sizes(baseline), layout.sizes(tree)
    add('references', _budget(before, after))
    return _report(root, rows, {'before': before, 'after': after}, authored)


def _authored_cap(authored: list[tuple[str, int]]) -> list[Finding]:
    if not authored:
        return []
    severity = 'hard' if len(authored) > MAX_AUTHORED_BLOCKS else 'warn'
    where = ', '.join(f'{rel}:{line}' for rel, line in authored)
    return [
        Finding(
            'authored-code',
            f'{len(authored)} authored code block(s) not checked against the corpus (max {MAX_AUTHORED_BLOCKS}): {where}',
            None,
            severity,
        )
    ]


def _budget(before: dict[str, int], after: dict[str, int]) -> list[Finding]:
    cap = int(before.get('mirror', 0) * layout.MAX_REFERENCE_SHARE)
    if cap and after.get('references', 0) > cap:
        return [
            Finding(
                'budget',
                f'references total {after["references"]} tok, target at most ~{cap} tok',
                None,
                'warn',
            )
        ]
    return []


def _report(
    root: Path, rows: list[dict[str, Any]], tokens: dict[str, Any], authored: list[Any]
) -> dict[str, Any]:
    hard = sum(r['severity'] == 'hard' for r in rows)
    before, after = tokens.get('before', {}), tokens.get('after', {})
    return {
        'dir': str(root),
        'ok': hard == 0,
        'hard': hard,
        'warn': len(rows) - hard,
        'tokens': {
            'before': before.get('total'),
            'after': after.get('total'),
            'saved_pct': round(100 * (1 - after['total'] / before['total']), 1)
            if before.get('total')
            else None,
            'hub_before': before.get('hub'),
            'hub_after': after.get('hub'),
            'references_after': after.get('references'),
            'mirror_before': before.get('mirror'),
        },
        'authored_blocks': len(authored),
        'findings': rows,
    }


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py compact-verify`: gate the staged compact skill; non-zero on hard fails."""
    root = Path(args.dir).expanduser().resolve() if args.dir else ws.compact_dir
    if not root.is_dir():
        print(
            f'compact-verify: {root} does not exist; write the compact skill there first',
            file=sys.stderr,
        )
        return 2
    report = check(ws, root, laya=args.laya)
    ws.compact_verify_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    for r in report['findings']:
        if r['severity'] == 'hard':
            print(
                f'HARD {r["file"]}:{r["line"] or "-"} {r["rule"]}: {r["message"]}',
                file=sys.stderr,
            )
    t = report['tokens']
    print(
        f'compact-verify: {report["hard"]} hard, {report["warn"]} warn; tokens {t["before"]} -> {t["after"]} '
        f'({t["saved_pct"]}% saved), hub {t["hub_before"]} -> {t["hub_after"]} -> {ws.compact_verify_path}'
    )
    return 0 if report['ok'] else 1
