import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from anything_to_skill.core.models import Finding
from anything_to_skill.core.store import Store
from anything_to_skill.core.workspace import Workspace
from anything_to_skill.laya import client
from anything_to_skill.laya.questions import ask_many
from anything_to_skill.scan.quotes import is_connective

WINDOW_CHARS = 1200  # ~300 tokens, so claim + passage fit Laya's 512-token context
TOP_CHUNKS = 3  # nearest chunks tried per unsourced sentence
CHUNK_CHARS = 1000
MAX_CHUNKS = 3000
MAX_ATTRIBUTION = 60
MIN_WORDS = 8

SUPPORT = ['The passage supports the claim.', 'The passage does not support the claim.']
MATCH = ['The file matches the description.', 'The file does not match the description.']
SRC = re.compile(r'\(src:\s*(\d+)\s+"([^"]{1,300})"\)')
SENTENCE_END = re.compile(r'(?<=[.!?])\s+')
LEAD = re.compile(r'^[\s>*#|-]+|^\d+\.\s+')
PATH = re.compile(r'[\w./-]+\.md')


@dataclass
class _Tally:
    asked: int = 0
    agreed: int = 0

    def check(self, state: str, instructions: str, options: list[str]) -> int | None:
        """0 (first option) or 1, or None when the two option orders disagree."""
        self.asked += 1
        picked = ask_many(state, {'q': (instructions, options)})['q']
        if picked is None:
            return None
        self.agreed += 1
        return picked[0]


def prose_lines(path: Path) -> list[tuple[int, str]]:
    """(line number, text) for prose lines: no frontmatter, code fences or headings."""
    lines, fenced, front = [], False, False
    for n, raw in enumerate(path.read_text('utf-8').splitlines(), 1):
        line = raw.strip()
        if n == 1 and line == '---':
            front = True
        elif front:
            front = line != '---'
        elif line.startswith('```'):
            fenced = not fenced
        elif line and not fenced and not line.startswith('#'):
            lines.append((n, line))
    return lines


def _norm(text: str) -> str:
    return ' '.join(text.split())


def _window(text: str, quote: str) -> str | None:
    flat = _norm(text)
    at = flat.lower().find(_norm(quote).lower())
    if at < 0:
        return None
    half = (WINDOW_CHARS - len(quote)) // 2
    return flat[max(0, at - half) : at + len(quote) + half]


def _claim_before(line: str, marker_start: int) -> str:
    return LEAD.sub('', SENTENCE_END.split(line[:marker_start].rstrip())[-1]).strip()


def _check_supports(
    files: list[Path], store: Store, tally: _Tally, findings: list[Finding]
) -> None:
    for path in files:
        for n, line in prose_lines(path):
            for m in SRC.finditer(line):
                claim = _claim_before(line, m.start())
                unit_id = int(m.group(1))
                try:
                    passage = _window(store.read_markdown(unit_id), m.group(2))
                except (KeyError, OSError):
                    passage = None
                if not claim or passage is None:
                    continue  # a missing quote is scan.quotes' finding, not this check's
                verdict = tally.check(
                    f'Claim: {claim}\nPassage: {passage}',
                    'Does the passage support the claim?',
                    SUPPORT,
                )
                if verdict == 1:
                    findings.append(
                        Finding(
                            'laya-support',
                            f'{path.name}: claim may not be supported by its quote '
                            f'(src {unit_id}): {claim[:120]}',
                            n,
                        )
                    )


def _chunks(store: Store) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for unit in store.units(status='done'):
        if unit.kind == 'seed':
            continue
        text = store.read_markdown(unit.id)
        out += [
            (unit.id, text[i : i + CHUNK_CHARS]) for i in range(0, len(text), CHUNK_CHARS)
        ]
        if len(out) >= MAX_CHUNKS:
            break
    return out[:MAX_CHUNKS]


def _cosine_top(query: list[float], rows: list[list[float]], k: int) -> list[int]:
    def norm(v: list[float]) -> float:
        return math.sqrt(sum(x * x for x in v)) or 1.0

    q = norm(query)
    ranked = sorted(
        range(len(rows)),
        key=lambda i: -sum(a * b for a, b in zip(query, rows[i], strict=True))
        / (q * norm(rows[i])),
    )
    return ranked[:k]


def _unsourced(files: list[Path]) -> list[tuple[Path, int, str]]:
    out = []
    for path in files:
        for n, line in prose_lines(path):
            if line.startswith('|') or SRC.search(line):
                continue
            out += [
                (path, n, s)
                for s in SENTENCE_END.split(LEAD.sub('', line))
                if len(s.split()) >= MIN_WORDS and not is_connective(s)
            ]
    return out[:MAX_ATTRIBUTION]


def _check_attribution(
    files: list[Path], store: Store, tally: _Tally, findings: list[Finding]
) -> None:
    sentences = _unsourced(files)
    chunks = _chunks(store)
    if not sentences or not chunks:
        return
    embed = client.embed_fn()
    rows = [list(map(float, r)) for r in embed([c for _, c in chunks])]
    for (path, n, sentence), vec in zip(
        sentences, embed([s for _, _, s in sentences]), strict=True
    ):
        verdicts = []
        for i in _cosine_top(list(map(float, vec)), rows, TOP_CHUNKS):
            unit_id, chunk = chunks[i]
            verdict = tally.check(
                f'Claim: {sentence}\nPassage: {chunk}',
                'Does the passage support the claim?',
                SUPPORT,
            )
            if verdict == 0:
                findings.append(
                    Finding(
                        'laya-attributed',
                        f'{path.name}: attributed? unit {unit_id} may support this '
                        f'unsourced sentence: {sentence[:120]}',
                        n,
                    )
                )
                break
            verdicts.append(verdict)
        else:
            # one wrong nearest neighbour must not condemn a sentence: every candidate must refuse
            if verdicts and all(v == 1 for v in verdicts):
                findings.append(
                    Finding(
                        'laya-unsupported',
                        f'{path.name}: unsupported, no corpus passage backs: {sentence[:120]}',
                        n,
                    )
                )


def _plan_files(ws: Workspace) -> list[dict]:
    if not ws.plan_path.exists():
        return []
    sections = json.loads(ws.plan_path.read_text('utf-8')).get('sections', [])
    return [f for s in sections for f in s.get('files', [])]


def _plan_text(store: Store, plan_file: dict) -> str:
    """The file's own text: a page split across plan files contributes only its slice."""
    if parts := plan_file.get('parts'):
        return '\n'.join(
            store.read_markdown(int(p['unit']))[p['start'] : p['end']] for p in parts
        )
    return '\n'.join(store.read_markdown(int(u)) for u in plan_file.get('units', []))


def _routing_rows(ws: Workspace) -> list[tuple[int, str, str]]:
    skill = ws.authored_dir / 'SKILL.md'
    if not skill.exists():
        return []
    rows = []
    for n, line in prose_lines(skill):
        if (
            line.startswith('|')
            and not set(line) <= set('|-: ')
            and (m := PATH.search(line))
        ):
            rows.append((n, line.strip('| '), m.group(0)))
    return rows


def _route_target(
    ws: Workspace, store: Store, plan_files: list[dict], target: str
) -> str | None:
    rel = target.removeprefix('references/')
    for f in plan_files:
        if f.get('path', '').removeprefix('references/') == rel:
            return _plan_text(store, f)
    for candidate in (ws.authored_dir / target, ws.authored_dir / rel):
        if candidate.is_file():
            return candidate.read_text('utf-8')
    return None


def _check_routing(
    ws: Workspace, store: Store, tally: _Tally, findings: list[Finding]
) -> None:
    plan_files = _plan_files(ws)
    for n, row, target in _routing_rows(ws):
        text = _route_target(ws, store, plan_files, target)
        if text:
            verdict = tally.check(
                f'Description: {row}\nFile: {_norm(text)[:WINDOW_CHARS]}',
                'Does the file match the description?',
                MATCH,
            )
            if verdict == 1:
                findings.append(
                    Finding(
                        'laya-routing', f'SKILL.md routing row may mislabel {target}', n
                    )
                )
    for f in plan_files:
        if f.get('summary') and (text := _plan_text(store, f)):
            verdict = tally.check(
                f'Description: {f["path"]} - {f["summary"]}\nFile: {_norm(text)[:WINDOW_CHARS]}',
                'Does the file match the description?',
                MATCH,
            )
            if verdict == 1:
                findings.append(
                    Finding(
                        'laya-index',
                        f'INDEX row may mislabel {f["path"]}: {f["summary"][:100]}',
                    )
                )


def _record(ws: Workspace, laya_result: dict) -> None:
    data = {}
    if ws.verify_path.exists():
        try:
            data = json.loads(ws.verify_path.read_text('utf-8'))
        except ValueError:
            data = {}
    data['laya'] = laya_result
    ws.verify_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def run(ws: Workspace) -> list[Finding]:
    """Advisory support/attribution/routing checks; results also written to ws.verify_path.

    Never edits authored content. The verify.json 'laya' key is merged, not overwritten.
    """
    try:
        client.get_router()
    except client.LayaUnavailableError as exc:
        print(f'factcheck: skipped, {exc}', file=sys.stderr)
        _record(ws, {'skipped': str(exc)})
        return []
    files = sorted(ws.authored_dir.rglob('*.md'))
    findings: list[Finding] = []
    tally = _Tally()
    with ws.open_store() as store:
        _check_supports(files, store, tally, findings)
        _check_attribution(files, store, tally, findings)
        _check_routing(ws, store, tally, findings)
    _record(
        ws,
        {
            'checks': tally.asked,
            'order_agreement': round(tally.agreed / tally.asked, 3)
            if tally.asked
            else None,
            'flags': [
                {'rule': f.rule, 'message': f.message, 'line': f.line} for f in findings
            ],
        },
    )
    return findings
