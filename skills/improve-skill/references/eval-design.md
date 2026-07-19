# Eval Design Rules

Rules for authoring `evals/evals.json` and `evals/trigger-eval.json`, and for grading benchmark runs against them. Load this before writing or grading evals in steps 3 and 5 of `SKILL.md`.

## evals/evals.json

Exactly 3 scenarios per skill: a happy path, a judgment case (ambiguous input, no single correct output), and an edge case or refusal.

```json
{
  "skill": "<name>",
  "evals": [
    {"id": "kebab-case-id", "prompt": "exact trigger phrase a user would type", "assertions": ["..."]}
  ]
}
```

- **A correct refusal must be able to score 100%.** Never bundle a "should refuse" assertion in the same scenario as assertions that only make sense if the skill proceeded past the refusal point — a run that correctly stops early can't satisfy both, and that isn't a flaw in the run, it's a flaw in the eval. Split guard behavior into its own scenario.
- **Refusal/precondition scenarios assert that no mutating command ran** — no file writes outside what was explicitly requested, no `git commit`/`push`, no destructive Bash. A broken "helpful" auto-fix that ignores the guard and does the thing anyway should fail this assertion, not slip through because the report merely mentions the refusal.
- **No assertion may require mid-run interactive input.** A sandboxed eval run can't pause for a reply. Where the skill needs the user to answer something, assert that the final message asks the right question and stops there — not that the conversation continued past it.
- **Bake fixtures into the prompt.** Any sample file contents, repo state, or command output the scenario depends on goes directly into the eval prompt as a `SANDBOX SETUP (do this first, exactly): ...` block, so the scenario is deterministic on any host and doesn't depend on a live tool or network call succeeding.
- **Assertions discriminate.** Each one should plausibly fail for bad output and pass for good output — check structure and content, not filename existence or that a section merely appears.

## evals/trigger-eval.json

Top-level JSON array (no wrapper object) of `{"query": "...", "should_trigger": true|false}`, ~20 entries, roughly half `false`. The negatives should be realistic near-misses drawn from sibling skills' territory — the phrasings a loose description would wrongly catch — not obviously unrelated queries, which don't discriminate anything.

## Grading output — evals/results/{eval_id}/grading.json

Every grading pass, whether comparing `new_skill` vs `old_skill` or checking a single config in the no-subagent fallback, is graded deterministically: read the actual output/file state/transcript, never trust a run's self-report of "assertion passed."

```json
{
  "eval_id": "eval-1",
  "skill_name": "<name>",
  "config": "new_skill",
  "expectations": [
    {"assertion": "...", "pass": true, "reasoning": "grounded in what the transcript/output actually showed"}
  ],
  "summary": "one-line verdict: what passed, what didn't, and why"
}
```

The `summary` field is required on every `grading.json` — it's what the aggregation step in `SKILL.md` reads to build the per-eval verdict table without re-reading every transcript. A `grading.json` missing `summary` is treated the same as a missing run (see Scanning for missing runs below).

For a `new_skill` vs `old_skill` comparison, produce one `grading.json` per config per eval (same shape, different `config` value) so the aggregator can diff them.

## Scanning for missing runs

Before aggregating, confirm a `grading.json` exists for every `(eval, config)` pair that was supposed to run. A small fraction of sandboxed executor runs silently produce nothing (crash, timeout, wrong output path) — treating a missing run as an automatic 0 instead of re-running it silently poisons the aggregate score. Re-run only the missing ones.

## Anti-overfit invariants

- Once an eval's `prompt` or `assertions` are written and a baseline grading exists against them, don't edit them to make a subsequently-failing rewrite pass. If an assertion turns out to have been wrong when written (not: inconvenient now that a run failed it), say so explicitly to the user and get sign-off before changing it — silent tightening or loosening after seeing a result is the exact overfitting this whole benchmark step exists to catch.
- If one run out of an otherwise-consistent set contradicts its siblings (e.g. one 0/N against a pattern of passes elsewhere), treat it as a variance probe — re-run that one config once more and keep both gradings — rather than rewriting the skill around a single anomalous run.
