# Judge

Optional, advisory, and local. `judge.py` uses Laya, a small local model, to review each page against the goal before the deterministic plan. It runs after ingest and before `a2s.py plan`; its only output is `.cc-arsenal/a2s/<slug>/judge.json`, which `plan --overrides` consumes. If Laya is not installed or the machine is offline, the judge is skipped with a warning and the pipeline is unaffected.

## Why so guarded

The model's out-of-the-box accuracy is modest, and a yes/no question tends to follow the wording of its labels. So the judge never asks a yes/no question, never lets one answer change content on its own, and measures itself before trusting itself.

## Input per page

The goal, the page title, its path and its first ~200 tokens. Long pages use the model's long-input mode.

## Questions

All are two-or-more-option `choice` questions with neutral keys (A, B, C), and every one is asked twice with the options in opposite order. A label is kept only when both orders agree.

| Question | Options | Effect |
|---|---|---|
| `on_topic` | relevant to the goal / not | may drop the page (see rules) |
| `kind` | reference, tutorial, example, concept | annotates INDEX only |
| `cohesive` | one topic / several | advisory; deferred to the LLM |
| `section` | up to 20 candidate section slugs | asked only for orphan or `general` pages |

## Apply rules (deterministic)

- Drop a page only when `on_topic` is "not relevant", confidence is at least the threshold, both orderings agree, **and** the page has no goal-keyword hit. Never drop at `complete` effort.
- Only orphan or `general` pages get a `section` override. An established section is never moved.
- `kind` only annotates INDEX.md.
- Everything else, including all disagreements and every `cohesive` answer, goes to `deferred` for the LLM.

## Calibration guard

The judge first runs `kind` on up to 20 pages whose type is known from the URL (`/tutorial/`, `/api/`, `/examples/`) and scores how often its answer (both orders agreeing) equals the URL's type. Only URL-typed pages are sampled, so a model that is consistently wrong cannot pass. Below 0.7 the judge switches to annotate-only: no drops, no moves, and `annotate_only` is true in `judge.json`. With fewer than 5 URL-typed pages the guard cannot measure anything: `agreement` is `null` and the judge stays annotate-only. `order_agreement`, how often the two option orders agreed on `kind`, is recorded separately.

## judge.json

```json
{
  "version": 1,
  "annotate_only": false,
  "agreement": 0.85,
  "order_agreement": 0.95,
  "drop": [{"id": 12, "reason": "off-topic"}],
  "section": {"31": "indexing"},
  "kind": {"5": "tutorial"},
  "deferred": [{"id": 8, "note": "covers two topics"}]
}
```

`plan --overrides` applies `drop`, `section` and `kind`. `deferred` is shown in `review.md` for the LLM pass.

## Related: video ranking

`youtube_brain.py` reuses the same both-order `choice` questions to rank channel and playlist videos before they are fetched (see [sources.md](sources.md)). It is advisory too: it picks which videos to fetch, never edits their content, and a ranking whose two orders disagree on the top pick is recorded as such in `youtube.ranking`.

## Reviewing the result

Read `agreement` and `annotate_only` first. If the drop list is long relative to the corpus, sample two or three dropped pages by id before presenting the tree; a judge that drops a page the user cares about is the failure to catch. The user's approval at the tree review is the final gate.
