# Evals

Two separate things: the evals the skill ships inside the generated skill, and the opt-in run that proves the skill helps.

## Generated evals

The LLM pass writes `evals.json` and `trigger-eval.json` into `authored/`; `emit` places them in the skill's `evals/`. They follow the repo schema.

`evals.json`:

```json
{
  "skill": "<name>",
  "evals": [
    {"id": "short-slug", "prompt": "a realistic user request", "assertions": ["a checkable statement", "..."]}
  ]
}
```

- 3-6 evals. Each prompt is something a real user would type, answerable only with knowledge from the corpus.
- 3-5 assertions each, and every assertion is about the answer's content or outcome: a specific setting, command, value or decision from the sources. "Is accurate" is not an assertion, and neither is "reads references/X.md" or "opens INDEX": a run without the skill fails a file-read check for free, so it measures nothing. `verify` warns on such assertions; `compact-verify` fails on them.
- Target source-specific knowledge the base model likely lacks or gets wrong: exact flags and defaults, version-specific behavior, the source's own recommendations and numbers, non-obvious gotchas. An eval any model answers correctly without the skill proves nothing.
- Build them from the corpus: pick a hard fact from a reference file and ask for it indirectly.

`trigger-eval.json`: an array of `{"query": "...", "should_trigger": true|false}` with at least six of each. The false cases are near misses (same technology, different task), not unrelated noise.

## Opt-in comparison run (phase 8)

Costs tokens, so ask first.

1. Executors see only the prompts: `evals-freeze` writes `<ws>/eval-prompts.json` (id and prompt, no assertions), and each executor also gets its skill directory copied without `evals/`. Executors read the skill files directly, not saved tool output. Graders alone receive the assertions.
2. Run each eval prompt twice: once with the generated skill available, once without. `create-skill`'s `run_eval.py` and `generate_report.py` do this and grade the assertions; without them, run two subagent batches yourself and grade each assertion pass or fail with a one-line evidence quote.
3. Run the no-skill batch first. If its pass rate is above 0.8, the evals do not measure the skill: replace the easy ones with source-specific ones and re-run the baseline before comparing, and report that. Then compare pass rates per eval. The interesting rows are the ones where the skill did not help: either the corpus lacks the fact (a coverage gap to report) or the routing sends the agent to the wrong file (a routing bug to fix).
4. Present the result with the `render` skill in `report` mode (via the `Skill` tool where available, otherwise apply its steps inline: a self-contained HTML page with a section per eval and anchored comments). Read the user's marks back and act on them.

Do not modify assertions to make a run pass. If an assertion is wrong, say so and fix it openly.
