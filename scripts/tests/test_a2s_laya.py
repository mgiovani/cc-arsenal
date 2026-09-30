"""Unit tests for anything-to-skill's Laya integration, run against a fake router."""

import argparse
import hashlib
import json
import sys
import warnings
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / 'skills' / 'anything-to-skill' / 'scripts'
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from anything_to_skill.core.models import Unit  # noqa: E402
from anything_to_skill.core.workspace import Ctx, Workspace  # noqa: E402
from anything_to_skill.emit import write  # noqa: E402
from anything_to_skill.laya import (  # noqa: E402
    apply,
    brain,
    client,
    factcheck,
    judge,
    questions,
)
from anything_to_skill.sources.web.frontier import Link  # noqa: E402
from anything_to_skill.sources.youtube import run as yt_run  # noqa: E402

Policy = Callable[[str, dict[str, Any]], str | None]
Install = Callable[[Policy], 'FakeRouter']

CONFIDENT = 0.9
HALF = 0.5
FOURTH, FIFTH, NEGATED_LINE, MIN_WORD = 4, 5, 4, 5
PAIR = 2


class FakeRouter:
    """Answers each choice question from a policy(state, question) -> preferred option.

    The policy returns an option's description text (an order-independent model), a
    label such as 'A' (a position-biased model), or None (uniform).
    """

    def __init__(self, policy: Policy) -> None:
        self.policy = policy
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    def load(self, _name: str) -> object:
        return object()

    def predict(self, state: str | dict[str, str], qs: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((state, qs))
        text = state['request'] if isinstance(state, dict) else state
        answers = {}
        for name, q in qs.items():
            crit = q['criteria']
            want = self.policy(text, {'name': name, **q})
            key = next((k for k, v in crit.items() if v == want), want)
            rest = (1 - CONFIDENT) / max(1, len(crit) - 1)
            probs = {
                k: (CONFIDENT if k == key else rest) if key in crit else 1 / len(crit)
                for k in crit
            }
            answers[name] = {
                'choice': max(probs, key=probs.__getitem__),
                'probabilities': probs,
            }
        return {'answers': answers}


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Install:
    def install(policy: Policy) -> FakeRouter:
        router = FakeRouter(policy)
        monkeypatch.setattr(client, 'get_router', lambda: router)
        return router

    return install


def unit(uid: int, uri: str = 'https://x.dev/docs/a', title: str = 't') -> Unit:
    return Unit(id=uid, source='web', uri=uri, title=title, status='done')


# --- questions -----------------------------------------------------------------------


def test_ask_many_asks_both_orders_with_neutral_keys(fake: Install) -> None:
    router = fake(lambda _s, _q: 'second option')
    got = questions.ask_many('state', {'q': ('?', ['first option', 'second option'])})
    assert got['q'] == (1, CONFIDENT)
    forward, backward = (c[1]['q']['criteria'] for c in router.calls)
    assert forward == {'A': 'first option', 'B': 'second option'}
    assert backward == {'A': 'second option', 'B': 'first option'}


def test_ask_many_marks_only_the_disagreeing_question(fake: Install) -> None:
    fake(lambda _s, q: 'A' if q['name'] == 'biased' else 'good')
    got = questions.ask_many(
        's', {'biased': ('?', ['x', 'y']), 'steady': ('?', ['bad', 'good'])}
    )
    assert got['biased'] is None
    assert got['steady'] is not None
    assert got['steady'][0] == 1


def test_confidence_is_the_weaker_of_the_two_orders() -> None:
    assert questions.agree([0.9, 0.1], [0.6, 0.4]) == (0, 0.6)
    assert questions.agree([0.9, 0.1], [0.4, 0.6]) is None


# --- client --------------------------------------------------------------------------


def test_get_router_raises_unavailable_when_laya_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, 'laya', None)
    client.get_router.cache_clear()
    with pytest.raises(client.LayaUnavailableError):
        client.get_router()


def test_get_router_wraps_load_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_kw: Any) -> None:
        raise OSError('offline')

    monkeypatch.setitem(sys.modules, 'laya', SimpleNamespace(Router=boom))
    client.get_router.cache_clear()
    with pytest.raises(client.LayaUnavailableError, match='offline'):
        client.get_router()


def test_predict_shortlists_only_past_k(
    monkeypatch: pytest.MonkeyPatch, fake: Install
) -> None:
    router = fake(lambda _s, _q: None)
    seen = {}

    def shortlist(*_a: object, k: int, **_kw: object) -> dict[str, dict]:
        seen['k'] = k
        return {'answers': {}}

    monkeypatch.setitem(
        sys.modules,
        'laya',
        SimpleNamespace(
            predict_shortlist=shortlist, embed_fn_from_agent=lambda _a: lambda _t: []
        ),
    )
    client.embed_fn.cache_clear()
    small = {'q': {'type': 'choice', 'criteria': {str(i): 'x' for i in range(20)}}}
    big = {'q': {'type': 'choice', 'criteria': {str(i): 'x' for i in range(21)}}}
    client.predict('s', small)
    assert not seen
    assert len(router.calls) == 1
    client.predict('s', big)
    assert seen == {'k': 20}


# --- apply ---------------------------------------------------------------------------


def j(label: str = 'off', conf: float = 0.95, kw: int = 0, **extra: Any) -> dict:
    return {'on_topic': {'label': label, 'conf': conf}, 'kw': kw, 'disagree': [], **extra}


def test_drop_needs_off_topic_confidence_and_zero_keywords() -> None:
    units = [unit(i) for i in range(1, 6)]
    out = apply.apply_rules(
        {
            1: j(),
            2: j(conf=0.7),
            3: j(kw=2),
            4: j(label='on'),
            5: {'disagree': ['on_topic'], 'kw': 0},
        },
        units,
        'standard',
    )
    assert [d['id'] for d in out['drop']] == [1]
    noted = {d['id']: d['note'] for d in out['deferred']}
    assert 'below' in noted[2]
    assert 'keywords' in noted[3]
    assert FOURTH not in noted
    assert 'disagreed' in noted[FIFTH]


def test_never_drops_at_complete_effort_or_when_annotate_only() -> None:
    units = [unit(1)]
    assert apply.apply_rules({1: j()}, units, 'complete')['drop'] == []
    out = apply.apply_rules(
        {1: j()}, units, 'standard', annotate_only=True, agreement=0.5
    )
    assert out['drop'] == []
    assert out['annotate_only'] is True
    assert out['agreement'] == HALF


def test_missing_keyword_count_blocks_the_drop() -> None:
    judgment = j()
    del judgment['kw']
    assert apply.apply_rules({1: judgment}, [unit(1)], 'standard')['drop'] == []


def test_only_orphans_get_a_section_override() -> None:
    units = [unit(1), unit(2)]
    section = {'label': 'indexing', 'conf': 0.4}
    judgments = {1: j(label='on', section=section), 2: j(label='on', section=section)}
    out = apply.apply_rules(judgments, units, 'standard', orphans={1})
    assert out['section'] == {'1': 'indexing'}
    assert apply.apply_rules(judgments, units, 'standard')['section'] == {}


def test_annotate_only_defers_section_moves_but_keeps_kind_labels() -> None:
    judgments = {
        1: j(
            label='on',
            kind={'label': 'tutorial', 'conf': 0.9},
            section={'label': 'indexing', 'conf': 0.9},
        )
    }
    out = apply.apply_rules(
        judgments, [unit(1)], 'standard', orphans={1}, annotate_only=True
    )
    assert out['section'] == {}
    assert out['kind'] == {'1': 'tutorial'}
    assert 'annotate-only' in out['deferred'][0]['note']


def test_multi_topic_pages_are_deferred() -> None:
    out = apply.apply_rules(
        {1: j(label='on', cohesive={'label': 'several', 'conf': 0.9})},
        [unit(1)],
        'standard',
    )
    assert out['deferred'][0]['id'] == 1


def test_unknown_unit_ids_are_ignored() -> None:
    assert apply.apply_rules({99: j()}, [unit(1)], 'standard')['drop'] == []


# --- judge ---------------------------------------------------------------------------


def build_workspace(
    tmp_path: Path, pages: list[tuple[str, str, str]], plan: dict | None = None
) -> Workspace:
    ws = Workspace.create('demo', tmp_path)
    with ws.open_store() as store:
        store.set_meta('goal', 'postgres indexing performance')
        store.set_meta('effort', 'standard')
        for uri, title, text in pages:
            uid = store.add_unit('web', uri)
            store.finish(uid, text, title=title)
    if plan:
        ws.plan_path.write_text(json.dumps(plan), encoding='utf-8')
    return ws


def judge_policy(state: str, q: dict[str, Any]) -> str | None:
    crit = q['criteria']
    if q['name'] == 'on_topic':
        return judge.ON_TOPIC[1] if 'cooking' in state else judge.ON_TOPIC[0]
    if q['name'] == 'kind':
        return (
            judge.KINDS['tutorial'] if '/tutorial/' in state else judge.KINDS['reference']
        )
    if q['name'] == 'cohesive':
        return judge.COHESIVE[0]
    return next(v for v in crit.values() if 'Indexing' in v)


PAGES = [
    (f'https://x.dev/tutorial/p{i}', f'Page {i}', f'postgres indexing guide {i}')
    for i in range(6)
] + [('https://x.dev/blog/cake', 'Cake', 'cooking pasta at home')]


def test_judge_writes_judge_json_with_drop_and_kinds(
    tmp_path: Path, fake: Install
) -> None:
    ws = build_workspace(tmp_path, PAGES)
    fake(judge_policy)
    assert judge.run(ws, argparse.Namespace(tau=0.8)) == 0
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['annotate_only'] is False
    assert out['agreement'] == 1.0
    assert [d['id'] for d in out['drop']] == [7]
    assert out['kind']['1'] == 'tutorial'
    assert out['kind']['7'] == 'reference'


def test_keyword_hit_protects_an_off_topic_page(tmp_path: Path, fake: Install) -> None:
    pages = [
        *PAGES[:6],
        ('https://x.dev/blog/cake', 'Cake', 'cooking with postgres indexing'),
    ]
    ws = build_workspace(tmp_path, pages)
    fake(judge_policy)
    judge.run(ws, argparse.Namespace(tau=0.8))
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['drop'] == []
    assert 'keywords' in out['deferred'][0]['note']


def test_a_goal_too_short_for_keywords_never_authorizes_a_drop(
    tmp_path: Path, fake: Install
) -> None:
    ws = build_workspace(tmp_path, PAGES)
    with ws.open_store() as store:
        store.set_meta('goal', 'AI')
    fake(judge_policy)
    judge.run(ws, argparse.Namespace(tau=0.8))
    assert json.loads(ws.judge_path.read_text('utf-8'))['drop'] == []


def test_calibration_downgrades_to_annotate_only(tmp_path: Path, fake: Install) -> None:
    ws = build_workspace(tmp_path, PAGES)

    def biased_kind(state: str, q: dict[str, Any]) -> str | None:
        return 'A' if q['name'] == 'kind' else judge_policy(state, q)

    fake(biased_kind)
    judge.run(ws, argparse.Namespace(tau=0.8))
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['annotate_only'] is True
    assert out['agreement'] < judge.MIN_AGREEMENT
    assert out['drop'] == []
    assert out['kind'] == {}


def test_consistently_wrong_kind_answers_trip_the_guard(
    tmp_path: Path, fake: Install
) -> None:
    ws = build_workspace(tmp_path, PAGES)

    def wrong_but_steady(state: str, q: dict[str, Any]) -> str | None:
        return judge.KINDS['example'] if q['name'] == 'kind' else judge_policy(state, q)

    fake(wrong_but_steady)
    judge.run(ws, argparse.Namespace(tau=0.8))
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['order_agreement'] == 1.0
    assert out['agreement'] == 0.0
    assert out['annotate_only'] is True


def test_guard_is_unmeasured_without_url_typed_pages(
    tmp_path: Path, fake: Install
) -> None:
    pages = [(f'https://x.dev/misc/{i}', 'm', 'postgres indexing') for i in range(8)]
    ws = build_workspace(tmp_path, pages)
    fake(judge_policy)
    judge.run(ws, argparse.Namespace(tau=0.8))
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['agreement'] is None
    assert out['annotate_only'] is True


def test_calibration_prefers_url_typed_pages(tmp_path: Path) -> None:
    pages = [
        (f'https://x.dev/misc/{i}', 'm', 'postgres indexing') for i in range(30)
    ] + PAGES
    ws = build_workspace(tmp_path, pages)
    with ws.open_store() as store:
        units = store.units(status='done')
    sample = judge.calibration_sample(units)
    assert {u.uri for u in sample} <= {u.uri for u in units if '/tutorial/' in u.uri}


def test_section_question_only_for_orphans_from_the_plan(
    tmp_path: Path, fake: Install
) -> None:
    plan = {
        'sections': [
            {'slug': 'indexing', 'title': 'Indexing', 'files': [{'units': [1]}]},
            {'slug': 'general', 'title': 'General', 'files': [{'units': [2]}]},
        ]
    }
    ws = build_workspace(tmp_path, PAGES[:6], plan)
    router = fake(judge_policy)
    judge.run(ws, argparse.Namespace(tau=0.8))
    asked = [(c[0]['request'], 'section' in c[1]) for c in router.calls]
    assert {'Page 0' in s for s, has in asked if has} == {False}
    assert any('Page 1' in s and has for s, has in asked)
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['section'] == {'2': 'indexing'}


def test_video_leftovers_are_orphans_like_general(tmp_path: Path) -> None:
    plan = {
        'sections': [
            {'slug': 'indexing', 'title': 'Indexing', 'files': [{'units': [1]}]},
            {'slug': 'videos', 'title': 'Videos', 'files': [{'units': [2]}]},
        ]
    }
    ws = build_workspace(tmp_path, PAGES[:6], plan)
    named, orphans = judge._section_options(ws)  # noqa: SLF001
    assert named == [('indexing', 'Indexing')]
    assert orphans == {2}


def test_judge_skips_pages_the_user_dropped(tmp_path: Path, fake: Install) -> None:
    ws = build_workspace(tmp_path, PAGES)
    with ws.open_store() as store:
        store.set_meta('dropped_units', {'7': 'off goal', '1': 'stale'})
    fake(judge_policy)
    assert judge.run(ws, argparse.Namespace(tau=0.8)) == 0
    out = json.loads(ws.judge_path.read_text('utf-8'))
    assert out['drop'] == []
    assert sorted(out['kind'], key=int) == ['2', '3', '4', '5', '6']


def test_judge_skips_with_warning_when_laya_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ws = build_workspace(tmp_path, PAGES[:1])

    def missing() -> None:
        raise client.LayaUnavailableError('no laya')

    monkeypatch.setattr(client, 'get_router', missing)
    assert judge.run(ws, argparse.Namespace(tau=0.8)) == 0
    assert 'skipped' in capsys.readouterr().err
    assert not ws.judge_path.exists()


def test_judge_main_finds_the_workspace(tmp_path: Path, fake: Install) -> None:
    build_workspace(tmp_path, PAGES[:1])
    fake(judge_policy)
    assert judge.main(['--base', str(tmp_path)]) == 0


# --- brain ---------------------------------------------------------------------------

LINKS = [
    Link('https://x.dev/docs/indexes', 'B-tree indexes', 'Indexing'),
    Link('https://x.dev/careers', 'Jobs', 'Footer'),
    Link('https://x.dev/docs/planner', 'Query planner', 'Performance'),
]


def page_policy(state: str, _q: dict[str, Any]) -> str:
    return brain.PAGE_MATCH[0 if 'B-tree' in state else 1]


def test_scorer_ranks_the_relevant_link_first(fake: Install) -> None:
    fake(page_policy)
    scores = brain.LayaScorer('index tuning').score('index tuning', 'Docs', 'Docs', LINKS)
    assert scores == pytest.approx([CONFIDENT, 1 - CONFIDENT, 1 - CONFIDENT])


def test_scorer_asks_each_link_alone_as_a_neutral_two_option_pair(fake: Install) -> None:
    router = fake(page_policy)
    brain.LayaScorer('g').score('g', 'Docs', 'Docs', LINKS)
    assert len(router.calls) == 2 * len(LINKS)
    forward, backward = (c[1]['page']['criteria'] for c in router.calls[:2])
    assert forward == {'A': brain.PAGE_MATCH[0], 'B': brain.PAGE_MATCH[1]}
    assert backward == {'A': brain.PAGE_MATCH[1], 'B': brain.PAGE_MATCH[0]}
    assert router.calls[0][1]['page']['instructions'] == brain.PAGE_INSTRUCTIONS


def test_scorer_describes_a_link_by_anchor_path_words_and_heading(fake: Install) -> None:
    router = fake(page_policy)
    brain.LayaScorer('g').score('g', 'Docs', 'Docs', LINKS[:1])
    assert router.calls[0][0]['request'] == (
        'Page: B-tree indexes | docs indexes | Indexing\nGoal: g'
    )


def test_scorer_describes_a_bare_sitemap_url_by_its_path_words(fake: Install) -> None:
    router = fake(page_policy)
    link = Link('https://x.dev/docs/current/performance-tips.html')
    brain.LayaScorer('g').score('g', '', '', [link])
    assert router.calls[0][0]['request'] == 'Page: docs current performance tips\nGoal: g'


def test_scorer_keeps_the_raw_probability_when_the_orders_disagree(
    fake: Install, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake(page_policy)
    answers = iter([([0.8, 0.2], [0.4, 0.6]), ([0.5, 0.5], [0.5, 0.5])])
    monkeypatch.setattr(brain, 'ask_probs', lambda *_a: {'page': next(answers)})
    scores = brain.LayaScorer('g').score('g', '', '', LINKS[:2])
    assert scores == pytest.approx([0.6, 0.5])


def test_scorer_falls_back_to_neutral_scores_on_error(
    fake: Install, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    router = fake(page_policy)
    scorer = brain.LayaScorer('g')

    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError('torch died')

    monkeypatch.setattr(router, 'predict', boom)
    assert scorer.score('g', 't', 'h', LINKS) == [0.5, 0.5, 0.5]
    scorer.score('g', 't', 'h', LINKS)
    assert capsys.readouterr().err.count('neutral') == 1


def test_scorer_construction_raises_when_laya_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing() -> None:
        raise client.LayaUnavailableError('no laya')

    monkeypatch.setattr(client, 'get_router', missing)
    with pytest.raises(client.LayaUnavailableError):
        brain.LayaScorer('g')


def test_scorer_handles_no_candidates(fake: Install) -> None:
    fake(page_policy)
    assert brain.LayaScorer('g').score('g', 't', 'h', []) == []


# --- video ranking -------------------------------------------------------------------

VIDEOS = [
    {'id': 'a', 'url': 'u/a', 'title': 'Cat compilation', 'duration': 300},
    {
        'id': 'b',
        'url': 'u/b',
        'title': 'B-tree index internals',
        'description': 'How\nindexes work',
        'duration': 1800,
        'upload_date': '20240102',
    },
    {'id': 'c', 'url': 'u/c', 'title': 'Vacuum and bloat'},
]


def video_policy(state: str, _q: dict[str, Any]) -> str | None:
    on_topic = 'B-tree' in state
    return brain.VIDEO_ON_TOPIC[0 if on_topic else 1]


def yt_ctx(tmp_path: Path, goal: str = 'index tuning') -> Ctx:
    ws = Workspace.create('v', tmp_path)
    store = ws.open_store()
    store.set_meta('goal', goal)
    return Ctx.open(ws, store)


def brain_args(brain: str = 'laya') -> argparse.Namespace:
    return argparse.Namespace(brain=brain)


def test_video_ranker_asks_one_two_option_title_question_per_video(
    fake: Install,
) -> None:
    router = fake(video_policy)
    scores, agreed = brain.LayaVideoRanker('index tuning').score(VIDEOS, [0, 0, 0])
    judged = [s if s is not None else -1.0 for s in scores]
    assert judged.index(max(judged)) == 1
    assert all(agreed)
    states = [c[0]['request'] for c in router.calls]
    assert 'title: B-tree index internals' in states[2]
    assert states[4].startswith('Video title: Vacuum and bloat')


def test_video_ranker_judges_evidence_texts_with_the_same_two_option_question(
    fake: Install,
) -> None:
    router = fake(video_policy)
    texts = [
        'Video title: X\nDescription: B-tree pages',
        'Video title: Y\nChapters: cats',
    ]
    high, low = brain.LayaVideoRanker('index tuning').judge(texts)
    assert high > low
    assert len(router.calls) == 2 * len(texts)
    assert router.calls[0][0]['request'] == f'{texts[0]}\nTopic: index tuning'
    assert router.calls[0][1]['video']['instructions'] == brain.VIDEO_INSTRUCTIONS


CHANNEL_GOAL = (
    'AI fundamentals: how large language models work, tokens, context windows, agents'
)
AI_TITLE = ('context window', 'token', 'agent', 'llm')


def channel_listing() -> list[dict]:
    path = Path(__file__).parent / 'fixtures' / 'anything_to_skill' / 'youtube'
    entries = json.loads((path / 'channel_listing.json').read_text('utf-8'))
    return [{**e, 'url': f'https://www.youtube.com/watch?v={e["id"]}'} for e in entries]


def channel_policy(state: str, _q: dict[str, Any]) -> str:
    title = state.split('title: ')[1].split('\n')[0].lower()
    return brain.VIDEO_ON_TOPIC[0 if any(w in title for w in AI_TITLE) else 1]


def test_channel_ranking_judges_keyword_hits_even_when_embeddings_miss_them(
    fake: Install, monkeypatch: pytest.MonkeyPatch
) -> None:
    router = fake(channel_policy)

    def unrelated_embeddings(texts: list[str]) -> list[list[float]]:
        return [list(hashlib.sha256(t.encode()).digest()[:8]) for t in texts]

    monkeypatch.setattr(client, 'embed_fn', lambda: unrelated_embeddings)
    monkeypatch.setattr(brain, 'CANDIDATES_PER_SIGNAL', 10)
    entries = channel_listing()
    chosen, record = yt_run.rank(
        entries, CHANNEL_GOAL, 5, brain.LayaVideoRanker(CHANNEL_GOAL)
    )
    titles = [e['title'] for e, _ in chosen]
    assert any('context windows' in t for t in titles)
    assert any('LLM tokens' in t for t in titles)
    assert not any('TypeScript' in t for t in titles)
    assert 0 < record['judged'] < len(entries)
    assert all(row['laya'] > 0 for row in record['chosen'] + record['skipped'])
    # every candidate is one neutral two-option question, in both orders
    assert all(len(q['criteria']) == PAIR for _, qs in router.calls for q in qs.values())
    assert len(router.calls) == 2 * record['judged']


def test_unjudged_videos_are_scored_neutral_never_zero() -> None:
    class Partial:
        def score(self, _entries: list[dict], _hits: list[int]) -> tuple[list, list]:
            return [None, 0.1, 0.9], [False, True, True]

    _, record = yt_run.rank(VIDEOS, 'zzz', 3, Partial())
    by_id = {r['id']: r for r in record['chosen']}
    assert by_id['a']['laya'] == yt_run.UNJUDGED_LAYA
    assert by_id['a']['score'] > by_id['b']['score']


def test_keyword_selection_matches_word_starts_not_substrings() -> None:
    entries = [{'title': 'Barcode scanner'}, {'title': 'Code review tips'}]
    assert [e['title'] for e, _ in yt_run.select(entries, 'code', 5)] == [
        'Code review tips'
    ]


def test_router_load_hides_the_uncalibrated_bucket_warning_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Router:
        def __init__(self, **_kw: object) -> None: ...

        def load(self, _name: str) -> None:
            warnings.warn(
                'laya: this checkpoint ships invalid temperatures or values',
                RuntimeWarning,
                stacklevel=2,
            )
            warnings.warn('something else', RuntimeWarning, stacklevel=2)

    monkeypatch.setitem(sys.modules, 'laya', SimpleNamespace(Router=Router))
    client.get_router.cache_clear()
    with pytest.warns(RuntimeWarning, match='something else') as seen:
        client.get_router()
    assert [str(w.message) for w in seen] == ['something else']
    client.get_router.cache_clear()


def test_rank_blends_keywords_and_records_chosen_and_skipped(fake: Install) -> None:
    fake(lambda _s, _q: None)  # a model with no opinion: keywords must still order
    ranker = brain.LayaVideoRanker('g')
    chosen, record = yt_run.rank(VIDEOS, 'B-tree index', 1, ranker)
    assert [e['id'] for e, _ in chosen] == ['b']
    assert record['candidates'] == len(VIDEOS)
    assert [r['id'] for r in record['chosen']] == ['b']
    assert [r['id'] for r in record['skipped']] == ['a', 'c']
    assert record['skipped_total'] == len(VIDEOS) - 1
    assert record['chosen'][0]['keywords'] > 0
    assert record['chosen'][0]['score'] > record['skipped'][0]['score']


def test_choose_ranks_with_laya_and_stores_the_ranking(
    fake: Install, tmp_path: Path
) -> None:
    fake(video_policy)
    ctx = yt_ctx(tmp_path, goal='zzz')
    seed = ctx.store.get(ctx.store.add_unit('youtube', 'https://y/c', kind='seed'))
    picked = yt_run.choose(ctx, brain_args(), yt_run.RunSummary(), seed, VIDEOS, 1)
    assert [e['id'] for e, _ in picked] == ['b']
    stored = ctx.store.get_meta('youtube.ranking')['https://y/c']
    assert stored['method'] == 'laya'
    assert stored['chosen'][0]['id'] == 'b'


def test_choose_skips_laya_when_the_listing_fits_the_cap(
    fake: Install, tmp_path: Path
) -> None:
    router = fake(video_policy)
    ctx = yt_ctx(tmp_path)
    seed = ctx.store.get(ctx.store.add_unit('youtube', 'https://y/c', kind='seed'))
    yt_run.choose(ctx, brain_args(), yt_run.RunSummary(), seed, VIDEOS, len(VIDEOS))
    assert not router.calls
    assert ctx.store.get_meta('youtube.ranking') is None


def test_choose_falls_back_to_keywords_when_laya_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def missing() -> None:
        raise client.LayaUnavailableError('no laya')

    monkeypatch.setattr(client, 'get_router', missing)
    ctx = yt_ctx(tmp_path, goal='vacuum')
    seed = ctx.store.get(ctx.store.add_unit('youtube', 'https://y/c', kind='seed'))
    summary = yt_run.RunSummary()
    yt_run.choose(ctx, brain_args(), summary, seed, VIDEOS, 1)
    picked = yt_run.choose(ctx, brain_args(), summary, seed, VIDEOS, 1)
    assert [e['id'] for e, _ in picked] == ['c']
    assert capsys.readouterr().err.count('unavailable') == 1
    assert ctx.store.get_meta('youtube.ranking') is None


def test_choose_falls_back_to_keywords_when_ranking_raises(
    fake: Install, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    router = fake(video_policy)
    ctx = yt_ctx(tmp_path, goal='vacuum')
    seed = ctx.store.get(ctx.store.add_unit('youtube', 'https://y/c', kind='seed'))

    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError('torch died')

    monkeypatch.setattr(router, 'predict', boom)
    summary = yt_run.RunSummary()
    picked = yt_run.choose(ctx, brain_args(), summary, seed, VIDEOS, 1)
    assert [e['id'] for e, _ in picked] == ['c']
    assert any('ranking failed' in e for e in summary.errors)


def test_choose_never_uses_laya_under_the_rules_brain(
    fake: Install, tmp_path: Path
) -> None:
    router = fake(video_policy)
    ctx = yt_ctx(tmp_path)
    seed = ctx.store.get(ctx.store.add_unit('youtube', 'https://y/c', kind='seed'))
    yt_run.choose(ctx, brain_args('rules'), yt_run.RunSummary(), seed, VIDEOS, 1)
    assert not router.calls


def test_sources_md_lists_kept_and_skipped_videos() -> None:
    row = {
        'id': 'a',
        'title': 'Cat compilation',
        'score': 0.12,
        'laya': 0.1,
        'keywords': 0,
    }
    top = {**row, 'id': 'b', 'title': 'B-tree internals', 'score': 0.9}
    record = {'candidates': 2, 'chosen': [top], 'skipped': [row]}
    text = '\n'.join(write.ranking_lines({'https://y/c': record}))
    assert '1 of 2 videos kept' in text
    assert '- kept 0.9: B-tree internals' in text
    assert '- skipped 0.12: Cat compilation' in text
    assert write.ranking_lines({}) == []
    read = {**top, 'meta': 0.8, 'transcript': 0.7}
    deep = '\n'.join(
        write.ranking_lines(
            {
                'https://y/c': {
                    **record,
                    'chosen': [read],
                    'funnel': {
                        'meta': {'asked': 2, 'scored': 2},
                        'transcripts': {'asked': 1, 'scored': 1},
                        'throttled': 'transcripts',
                    },
                }
            }
        )
    )
    assert (
        '- kept 0.9 (title 0.1, description 0.8, transcript 0.7): B-tree internals'
        in deep
    )
    assert '2 on description and chapters, 1 on captions; transcripts throttled' in deep
    cut = '\n'.join(write.ranking_lines({'https://y/c': record}, frozenset({'b'})))
    assert '0 of 2 videos kept' in cut
    assert '- dropped 0.9: B-tree internals' in cut


# --- factcheck -----------------------------------------------------------------------

PASSAGE = (
    'Autovacuum runs automatically. The default is to keep it enabled for all tables.'
)


def support_policy(state: str, q: dict[str, Any]) -> str | None:
    """Ideal model, negation-aware: claim and passage must agree on 'not'."""
    if q['criteria'] and 'passage' in next(iter(q['criteria'].values())).lower():
        claim, _, passage = state.partition('\nPassage: ')
        same = (' not ' in claim) == (' not ' in passage)
        return factcheck.SUPPORT[0 if same else 1]
    if q['name'] == 'q' and 'file' in next(iter(q['criteria'].values())).lower():
        desc, _, file_text = state.partition('\nFile: ')
        ok = any(
            w in file_text.lower() for w in desc.lower().split() if len(w) > MIN_WORD
        )
        return factcheck.MATCH[0 if ok else 1]
    return None


def write_authored(ws: Workspace, name: str, text: str) -> None:
    path = ws.authored_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def factcheck_workspace(tmp_path: Path) -> Workspace:
    return build_workspace(
        tmp_path,
        [('https://x.dev/docs/vacuum', 'Vacuum', PASSAGE)],
        {
            'sections': [
                {
                    'slug': 'maintenance',
                    'title': 'Maintenance',
                    'files': [{'path': 'maintenance/vacuum.md', 'units': [1]}],
                }
            ]
        },
    )


def set_summary(ws: Workspace, summary: str) -> None:
    plan = json.loads(ws.plan_path.read_text('utf-8'))
    plan['sections'][0]['files'][0]['summary'] = summary
    ws.plan_path.write_text(json.dumps(plan), encoding='utf-8')


def test_support_check_flags_a_negated_claim_with_a_real_quote(
    tmp_path: Path, fake: Install
) -> None:
    ws = factcheck_workspace(tmp_path)
    write_authored(
        ws,
        'best-practices.md',
        '# Tips\n\n'
        'Autovacuum is on by default (src: 1 "keep it enabled for all tables").\n'
        'Autovacuum is not on by default (src: 1 "keep it enabled for all tables").\n',
    )
    fake(support_policy)
    findings = factcheck.run(ws)
    flagged = [f for f in findings if f.rule == 'laya-support']
    assert len(flagged) == 1
    assert flagged[0].line == NEGATED_LINE
    assert 'not on by default' in flagged[0].message
    assert {f.severity for f in findings} == {'warn'}


def test_order_disagreement_is_reported_not_flagged(
    tmp_path: Path, fake: Install
) -> None:
    ws = factcheck_workspace(tmp_path)
    write_authored(ws, 'best-practices.md', 'It is on (src: 1 "keep it enabled").\n')
    fake(lambda _s, _q: 'A')
    assert factcheck.run(ws) == []
    laya = json.loads(ws.verify_path.read_text('utf-8'))['laya']
    assert laya['order_agreement'] == 0.0
    assert laya['checks'] == 1


def test_quote_that_is_not_in_the_unit_is_left_to_the_quote_scanner(
    tmp_path: Path, fake: Install
) -> None:
    ws = factcheck_workspace(tmp_path)
    write_authored(ws, 'best-practices.md', 'Claim here (src: 1 "never said this").\n')
    router = fake(support_policy)
    assert factcheck.run(ws) == []
    assert router.calls == []


def test_unsourced_sentences_are_attributed_or_flagged(
    tmp_path: Path, fake: Install, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = factcheck_workspace(tmp_path)
    write_authored(
        ws,
        'SKILL.md',
        '---\nname: x\n---\n\n# Hub\n\n'
        'Autovacuum runs automatically on every table in the database.\n'
        'Autovacuum is not enabled for any table in the database at all.\n',
    )

    def embed(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(client, 'embed_fn', lambda: embed)
    fake(support_policy)
    rules = {f.rule for f in factcheck.run(ws)}
    assert rules == {'laya-attributed', 'laya-unsupported'}


def test_a_supporting_chunk_among_the_nearest_three_clears_the_sentence(
    tmp_path: Path, fake: Install, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = [
        ('https://x.dev/docs/a', 'A', 'Autovacuum is not run on this page at all.'),
        ('https://x.dev/docs/b', 'B', 'Autovacuum runs on every table by default.'),
        ('https://x.dev/docs/c', 'C', 'Autovacuum is not tuned on this page either.'),
    ]
    ws = build_workspace(tmp_path, pages)
    write_authored(
        ws,
        'SKILL.md',
        '---\nname: x\n---\n\n# Hub\n\n'
        'Autovacuum runs automatically on every table in the database.\n',
    )
    # equal vectors: the nearest chunks come back in corpus order, a wrong one first
    monkeypatch.setattr(
        client, 'embed_fn', lambda: lambda texts: [[1.0, 0.0]] * len(texts)
    )
    fake(support_policy)
    assert {f.rule for f in factcheck.run(ws)} == {'laya-attributed'}


def test_routing_and_index_rows_are_checked(
    tmp_path: Path, fake: Install, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = factcheck_workspace(tmp_path)
    write_authored(
        ws,
        'SKILL.md',
        '| When | Read |\n|---|---|\n'
        '| Tuning autovacuum | references/maintenance/vacuum.md |\n'
        '| Designing partitions | references/maintenance/vacuum.md |\n',
    )
    set_summary(ws, 'Autovacuum defaults and tuning')
    monkeypatch.setattr(client, 'embed_fn', lambda: lambda t: [[1.0] for _ in t])
    fake(support_policy)
    findings = factcheck.run(ws)
    routing = [f for f in findings if f.rule == 'laya-routing']
    assert [f.line for f in routing] == [4]
    assert not [f for f in findings if f.rule == 'laya-index']


def test_split_plan_file_is_checked_against_its_own_slice(tmp_path: Path) -> None:
    ws = factcheck_workspace(tmp_path)
    with ws.open_store() as store:
        text = store.read_markdown(1)
        cut = len(text) // 2
        entry = {'units': [1], 'parts': [{'unit': 1, 'start': cut, 'end': len(text)}]}
        assert factcheck._plan_text(store, entry) == text[cut:]  # noqa: SLF001


def test_mislabelled_index_row_is_flagged(tmp_path: Path, fake: Install) -> None:
    ws = factcheck_workspace(tmp_path)
    set_summary(ws, 'Replication topologies')
    fake(support_policy)
    assert [f.rule for f in factcheck.run(ws)] == ['laya-index']


def test_verify_json_is_merged_and_authored_files_are_untouched(
    tmp_path: Path, fake: Install
) -> None:
    ws = factcheck_workspace(tmp_path)
    body = 'Autovacuum is not on by default (src: 1 "keep it enabled for all tables").\n'
    write_authored(ws, 'best-practices.md', body)
    ws.verify_path.write_text(json.dumps({'hard_fails': 0}), encoding='utf-8')
    fake(support_policy)
    factcheck.run(ws)
    data = json.loads(ws.verify_path.read_text('utf-8'))
    assert data['hard_fails'] == 0
    assert data['laya']['flags'][0]['rule'] == 'laya-support'
    assert (ws.authored_dir / 'best-practices.md').read_text('utf-8') == body


def test_factcheck_skips_with_warning_when_laya_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ws = factcheck_workspace(tmp_path)

    def missing() -> None:
        raise client.LayaUnavailableError('offline')

    monkeypatch.setattr(client, 'get_router', missing)
    assert factcheck.run(ws) == []
    assert 'skipped' in capsys.readouterr().err
    assert 'offline' in json.loads(ws.verify_path.read_text('utf-8'))['laya']['skipped']


def testprose_lines_skip_frontmatter_fences_and_headings(tmp_path: Path) -> None:
    path = tmp_path / 'a.md'
    path.write_text('---\nname: x\n---\n# H\n```\ncode line\n```\nreal prose\n', 'utf-8')
    assert factcheck.prose_lines(path) == [(8, 'real prose')]
