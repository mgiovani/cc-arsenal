---
name: implement-feature
description: Implements a new feature end-to-end as a senior staff engineer would,
  discovers project conventions, researches current best practices, drafts a plan for
  approval, then builds it (with parallel subagents where available) reusing existing
  code, skipping speculative abstractions, and verifying with tests before completion.
  Use when the user wants to implement, build, add, or ship new functionality (a
  feature, endpoint, component, module, or integration). Not for fixing an existing bug
  (use fix-bug), restructuring code that already works with no new behavior (use
  refactor), or a large multi-service build that explicitly needs a full adaptive team
  of 3-11 agents (use team-implement).
disable-model-invocation: false
argument-hint: "<feature_description>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, EnterPlanMode, AskUserQuestion, ExitPlanMode
---

# Feature Implementation

Implement a new feature as a **Senior Staff Engineer** would (SOLID, DRY, YAGNI) to
produce a secure, fast, reliable change.

This skill produces exactly one of two outputs: an implemented feature (Phases 0-6
below), or (when the Ambiguity Gate at the start of Phase 0 fails) 2-3 clarifying
questions and nothing else. Never both in the same turn.

## Feature to Implement

$ARGUMENTS

## Anti-Hallucination Guidelines

Before implementing anything:
1. Discover project commands first: do not assume `bun`, `npm`, `make`, etc. exist.
2. Read CLAUDE.md: every project has different conventions.
3. Verify tools exist: check for `Makefile`, `justfile`, `package.json`, `pyproject.toml`.
4. Never guess the test command: find the one this project actually uses.
5. Any number reported at the end (files changed, tests added, pass count) must come
   from a command actually run in this session: never state a count or percentage
   you didn't verify by running something.

## Lean Code

Write the smallest change that fully does the job, and that the next person can change without fear. Two goals at once: minimal footprint, easy to change.

**Before you add code**
- **Does it already exist?** Search this codebase, the standard library, the framework, and installed dependencies before writing anything new. Reuse beats reimplementation.
- **Does it need to exist?** Build only what a current, concrete requirement needs: no speculative flags, options, or extension points for a future that may never come.
- **Is the abstraction earning its keep?** No interface with a single implementation, no factory for one product, no wrapper that only forwards. Add indirection when a second caller actually appears.

**While you write it**
- **Change it in one place.** Put logic where a future change touches one spot: fix the shared function once instead of guarding every caller.
- **Smallest correct surface.** Prefer the change that reuses or deletes code over the one that adds it. Fewer files, shorter diff, as long as it stays complete.
- **Read before you change.** Trace the real flow of the code you touch, end to end, first. A tiny diff written without understanding is a liability, not lean.

**The line you never cross: lean, never negligent**
"Only what the task needs" is about scope, not corner-cutting. Input/trust-boundary validation, error and data-loss handling, security, and accessibility are always in scope, however small the change. A version that drops one of these isn't leaner: it's unfinished.

**When you deliberately simplify**
Leave an auditable trail instead of a silent gap:
`// LEAN-DEBT: <the limitation>. Upgrade when <the trigger>.`
e.g. `// LEAN-DEBT: in-memory rate limit, single instance only. Upgrade to Redis when we run >1 replica.`
A marker is for a shortcut chosen on purpose: never a license to skip the never-negligent line above.

## Verification Gates

Before marking an implementation complete, run the project's real commands (discovered in Phase 0) and require all of them to pass:
1. **Test suite**: e.g. `make test`, `npm test`, `pytest`.
2. **Lint**: e.g. `make lint`, `npm run lint`, `ruff check`.
3. **Type check / build**: if the project has one.

Any check fails → keep working, do not mark complete. Command not found → go back to Phase 0 discovery, don't guess one.

## Task Tracking: Opt-In, Not Default

Create Task-system entries (`TaskCreate`/`TaskUpdate`) **only** when the feature crosses
one of these:
- touches **4+ files**, or
- needs **3+ of the phases below tracked as separately-blocked work** (e.g. genuine parallel subagent workstreams).

Below that threshold (the common 3-5-file feature), run the phases in order below as
plain sequential work with **no** task-system calls at all. The phase structure is the
contract; the task ceremony is bookkeeping for when there's enough concurrent work to
need it.

When the threshold is crossed, see `references/task-best-practices.md` for the literal
6-task dependency chain (call templates, parallel child-task pattern, antipatterns to
avoid): set it up once at the start of Phase 0, then flip status at the start/end of
each phase.

**No `Task`/`TaskCreate` tools available?** Skip task tracking and subagent parallelism
regardless of size: work through every phase below yourself, sequentially, in order.
Nothing about the workflow's correctness depends on the task system; it only depends on
doing Discovery → Research → Plan → Implement → Verify → Commit in that order.

**Running in an eval or sandbox harness?** Never call the real session
`Task`/`TaskCreate`/`TaskUpdate`/`TaskList` tools there: those would mutate the
operator's actual task list. If the prompt asks you to record intended calls into a file
instead (e.g. `outputs/tasks.json`), write the full task chain there and treat that file
as the graded deliverable, rather than skipping ceremony or only narrating it in prose.

## Implementation Workflow

### Phase 0: Ambiguity Gate & Project Discovery (required)

**Step 0.0: Ambiguity gate. Check this before anything else, including task creation.**

Can you name the concrete behavior to build (what surface, what data, what constraints)
without inventing any load-bearing decision yourself? Missing small details (exact
copy, minor styling, file layout) doesn't fail this check; note the assumption and keep
going. Fails when the request leaves open multiple structurally different
implementations and picking one means guessing at a decision the user would want to
make themselves: e.g. "add support for team accounts" with no team size limit, billing
model, permission roles, or invitation flow specified.

If it fails: end your response with 2-3 concrete clarifying questions about the
ambiguous decision points (`AskUserQuestion` if available, else plain prose) and produce
nothing else: no task-system entries, no plan, no file created or modified, no command
run, no commit. Code built on a guessed requirement has to be audited line-by-line
against what the user actually meant, which costs more than asking first.

If it passes, continue to Step 0.1.

**Step 0.1: Discover project commands.**

Above the size threshold, create the 6-task chain now (see reference doc); mark this
phase `in_progress`.

Identify the project's real test, lint, type-check, build, and dev-server commands:
read CLAUDE.md, then check for `Makefile`, `justfile`, `package.json` scripts,
`pyproject.toml`. If a Task tool is available, delegate this to an Explore/`haiku`
subagent (cheap, token-efficient for a read-only lookup); otherwise read the files
yourself. Store whatever you find: every later phase uses these exact commands, never
assumed ones.

Above threshold: mark Phase 0 `completed`, run `TaskList` to confirm Phase 1 unblocked.

### Phase 1: Research & Discovery

Above threshold: mark this phase `in_progress`.

Before writing code: search the web for current best practices for the feature
(security considerations, common pitfalls, performance notes), check Context7 for any
library docs involved, and explore the codebase for similar existing implementations,
conventions, and test fixtures to match. If a Task tool is available, delegate this to
an Explore/`haiku` subagent; otherwise do it inline.

Above threshold: mark Phase 1 `completed`, run `TaskList`.

### Phase 2: Planning

1. **Enter Plan Mode** (`EnterPlanMode`).
2. **Plan contents**: break the feature into discrete pieces, note which can run in
   parallel, define interfaces between components, note security implications, plan
   test coverage. **Apply Lean Code to every proposed component**: state why it needs
   to exist (which concrete requirement drives it) and what it reuses instead of adding
   new code. A component that can't answer "why does this need to exist" gets cut from
   the plan before implementation starts.
3. **Get user approval**: exit plan mode only after the user approves.

Above threshold: mark Phase 2 `completed`, run `TaskList`.

### Phase 3: Implementation

Above threshold: mark this phase `in_progress`.

For up to ~3 parallel workstreams (e.g. API + UI + tests), spawn and track subagents
yourself using the call template in `references/task-best-practices.md`. If the plan
needs more fan-out than that (large multi-service features, many independent
components), delegate to the `team-implement` skill instead of re-deriving spawn/track/
merge logic here.

Give each subagent: the specific task, an instruction to read CLAUDE.md first and trace
the real flow of code it's about to touch, the Lean Code rules above, the discovered
test/lint commands, and an instruction to report back rather than commit.

**Model selection**: always set `model` explicitly, never leave it unset:
- `sonnet` for implementation, test writing, docs, architecture decisions.
- `haiku` only for exploration/research subagents.
- Never `opus` for subagent work: too expensive for this fan-out.

After each subagent completes: review its diff, mark its task `completed` (if
tracking), and commit its work via the `git-commit` skill (or a manual conventional
commit) before moving to the next.

Above threshold: mark Phase 3 `completed` once every child task is done, run
`TaskList` to confirm Phase 4 unblocked.

### Phase 4: Integration & Verification

Above threshold: mark this phase `in_progress`.

Run the Phase 0 discovered test, lint, and type-check/build commands. Fix every
failure before proceeding. Repeat until all pass. Never mark this phase complete with
a red check.

Above threshold: mark Phase 4 `completed`, run `TaskList`.

### Phase 5: Final Commit

Above threshold: mark this phase `in_progress`.

Only proceed once every check passes: review all changes, create a final integration
commit if needed (conventional commit format), summarize what was implemented.

Above threshold: mark Phase 5 `completed`, run `TaskList`: everything should show
completed.

### Phase 6: Manual Testing (optional, UI features only)

If the feature has a UI, use the `agent-browser` skill: start the dev server, open the
feature (`agent-browser open <url>`), take a snapshot (`agent-browser snapshot -i`),
interact via refs (`agent-browser click @e1`), capture a screenshot, then
`agent-browser close`.

Skip for backend-only changes, pure refactors, test-only changes, or CLI tools with no
UI.

## Subagent Quality Checklist

Each subagent's output should satisfy:
- [ ] All new code has tests, and all tests pass
- [ ] No lint errors, no type errors (if applicable)
- [ ] Code follows existing patterns
- [ ] Lean Code rules applied (reuse checked first, no unrequested abstractions,
      never-negligent floor intact, `LEAN-DEBT:` markers for deliberate shortcuts)

## Error Handling

If a subagent hits an issue: log it clearly, attempt a within-scope fix, and if it
can't be fixed report back with details. Never commit broken code.

## Handling Ambiguity After the Gate

The hard stop is Step 0.0 above: this section is for smaller ambiguity that surfaces
once the gate has already passed. Unclear secondary detail at any later phase (a design
choice with more than one valid answer, a missing preference): use `AskUserQuestion`,
present concrete options with trade-offs, and if there's no answer yet, state the
assumption you're proceeding with rather than blocking. Don't re-litigate the gate here:
if a later discovery reveals the core behavior was never actually pinned down, stop
and go back to asking, the same way Step 0.0 would have.

## Output Format

Summarize: features implemented, files created/modified, tests added, manual-testing
results (if performed), and any known limitations or follow-up items. Every number in
this summary must trace back to a command actually run this session (see
Anti-Hallucination Guidelines).

## Usage

```bash
# Implement a specific feature
/implement-feature Add user authentication with OAuth2

# Implement with more context
/implement-feature Create a REST API endpoint for managing user preferences with validation

# Implement a refactoring-shaped feature (new behavior, not pure restructuring)
/implement-feature Migrate the payment module to a strategy pattern to support a second provider
```

## Important Notes

- Always run Phase 0 first: never assume which tools are available.
- Each project has its own quality gates; use the ones Phase 0 actually found.
- Prefer smaller, logical commits over one big commit.
- Ask when unsure: clarifying is cheaper than guessing wrong.
