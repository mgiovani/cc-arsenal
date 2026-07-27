# Claude Code Enhancement: Parallel Batch Orchestration

This file only applies when improving more than one skill in the same run AND a `Task` (or equivalent parallel-subagent) tool is available. For a single skill, or for any environment without a subagent tool, `SKILL.md` steps 1-8 already describe the complete sequential path: nothing here is required to finish the job.

## When to use this

The user asks to improve/audit several skills at once (e.g. "improve all the skills flagged by the last audit," or a named list of 4+ skills). Running steps 2-6 sequentially per skill still works, it's just slower: this section describes running them in parallel without agents stepping on each other's files.

## Per-stage model tiers

Match this repo's existing subagent policy, don't invent a different tiering per skill:

| Stage | Model | Why |
|---|---|---|
| Snapshot + inventory (step 2) | haiku | Pure file copy + verification, no judgment needed |
| Rewrite (step 3) | sonnet | Needs to read the whole skill, apply the rubric, and write evals: real judgment |
| Benchmark executors (step 5, running eval prompts) | haiku | Executing a fixed prompt against a fixed skill config is cheap, deterministic work |
| Grading (step 5, scoring assertions) | sonnet | Judging whether an assertion actually held requires reading output, not just pattern-matching |
| Aggregation + report synthesis (step 7) | opus (or whatever model is driving this run) | Cross-skill synthesis and the final verdict table benefit from the strongest reasoning available |

`model` is a required field on every spawned agent: an unset model silently inherits the parent, defeating the tiering above.

## Strict per-skill directory ownership

When N skills are being improved in parallel, each skill's rewrite agent touches only `skills/<that-skill>/` and `<workspace>/<that-skill>/`: never another skill's directory, even to "just check" a sibling's description for the disambiguation clause. If a rewrite agent needs to read a sibling skill's frontmatter, it reads it; it never writes there. Two agents never share a path. This is what makes running them in parallel safe: no lock, no merge conflict, because there is nothing to conflict over.

## No git in agents

Sub-agents in this workflow never run `git`: not `git diff`, not `git stash`, not `git checkout`. Snapshotting uses plain file copy (`cp -R`, see `SKILL.md` step 2), not git machinery, specifically so parallel agents can't collide on the working tree's git state or accidentally stash/restore each other's in-flight edits. Any git operation (viewing history, eventually committing the result) stays with the orchestrator, and per the Ground rules in `SKILL.md`, this skill doesn't run commits at all: that's `git-commit`/`ship`'s job, invoked by the user afterward.

## Aggregating a batch report

One row per skill in the final report: validator status, per-eval verdicts (or single-config note in fallback mode), and iteration count so far. Sort by whatever the user cares about most (e.g. worst-scoring first if this followed an audit), but never omit a skill from the table because its result was uninteresting; a skill with zero findings still gets a row saying so.
