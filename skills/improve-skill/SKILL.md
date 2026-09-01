---
name: improve-skill
description: >-
  Improve one or more EXISTING agent skills to the current authoring standard,
  with measured before/after evidence instead of a trust-me rewrite. Snapshots
  the current version to an immutable baseline, rewrites description/body/references
  against the rubric, authors or upgrades evals/evals.json and trigger-eval.json
  in the same pass, then benchmarks the rewrite against the frozen baseline with
  deterministic grading before calling it done. Use when the user wants to improve,
  audit, refresh, modernize, tighten, or benchmark a skill that already exists:
  "make this skill better", "this skill's description never triggers right",
  "audit my skills", "is the new version of X actually better", "clean up this
  SKILL.md". Not for creating a brand-new skill from scratch (use create-skill)
  or discovering/installing third-party skills (use find-skills).
metadata:
  author: mgiovani
  version: 1.0.0
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(mkdir *), Bash(cp *), Bash(diff *), Bash(uv run *), Task, AskUserQuestion
---

# Improve Skill

Take a skill that already exists and bring it up to the current authoring standard: with a frozen baseline and a measured comparison, not just a confident rewrite. Every claim of "better" in your final report must trace to a validator run or a grading result you actually produced this session.

## Ground rules

- **Snapshot before you touch anything, and never touch the snapshot again.** Once `skill-snapshot/` exists for a skill, it is read-only for the rest of the run: every later step (rewrite, iteration, feedback pass) reads it for comparison and never writes to it. If a later step wants to "fix" the baseline to make a comparison look better, that is overfitting to the eval, not improving the skill: refuse and explain why.
- **Never edit an eval's prompt or assertions to make a failing run pass.** If a rewritten skill fails an assertion, fix the skill (SKILL.md, references, description). If the assertion itself was wrong when it was written, say so explicitly and get the user's sign-off before changing it. Silently loosening an assertion after seeing it fail is the one move that makes every later benchmark meaningless.
- **Judgment, not rewrite-for-rewrite's-sake.** A skill that's already close to the rubric gets a small diff, not a fresh draft. Read it fully before deciding what's actually deficient: most of the value here is in the delta, not the word count changed.
- **This skill never commits, pushes, or force-updates anything.** Its output is a modified skill directory plus a benchmark report. When the user is ready to save the change, they invoke `git-commit` or `ship` separately: do not run `git commit` yourself even if the user says "looks good, ship it," because that phrase in this context is about the skill quality, not a request to commit.

## Workflow

### 1. Scope

Identify which skill(s) to improve: a name the user gave, a path, or "audit all skills" (if a repo-wide audit workflow already exists here, e.g. `.claude/workflows/arsenal-audit.js`, its per-skill findings are a good prioritized starting list; don't re-derive that scoring yourself, just read its output). For each target, confirm `skills/<name>/SKILL.md` exists: if it doesn't, stop and say so; this skill only improves skills that already exist (a brand-new skill is `create-skill`'s job).

### 2. Snapshot

Pick a workspace root: reuse an existing scratch/eval convention in the repo if one exists (e.g. `ignored/eval-workspace/`), otherwise create `.improve-skill-workspace/` at the repo root. For each target skill:

```bash
mkdir -p <workspace>/<name>/skill-snapshot
cp -R skills/<name>/. <workspace>/<name>/skill-snapshot/
```

Verify the copy landed (`diff -rq skills/<name> <workspace>/<name>/skill-snapshot` should report no differences) before moving on. This is the only write this skill ever makes to `skill-snapshot/`: see Ground rules.

### 3. Rewrite

Read the full current `SKILL.md` plus every file it references. Rewrite against the rubric in [references/rubric.md](references/rubric.md), load it now:

- Description: use-case-first, third person, WHAT + WHEN, trigger phrases, one "Not for X (use sibling)" clause per real overlap, ≤1024 chars.
- Body: <500 lines, lean imperative, WHY only at hard boundaries, CAPS reserved for true invariants. Heavy detail moves to `references/<topic>.md` behind an inline link and a one-line "load when..." condition. 3-5 worked examples only where output format matters, plus an anti-hallucination floor. The core stays tool-neutral, with any subagent/orchestration mechanics called out as an enhancement carrying an explicit sequential fallback.
- If the skill mutates user state (installs, file edits, history rewrite, deploys), it must stop and ask before any destructive/irreversible step: the request that triggered the skill is not itself the confirmation.

**In the same pass**, author or upgrade `evals/evals.json` and `evals/trigger-eval.json` per [references/eval-design.md](references/eval-design.md), load it now. Evals encode the intended post-rewrite behavior; writing them after the fact, once you already know what the rewrite does, produces evals that only confirm what you built instead of testing it.

**Restraint gate: decide per dimension before editing.** Go through the rubric dimensions (description, body length/tone, references split, CAPS discipline, examples, portability, anti-hallucination) and mark each `compliant` or `deficient` from your full read. You may only rewrite the `deficient` ones. A dimension you judged `compliant` stays byte-for-byte unless fixing a `deficient` one forces a change through it: do not reword prose, add new sections, or expand the body on a dimension you already called compliant. If your rewrite grows the line count while your own analysis said the skill was already close, that is the over-rewrite failure this skill exists to avoid: stop and cut back to the actual delta. Report the compliant/deficient verdict per dimension and the specific gaps you closed: a near-compliant skill should show a small diff, not a fresh draft.

### 4. Validate

```bash
uv run skills/create-skill/scripts/quick_validate.py skills/<name>
```

Fix every error before continuing. This is create-skill's validator, reused as-is: don't fork or reimplement it here.

### 5. Benchmark

Run the evals from `evals/evals.json` against both configurations and compare: this is what turns "I rewrote it" into "here's the evidence it's better":

- **`new_skill`**: the rewritten skill in `skills/<name>/`.
- **`old_skill`**: the frozen copy in `<workspace>/<name>/skill-snapshot/`.

Grade each eval's assertions per-config, deterministically: read the actual output/transcript/file state, never take a run's self-report on faith. Record results as `grading.json` per eval per [references/eval-design.md](references/eval-design.md), including the required `summary` block.

**No subagent/parallel-task tool available**: skip the old-vs-new comparison, running two full sandboxed configurations sequentially for every eval isn't worth the wall-clock cost. Instead run each `evals/evals.json` prompt once, inline, against the rewritten skill only, grade its assertions yourself, and say plainly in the report that this was a single-configuration check, not a baseline comparison, and why (no comparison tooling in this environment).

### 6. Scan for missing runs

Before aggregating scored results, confirm every `(eval, config)` pair actually produced a `grading.json`: a small fraction of sandboxed runs silently write nothing. Re-run just the missing ones rather than treating an absent result as a 0.

### 7. Aggregate and report

Summarize per skill: validator status, per-eval pass/fail for both configs (or the single config in fallback mode), and a one-line verdict per eval (`new_skill` better / `old_skill` better / equivalent). Every number in this report must come from a validator run or a grading result produced this session: never estimate or round up "probably passes."

### 8. Iterate from feedback

If the user gives feedback after reviewing the report, generalize the underlying pattern rather than patching the one failing case: a fix that only works for the exact prompt that failed isn't a real fix (see `references/rubric.md`'s "generalize, don't overfit" note). Cap iteration at 2 rounds per skill (3 for a skill the user flags as still weak after round 2); after the cap, hand back to the user rather than looping indefinitely. Every iteration still obeys the Ground rules above: snapshot stays frozen, eval prompts/assertions stay frozen unless the user explicitly signs off on changing one because it was wrong.

## Anti-hallucination

- Every pass/fail, score, or "better than baseline" claim in the report must come from a validator invocation or a grading pass you actually ran this session: never infer a result from how a similar skill behaved before.
- Never invent file paths, tool names, or sibling-skill descriptions when writing the "Not for X" disambiguation clause: read the sibling's actual frontmatter description first.
- If `quick_validate.py` reports a warning you don't understand (e.g. an unfamiliar frontmatter key), read what the key means before deciding whether to keep or remove it: don't guess.

## Reference files

- [references/rubric.md](references/rubric.md): the full authoring rubric (description shape, body constraints, portability, anti-hallucination floor). Load in step 3, every rewrite.
- [references/eval-design.md](references/eval-design.md): eval-authoring rules, the `grading.json` schema with the required `summary` block, and the anti-overfit invariants. Load in steps 3 and 5.
- [references/orchestration.md](references/orchestration.md): Claude-Code-only enhancement, running steps 2-6 as parallel subagents across a batch of skills with per-stage model tiers and strict per-skill directory ownership. Load only when improving more than one skill at once and a `Task` (or equivalent parallel subagent) tool is available; otherwise steps 2-7 above already describe the full sequential path.
