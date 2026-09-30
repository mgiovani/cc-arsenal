import math
import re
import sys
from typing import Any
from urllib.parse import urlparse

from anything_to_skill.laya import client
from anything_to_skill.laya.questions import agree, ask_probs
from anything_to_skill.sources.web.frontier import Link

# One 100-way "which link?" choice put every option in the uncalibrated `choice:11+`
# bucket and was min-max normalised, so on the postgres docs sql-create* pages scored 0.94
# and performance-tips 0.0. Each page instead gets its own two-option question (the
# calibrated `choice:2` bucket) in both orders, like the videos below. Asking with the
# page first and the goal last ranked best (AUC 0.74 against 0.69 the other way round).
PAGE_INSTRUCTIONS = 'Does this page match the goal?'
PAGE_MATCH = ['The page matches the goal.', 'The page does not match the goal.']
# Measured on the recorded 143-video channel listing (scripts/tests/fixtures): asking
# whether the *video* is about the topic, with the title first, ranks on-goal videos
# higher than 'does the title match the topic?' (AUC 0.72 vs 0.67 for an AI goal, 0.94
# vs 0.73 for a TypeScript goal).
VIDEO_INSTRUCTIONS = 'Is this video about the topic?'
VIDEO_ON_TOPIC = ['The video is about the topic.', 'The video is not about the topic.']
CANDIDATES_PER_SIGNAL = 100
ANCHOR_CHARS = 50
PATH_CHARS = 40
TITLE_CHARS = 70
_PATH_SEPARATORS = re.compile(r'[-_/.]+')
_EXTENSION = re.compile(r'\.(html?|php|aspx?|md)$', re.I)


def _describe(link: Link) -> str:
    """What is known of a page before fetching it: anchor text, URL path words, heading."""
    path = _PATH_SEPARATORS.sub(' ', _EXTENSION.sub('', urlparse(link.url).path)).strip()
    parts = [
        link.anchor.strip()[:ANCHOR_CHARS],
        path[-PATH_CHARS:],
        link.heading.strip()[:ANCHOR_CHARS],
    ]
    return ' | '.join(p for p in parts if p) or link.url[:PATH_CHARS]


def _match_prob(
    name: str, state: str, instructions: str, options: list[str]
) -> tuple[float, bool]:
    """(mean p(first option) over both option orders, whether the orders agreed)."""
    forward, backward = ask_probs(state, {name: (instructions, options)})[name]
    return (forward[0] + backward[0]) / 2, agree(forward, backward) is not None


def _video_title(entry: dict[str, Any]) -> str:
    title = ' '.join(str(entry.get('title') or '').split())[:TITLE_CHARS]
    return title or str(entry.get('url', ''))[:PATH_CHARS]


class LayaScorer:
    """LinkScorer backed by Laya: p(page matches the goal), averaged over both option orders.

    Raises LayaUnavailableError at construction so the caller can fall back to rules; any later
    failure only yields neutral scores, since a wrong ranking changes fetch order and never
    content. The raw probability is kept (no collapsing of order disagreement to a constant),
    so an unsure page still sits between a confident match and a confident miss.
    """

    def __init__(self, goal: str) -> None:
        self.goal = goal
        client.get_router()
        self._warned = False

    def score(
        self,
        goal: str,
        page_title: str,  # noqa: ARG002 - the linking page says nothing about the candidate
        heading_path: str,  # noqa: ARG002
        candidates: list[Link],
    ) -> list[float]:
        try:
            scores = [
                _match_prob(
                    'page',
                    f'Page: {_describe(link)}\nGoal: {goal or self.goal}',
                    PAGE_INSTRUCTIONS,
                    PAGE_MATCH,
                )[0]
                for link in candidates
            ]
        except Exception as exc:  # noqa: BLE001 - benign by design, see class docstring
            if not self._warned:
                print(
                    f'laya brain: falling back to neutral scores ({exc})', file=sys.stderr
                )
                self._warned = True
            return [0.5] * len(candidates)
        return scores


class LayaVideoRanker:
    """Judges channel or playlist entries against the goal one at a time. Unlike LayaScorer,
    a failure raises: the ranking decides which videos get fetched, so the caller falls
    back to keyword selection instead of accepting neutral scores.

    A 20-way choice would put every option in the checkpoint's uncalibrated `choice:11+`
    bucket and, past the shortlist, score the rest 0. Each candidate instead gets its own
    two-option question (the calibrated `choice:2` bucket) asked in both orders, and the
    candidates are the union of the best keyword and embedding matches, so an on-topic
    title is judged even when the embedding misses it.
    """

    def __init__(self, goal: str) -> None:
        self.goal = goal
        client.get_router()

    def candidates(self, options: list[str], hits: list[int]) -> list[int]:
        """Indexes worth judging: top keyword matches plus nearest embeddings."""
        if len(options) <= 2 * CANDIDATES_PER_SIGNAL:
            return list(range(len(options)))
        by_keywords = sorted(
            (i for i, h in enumerate(hits) if h > 0), key=lambda i: (-hits[i], i)
        )[:CANDIDATES_PER_SIGNAL]
        return sorted({*by_keywords, *self._nearest(options, CANDIDATES_PER_SIGNAL)})

    def _nearest(self, options: list[str], k: int) -> list[int]:
        query, *rows = (
            [float(x) for x in v] for v in client.embed_fn()([self.goal, *options])
        )
        norm = math.sqrt(sum(x * x for x in query)) or 1.0
        sims = [
            sum(a * b for a, b in zip(query, row, strict=True))
            / (norm * (math.sqrt(sum(x * x for x in row)) or 1.0))
            for row in rows
        ]
        return sorted(range(len(rows)), key=lambda i: -sims[i])[:k]

    def score(
        self, entries: list[dict[str, Any]], hits: list[int]
    ) -> tuple[list[float | None], list[bool]]:
        """(on-topic probability per entry, orders agreed per entry).

        None means the entry was not judged. The score is the raw probability averaged over
        both option orders: collapsing disagreement to 0.5 put every unsure video above the
        confidently off-topic ones (mean ~0.33) and tied them, hiding real differences.
        """
        options = [_video_title(e) for e in entries]
        scores: list[float | None] = [None] * len(entries)
        agreed = [False] * len(entries)
        for i in self.candidates(options, hits):
            scores[i], agreed[i] = _match_prob(
                'video',
                f'Video title: {options[i]}\nTopic: {self.goal}',
                VIDEO_INSTRUCTIONS,
                VIDEO_ON_TOPIC,
            )
        return scores, agreed

    def judge(self, evidence: list[str]) -> list[float]:
        """On-topic probability of each evidence text (description, chapters or a transcript
        excerpt). Same two-option question as `score`, so stage scores are comparable."""
        return [
            _match_prob(
                'video', f'{text}\nTopic: {self.goal}', VIDEO_INSTRUCTIONS, VIDEO_ON_TOPIC
            )[0]
            for text in evidence
        ]
