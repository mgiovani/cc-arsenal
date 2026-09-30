# Compaction rubric (phase 9)

Turn the emitted skill, a source mirror with a routing hub, into a lean expert skill: what a senior practitioner would hand a colleague, not a copy of the docs. You write it into `.cc-arsenal/a2s/<slug>/compact/` from `compact-brief.md`. Scripts check the mechanics; this file is the judgment.

## Output shape

```
compact/
  SKILL.md              hub: when to use, core workflow, decision rules, routing
  references/<task>.md  2-6 files, grouped by task, not by source or page
  evals/evals.json      frozen copy of the full skill's evals, verbatim (never edited)
  evals/trigger-eval.json
```

No `INDEX.md`, `SOURCES.md` or one-file-per-page mirror. Frontmatter is `name` (unchanged) and `description` only.

Budgets, checked by `compact-verify`: hub at most ~150 lines (hard limit 499); references together at most 25% of the mirror's tokens; each reference file under ~3k tokens so one read holds one task.

## Cut

- What the model already knows: language basics, generic advice ("write tests", "handle errors"), what a common tool is for.
- Restated documentation: the same rule said in three pages says once, in the place it is used.
- Navigation and framing: introductions, "in this guide", tables of contents, next/previous links, changelog banners.
- Attribution and provenance: `(src: ...)` markers, source links, URLs of the crawled sites, "the docs say", the words "mirror", "INDEX" and "SOURCES". The skill speaks as the expert, not as a citation.
- Long prose around a command: keep the command and the one condition that decides when to run it.
- Anything the eval prompts and the goal never need.

## Keep

- Decision rules: "If X, do Y; otherwise Z", with the threshold or default that decides.
- Exact commands, flags, config keys, defaults, limits and version-specific behavior, character for character.
- Non-obvious gotchas: what fails silently, what the obvious approach gets wrong, ordering constraints, destructive steps. Put each next to the step it guards.
- Worked examples that show a whole task end to end; one good example beats three variants.
- The facts the evals assert. Check every assertion against the new text before finishing.

## Structure

- Hub: a one-paragraph purpose, `When to use`, a numbered core workflow for the common task, the handful of rules that apply everywhere, then a routing table with one row per reference in the user's words plus a "load when ..." condition. Details live in references, not the hub.
- References grouped by what the reader is doing (`setup`, `tuning`, `troubleshooting`), never one per source page. Merge pages that answer the same question. Open each with one line saying when to read it.
- Description: what the skill covers, concrete triggers ("Use when ..."), what it does not cover. Third person, at most 1024 characters, no source names.
- Voice: imperative and specific ("Set `max_connections` below 200 unless a pooler runs"). One term per concept. No filler, hedging, praise or apologies. Reserve ALL CAPS for invariants that break things.
- Match specificity to fragility: exact steps where a slip is costly, a short principle where several approaches work.

## Grounding

Compaction removes markers, so `compact-verify` checks the corpus directly:

- Every fenced code block must be found in the corpus, either whole or line by line (trimmed or spliced from several source blocks). Comment lines and lines with no letters are exempt; a block of only comments is not.
- A block you must write yourself (a glue snippet, a sketch) takes the word `authored` in its fence info (```` ```bash authored ````). It may use only commands, flags and APIs that appear in the corpus. At most 5 per skill; each draws a warning.
- Prose is not sourced any more: state only what the corpus supports, and drop a claim you cannot trace to it. `--laya` lists sentences no corpus passage supports; treat each as a claim to fix or cut.
- Never invent numbers, versions, flags or paths.

## Evals

The evals are how you prove nothing useful was lost, so they are frozen: the same set grades the no-skill, full and compact runs.

- `compact-brief` (or `evals-freeze`) freezes the full skill's `evals/evals.json` into `<ws>/evals.frozen.json` and copies it verbatim into `compact/evals/`. The compactor never edits evals: not a prompt, not an id, not one assertion, and adds or drops none.
- The same command writes `<ws>/eval-prompts.json`: ids and prompts only. Eval executors (all three configs) receive that file and their skill directory copied without `evals/`; only graders see `evals.frozen.json`. An executor that can read the assertions is teaching to the test.
- `compact-verify` hard-fails on any id, prompt or assertion that differs from the frozen set, and on any assertion that mentions a file, a path or a file read. Those grade the process, which a run without the skill fails for free.
- If the evals are weak (no-skill pass rate above 0.8, or file-read assertions), that is fixed before compaction, in the full skill: replace the easy evals with ones on source-specific knowledge, then `evals-freeze --force`. Never during the rewrite.
- Keep every fact the evals assert. Check each assertion against the new text before finishing.

## Gate

`a2s.py compact-gate --none X --full Y --compact Z [--lost 'assertion' ...]` encodes the rule and records it in `<ws>/compact-gate.json`. Accept only if `compact >= full - 0.05` and `compact - none >= 0.1`. If `none` is above 0.8 it prints `strengthen-evals` instead: fix the evals in the full skill first. Whatever the decision, report the lost assertions (passed by full, failed by compact) and the token savings.

## Retry

If the gate fails, read the failing assertions and restore the missing fact in the place the routing table sends the reader. Never edit an eval or an assertion to make it pass. One retry, then keep the full skill.
