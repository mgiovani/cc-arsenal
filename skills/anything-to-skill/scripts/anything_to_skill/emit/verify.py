import argparse
import importlib.util
import json
import re
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from anything_to_skill.core.models import Finding
from anything_to_skill.core.store import Store
from anything_to_skill.core.tokens import count
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.emit.write import (
    GENERIC_DESCRIPTION,
    _frontmatter_description,
    skill_name,
)
from anything_to_skill.scan import credentials, injection, quotes, unicode

MAX_SKILL_LINES = 500
MAX_REF_TOKENS = 8000
ALLOWED_KEYS = {'name', 'description'}
QUICK_VALIDATE = (
    Path(__file__).resolve().parents[4] / 'create-skill' / 'scripts' / 'quick_validate.py'
)
_ROUTE = re.compile(r'(?:references|assets|evals)/[\w\-./]*[\w/]')
# An eval assertion about what the agent read or which file it named grades the process:
# a run without the skill fails it for free while content assertions pass without the skill.
_PROCESS = re.compile(
    r'\b(?:references|evals)/[\w\-./]*[\w/]|\b(?:INDEX|SOURCES|SKILL)\.md\b|'
    r'^\W*(?:reads?|opens?|loads?|consults?|refers? to|cites?|'
    r'names? the (?:source|reference|file)|(?:uses?|invokes?) the [\w-]* ?skill)\b',
    re.I,
)
_IMAGE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)\)')
_INDEX_PATH = re.compile(r'^[\s\-*`]*([\w\-./]+\.md)\b')
# Authored files carry claims, so their code and quotes are re-checked against the corpus.
_AUTHORED = re.compile(
    r'^(?:SKILL\.md|references/best-practices\.md|references/examples/.+\.md)$'
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--laya', action='store_true', help='also run advisory Laya fact-check'
    )
    parser.add_argument('--dir', help='skill directory (default: the init --out answer)')


def _skill_dir(ws: Workspace, override: str | None) -> Path:
    with ws.open_store() as store:
        out = override or store.get_meta('out')
        name = skill_name(ws, store.get_meta('name'))
    path = Path(out).expanduser() if out else Path('.agents/skills') / name
    return path if path.is_absolute() else Path.cwd() / path


def _frontmatter_keys(text: str) -> list[str] | None:
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None
    return re.findall(r'^([A-Za-z0-9_-]+):', m.group(1), re.MULTILINE)


def _routing(rel: str, text: str, root: Path, severity: str) -> list[Finding]:
    """Every path mentioned in SKILL.md, and every file INDEX.md lists, must exist."""
    findings = []
    if rel == 'SKILL.md':
        for path in sorted(set(_ROUTE.findall(text))):
            if not (root / path).exists():
                findings.append(
                    Finding('route-missing', f'{path} does not exist', None, severity)
                )
    elif rel == 'references/INDEX.md':
        for i, line in enumerate(text.splitlines(), 1):
            m = _INDEX_PATH.match(line)
            if m and not any(
                (root / base / m.group(1)).is_file() for base in ('', 'references')
            ):
                findings.append(
                    Finding('index-missing', f'{m.group(1)} does not exist', i, 'warn')
                )
    return findings


def process_assertions(raw: str, severity: str) -> list[Finding]:
    """Assertions that check file reads or paths instead of the content of the answer."""
    try:
        cases = json.loads(raw)['evals']
    except (ValueError, KeyError, TypeError):
        return []
    return [
        Finding(
            'eval-process-assertion',
            f'eval {c.get("id")!r}: assertion is about files or process, not answer content: {a[:70]!r}',
            None,
            severity,
        )
        for c in cases
        if isinstance(c, dict)
        for a in c.get('assertions', [])
        if isinstance(a, str) and _PROCESS.search(a)
    ]


def _images(rel: str, text: str, root: Path, severity: str) -> list[Finding]:
    return [
        Finding('image-missing', f'{target} does not exist', None, severity)
        for target in sorted(set(_IMAGE.findall(text)))
        if '://' not in target and not (root / rel).parent.joinpath(target).is_file()
    ]


def _quick_validate(skill: Path) -> dict[str, Any]:
    if not QUICK_VALIDATE.exists():
        return {'skipped': 'create-skill/scripts/quick_validate.py not found'}
    spec = importlib.util.spec_from_file_location('a2s_quick_validate', QUICK_VALIDATE)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    valid, errors, warnings = module.validate_skill(skill)
    return {'valid': valid, 'errors': errors, 'warnings': warnings}


def _check_file(
    rel: str, text: str, root: Path, store: Store, corpus: dict[int, str]
) -> list[Finding]:
    hard = rel == 'SKILL.md'
    findings = unicode.scan(text) + injection.scan(text)
    if not hard:
        findings = [replace(f, severity='warn') for f in findings]
    findings += credentials.scan(text)
    if _AUTHORED.match(rel):
        findings += quotes.verify(text, store, corpus)
        findings += quotes.verify_links(text, (root / rel).parent)
    findings += _routing(rel, text, root, 'hard' if hard else 'warn')
    findings += _images(rel, text, root, 'hard' if hard else 'warn')
    if rel == 'evals/evals.json':
        findings += process_assertions(text, 'warn')
    if hard:
        keys = _frontmatter_keys(text)
        if keys is None:
            findings.append(
                Finding('frontmatter', 'SKILL.md has no frontmatter', 1, 'hard')
            )
        elif extra := sorted(set(keys) - ALLOWED_KEYS):
            findings.append(
                Finding(
                    'frontmatter',
                    f'unexpected frontmatter keys: {", ".join(extra)}',
                    1,
                    'hard',
                )
            )
        description, _ = _frontmatter_description(text)
        if description and GENERIC_DESCRIPTION.match(description):
            findings.append(
                Finding(
                    'description-generic',
                    'description is the generic default; write one in authored/SKILL.md frontmatter',
                    2,
                    'warn',
                )
            )
        lines = text.count('\n') + 1
        if lines >= MAX_SKILL_LINES:
            findings.append(
                Finding(
                    'limits',
                    f'SKILL.md has {lines} lines (max {MAX_SKILL_LINES - 1})',
                    None,
                    'hard',
                )
            )
    elif rel.startswith('references/') and (tokens := count(text)) > MAX_REF_TOKENS:
        findings.append(
            Finding('limits', f'{tokens} tokens (max {MAX_REF_TOKENS})', None, 'warn')
        )
    return findings


def run(ws: Workspace, args: argparse.Namespace) -> int:
    """`a2s.py verify`: scans, quote check, limits, quick_validate; non-zero on hard fails."""
    root = _skill_dir(ws, args.dir)
    if ws.full_dir.is_dir() and not (root / 'references' / 'SOURCES.md').exists():
        print(
            'verify: this skill was compacted; use `a2s.py compact-verify`, or `compact --revert` first',
            file=sys.stderr,
        )
        return 2
    if not (root / 'SKILL.md').is_file():
        print(
            f'verify: no SKILL.md under {root}; run `a2s.py emit` first', file=sys.stderr
        )
        return 2
    rows: list[dict[str, Any]] = []

    def add(rel: str, findings: list[Finding]) -> None:
        rows.extend({'file': rel, **asdict(f)} for f in findings)

    with ws.open_store() as store:
        corpus = quotes.load_corpus(store)
        for path in sorted(root.rglob('*')):
            rel = path.relative_to(root).as_posix()
            if path.is_file() and path.suffix in ('.md', '.json'):
                add(rel, _check_file(rel, path.read_text('utf-8'), root, store, corpus))

    name_in_dir = root.name
    fm_name = re.search(
        r'^name:\s*(\S+)', (root / 'SKILL.md').read_text('utf-8'), re.MULTILINE
    )
    if fm_name and fm_name.group(1) != name_in_dir:
        add(
            'SKILL.md',
            [
                Finding(
                    'name-dir',
                    f'name {fm_name.group(1)!r} differs from directory {name_in_dir!r}',
                    1,
                    'warn',
                )
            ],
        )

    qv = _quick_validate(root)
    add(
        'SKILL.md',
        [Finding('quick_validate', e, None, 'hard') for e in qv.get('errors', [])],
    )
    add(
        'SKILL.md',
        [Finding('quick_validate', w, None, 'warn') for w in qv.get('warnings', [])],
    )

    laya: Any = None
    if args.laya:
        ws.verify_path.unlink(missing_ok=True)
        try:
            from anything_to_skill.laya import factcheck  # noqa: PLC0415

            add('(laya)', factcheck.run(ws))
            if ws.verify_path.exists():
                laya = json.loads(ws.verify_path.read_text('utf-8')).get('laya')
        except Exception as exc:  # noqa: BLE001
            add(
                '(laya)',
                [Finding('laya-unavailable', f'fact-check skipped: {exc}', None, 'warn')],
            )

    hard = sum(r['severity'] == 'hard' for r in rows)
    report = {
        'skill_dir': str(root),
        'ok': hard == 0,
        'hard': hard,
        'warn': len(rows) - hard,
        'quick_validate': qv,
        'findings': rows,
        'laya': laya,
    }
    ws.verify_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    for r in rows:
        if r['severity'] == 'hard':
            print(
                f'HARD {r["file"]}:{r["line"] or "-"} {r["rule"]}: {r["message"]}',
                file=sys.stderr,
            )
    print(f'verify: {hard} hard, {report["warn"]} warn -> {ws.verify_path}')
    return 1 if hard else 0
