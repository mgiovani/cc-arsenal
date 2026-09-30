from collections.abc import Collection
from typing import Any

from anything_to_skill.core.models import Unit

DEFAULT_TAU = 0.8

JUDGE_SCHEMA = """judge.json:
{"version": 1, "annotate_only": bool, "agreement": float|null, "order_agreement": float|null,
 "drop": [{"id": int, "reason": str}],
 "section": {"<unit id>": "<section slug>"},
 "kind": {"<unit id>": "reference|tutorial|example|concept"},
 "deferred": [{"id": int, "note": str}]}"""


def _drop_blocker(
    judgment: dict[str, Any], effort: str, tau: float, *, annotate_only: bool
) -> str | None:
    if annotate_only:
        return 'judge is in annotate-only mode'
    if effort == 'complete':
        return 'effort is complete, every page is kept'
    if judgment['on_topic']['conf'] < tau:
        return f'confidence {judgment["on_topic"]["conf"]:.2f} is below {tau}'
    # A missing keyword count means unknown, so it blocks the drop.
    if judgment.get('kw', 1) > 0:
        return 'goal keywords appear on the page'
    return None


def apply_rules(
    judgments: dict[int, dict[str, Any]],
    units: list[Unit],
    effort: str,
    *,
    orphans: Collection[int] = (),
    annotate_only: bool = False,
    agreement: float | None = 1.0,
    tau: float = DEFAULT_TAU,
) -> dict[str, Any]:
    """Turn raw per-unit judgments into judge.json under the deterministic apply rules.

    A judgment is {question: {'label', 'conf'}} for each question whose two option orders
    agreed, plus 'disagree' (question names that did not) and 'kw' (goal keyword hits).
    """
    known = {u.id for u in units}
    out: dict[str, Any] = {
        'version': 1,
        'annotate_only': annotate_only,
        'agreement': None if agreement is None else round(agreement, 3),
        'drop': [],
        'section': {},
        'kind': {},
        'deferred': [],
    }
    for uid in sorted(judgments):
        if uid not in known:
            continue
        j = judgments[uid]
        notes: list[str] = []
        if 'kind' in j:
            out['kind'][str(uid)] = j['kind']['label']
        if 'on_topic' in j and j['on_topic']['label'] == 'off':
            blocker = _drop_blocker(j, effort, tau, annotate_only=annotate_only)
            if blocker is None:
                out['drop'].append(
                    {
                        'id': uid,
                        'reason': f'off topic (confidence {j["on_topic"]["conf"]:.2f}), '
                        'no goal keywords',
                    }
                )
            else:
                notes.append(f'judged off topic but kept: {blocker}')
        elif 'on_topic' in j.get('disagree', ()):
            notes.append('on-topic check: the two option orders disagreed')
        if j.get('cohesive', {}).get('label') == 'several':
            notes.append('may cover several topics, left to the LLM review')
        if 'section' in j and uid in orphans:
            slug = j['section']['label']
            if annotate_only:
                notes.append(f'suggested section {slug}, not applied (annotate-only)')
            else:
                out['section'][str(uid)] = slug
        if notes:
            out['deferred'].append({'id': uid, 'note': '; '.join(notes)})
    return out
