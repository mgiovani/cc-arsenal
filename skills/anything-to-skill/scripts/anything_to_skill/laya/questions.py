from anything_to_skill.laya import client

LETTERS = 26


def _key(position: int) -> str:
    # Neutral labels only: the model follows label text, so no yes/no or meaningful keys.
    return chr(65 + position) if position < LETTERS else f'Z{position}'


def ask_probs(
    state: str, specs: dict[str, tuple[str, list[str]]]
) -> dict[str, tuple[list[float], list[float]]]:
    """Ask every spec (instructions, options) in original then reversed option order.

    Returns name -> (forward, reversed) probabilities, both indexed by original option.
    """
    rows: dict[str, list[list[float]]] = {name: [] for name in specs}
    for reverse in (False, True):
        orders = {
            name: list(range(len(opts)))[:: -1 if reverse else 1]
            for name, (_, opts) in specs.items()
        }
        questions = {
            name: {
                'type': 'choice',
                'instructions': specs[name][0],
                'criteria': {_key(pos): specs[name][1][i] for pos, i in enumerate(order)},
            }
            for name, order in orders.items()
        }
        answers = client.predict({'request': state}, questions)['answers']
        for name, order in orders.items():
            probs = answers[name]['probabilities']
            row = [0.0] * len(order)
            for pos, i in enumerate(order):
                row[i] = float(probs.get(_key(pos), 0.0))
            rows[name].append(row)
    return {name: (r[0], r[1]) for name, r in rows.items()}


def agree(forward: list[float], backward: list[float]) -> tuple[int, float] | None:
    """(index, confidence) when both orders pick the same option, else None."""
    best = max(range(len(forward)), key=forward.__getitem__)
    if best != max(range(len(backward)), key=backward.__getitem__):
        return None
    return best, min(forward[best], backward[best])


def ask_many(
    state: str, specs: dict[str, tuple[str, list[str]]]
) -> dict[str, tuple[int, float] | None]:
    """Several questions about one state; None for a question whose orders disagree."""
    return {name: agree(*pair) for name, pair in ask_probs(state, specs).items()}
