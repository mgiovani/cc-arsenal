import functools
import importlib
import os
import warnings
from collections.abc import Callable, Sequence
from typing import Any

MODEL = 'english'
SHORTLIST_K = 20


class LayaUnavailableError(RuntimeError):
    pass


def _laya() -> Any:
    return importlib.import_module('laya')


@functools.cache
def get_router() -> Any:
    """Load the Laya router once. Raises LayaUnavailableError when laya is missing or offline."""
    try:
        router = _laya().Router(
            default=MODEL, max_loaded=1, device=os.environ.get('LAYA_DEVICE') or None
        )
        with warnings.catch_warnings():
            # The checkpoint fits `choice:11+` at T=0.1 (a 10x sharpening) and laya clamps it
            # to 0.5, so probabilities of questions with more than 10 options are
            # uncalibrated. Nothing here gates on them: tau reads two-option questions
            # (`choice:2`, T=1.9, valid) and wider ones rely on both-order agreement.
            warnings.filterwarnings(
                'ignore', message='laya: this checkpoint ships invalid temperatures'
            )
            # Load now so a missing download shows up here, not mid-run.
            router.load(MODEL)
    except ImportError as exc:
        raise LayaUnavailableError(
            'laya is not installed (run through verify_laya.py [--compact], judge.py or crawl_brain.py)'
        ) from exc
    except Exception as exc:
        raise LayaUnavailableError(f'laya model could not load: {exc}') from exc
    return router


@functools.cache
def embed_fn() -> Callable[[Sequence[str]], Any]:
    """Encoder embeddings from the already-loaded checkpoint, for retrieval and shortlisting."""
    return _laya().embed_fn_from_agent(get_router().load(MODEL))


def predict(
    state: Any, questions: dict[str, dict[str, Any]], k: int = SHORTLIST_K
) -> dict[str, Any]:
    """One forward pass; choice questions with more than k options are shortlisted first."""
    router = get_router()
    if any(
        q.get('type') == 'choice' and len(q['criteria']) > k for q in questions.values()
    ):
        return _laya().predict_shortlist(
            router, state, questions, embed_fn=embed_fn(), k=k
        )
    return router.predict(state, questions)
