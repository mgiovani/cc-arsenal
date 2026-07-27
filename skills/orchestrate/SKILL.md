---
name: orchestrate
description: Turn any task into a model-tiered multi-agent plan, decompose it into
  subtasks, classify each as research, implementation, planning, or synthesis, map every
  subtask to the right subagent and model (haiku for research/exploration, opus for
  planning, sonnet for everything else), then run independent tracks in parallel under
  strict one-owner-per-file discipline before synthesizing the result yourself. Use for
  "act as orchestrator", "spawn subagents for this", "delegate this with the right
  models", "run this in parallel", or any task large enough to fan out across multiple
  independent workstreams. Not for a single well-scoped feature with a known shape (use
  implement-feature), not for the full spec-driven agent-teams flow with cross-agent
  messaging (use team-implement), and not for pure task breakdown with no execution (use
  project-planner).
disable-model-invocation: false
argument-hint: "<task_description>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# Orchestrate

Turn a task into a model-tiered multi-agent plan, run it, and synthesize the result
yourself.

## Task

$ARGUMENTS

## Step 0: Is orchestration warranted?

Before decomposing anything, check: does this genuinely split into 2+ independent
pieces of real work? A task that touches one file, needs one command, or has one
obvious fix does NOT need a plan or a subagent: do it directly and say so in one line.
Spawning, tracking, and merging subagents costs more than the work itself below that
bar, and a fabricated multi-phase plan for a one-line change is worse than no plan.

If it passes this bar, continue to Step 1.

## Step 1: Decompose

Break the task into subtasks. For each, state its concrete input, its expected output,
and classify it as one of:

- **research**: exploration, search, reading, gathering information; no code written
- **implementation**: writing or editing code, config, or content
- **planning**: architecture/design decisions, non-trivial trade-off calls
- **synthesis**: merging multiple subagents' outputs into one final deliverable

## Step 2: Model table (`model` is required, never inherited)

| Classification | subagent_type | model | Why |
|---|---|---|---|
| research | Explore | haiku | cheap, good at search/read |
| planning | Plan | opus | best reasoning for architecture/trade-offs |
| implementation | general-purpose (or the repo's own agent) | sonnet | balance of cost and capability |
| synthesis | n/a (orchestrator itself) | n/a | never delegate the final merge |

Every spawn call MUST set `model` explicitly. An unset `model` silently inherits the
caller (often the most expensive model available) and defeats the whole point of
tiering. Treat a missing `model` field as an incomplete call, not a default to fill in
later.

## Step 3: Parallelize with strict file ownership

Group subtasks into independent tracks: a track is independent if it shares no file or
directory with any other track. Before spawning, write down the ownership map (track →
files/dirs it will touch) and confirm no two tracks overlap. Two agents editing the same
file is a merge conflict you caused, not one you'll resolve later: split the map
instead of hoping it works out.

Spawn every independent track's subagent(s) in parallel: multiple `Task` calls in the
same turn. Sequential subtasks (B depends on A's output) run one after another in the
same session, passing A's actual output forward, never a paraphrase of it.

## Step 4: Orchestrator does the synthesis and the git

Once every track reports back:

1. Review each subagent's actual diff or output: don't take a subagent's self-report
   on faith.
2. Merge/synthesize the final deliverable yourself. Never spawn a subagent to do the
   final merge.
3. If the task touched code, run the project's real verification commands (test/lint/
   build): discover them from the repo, don't assume `npm test` or `make test` exist.
4. Any git operation (commit, push) is the orchestrator's job alone: no subagent
   commits.

## Portability: no Task/subagent tool available

Run the exact same Step 1-4 structure yourself, inline, sequentially, in dependency
order: research tracks first, then planning, then implementation, then your own
synthesis. Nothing about the plan's correctness depends on subagents existing; they're
a speed optimization, not a requirement.

## Worked examples

### Research sweep (independent, parallel research tracks)

Task: "Research current pricing for 4 competitors, write a comparison table."
- 4 research subtasks (one per competitor), each `Explore`/`haiku`, no shared file:
  spawn all 4 in the same turn.
- Orchestrator synthesizes the 4 reports into the comparison table itself.

### Codebase-wide refactor (independent, parallel implementation tracks)

Task: "Rename `Invoice` to `Bill` across models/, api/, tests/, docs/."
- One research subtask first (`Explore`/`haiku`): grep every reference, return the
  full list.
- 4 implementation subtasks, one per directory, each `general-purpose`/`sonnet`,
  ownership map = `{models/, api/, tests/, docs/}` with zero overlap.
- Orchestrator runs the test suite, reviews all 4 diffs, commits once, alone.

### Mixed build (research → plan → parallel implementation → synthesis)

Task: "Add a new payment provider integration."
- 1 research subtask (`Explore`/`haiku`): find the existing provider abstraction and
  its test patterns.
- 1 planning subtask (`Plan`/`opus`): design the new provider's interface against what
  research found.
- 2-3 parallel implementation subtasks (`sonnet`) against the approved plan, one per
  component (client, tests, config), each with a distinct file scope.
- Orchestrator integrates, verifies, commits.

## Output format

Report the subtask list with each classification and model, the parallel groupings
actually run, and the synthesized result. If Step 0 concluded orchestration wasn't
warranted, say so in one line and do the work directly instead: no plan needed for
that case.

## Usage

```
/orchestrate Research current pricing for 4 payment competitors and write a comparison table
/orchestrate Rename the Invoice model to Bill everywhere in the codebase
/orchestrate Add support for a new payment provider (client + tests + config)
```
