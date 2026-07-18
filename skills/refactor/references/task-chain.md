# Task Chain Templates

Load this when a refactoring actually needs the full Phase 0-6 task chain (see
"When to Use the Full Task Chain" in SKILL.md) — for skip-eligible refactors,
ignore this file entirely.

## Creating the Task Chain

`TaskCreate` returns the real ID of the task it just made — capture each one
and use the captured value in `addBlockedBy`. Never hardcode literal IDs like
`"1"`..`"6"`: other tasks may already exist in the session, so the IDs
TaskCreate hands back are not guaranteed to be sequential integers starting
at 1.

```
p0 = TaskCreate:
  subject: "Phase 0: Discover project workflow"
  description: "Identify test, lint, type-check commands from CLAUDE.md and task runners"
  activeForm: "Discovering project workflow"

p1 = TaskCreate:
  subject: "Phase 1: Analyze refactoring scope"
  description: "Map dependencies, callers, and test coverage for target code"
  activeForm: "Analyzing refactoring scope"

p2 = TaskCreate:
  subject: "Phase 2: Write characterization tests"
  description: "Ensure sufficient test coverage before making structural changes"
  activeForm: "Writing characterization tests"

p3 = TaskCreate:
  subject: "Phase 3: Incremental refactoring"
  description: "Apply refactoring in small verified steps"
  activeForm: "Refactoring incrementally"

p4 = TaskCreate:
  subject: "Phase 4: Final verification"
  description: "Run full test suite, lint, type-check — confirm behavior preserved"
  activeForm: "Verifying refactoring safety"

p5 = TaskCreate:
  subject: "Phase 5: Final commit"
  description: "Create conventional commit with refactoring summary"
  activeForm: "Creating final commit"

# Strict sequential chain, using the captured IDs above
TaskUpdate: { taskId: p1, addBlockedBy: [p0] }
TaskUpdate: { taskId: p2, addBlockedBy: [p1] }
TaskUpdate: { taskId: p3, addBlockedBy: [p2] }
TaskUpdate: { taskId: p4, addBlockedBy: [p3] }
TaskUpdate: { taskId: p5, addBlockedBy: [p4] }

TaskUpdate: { taskId: p0, status: "in_progress" }
```

After finishing each phase, mark its task `completed` and run `TaskList` to
confirm the next one unblocked — do this at the end of every phase.

## Phase 0: Discovery Agent Prompt

```
Use Task tool with Explore agent:
- prompt: "Discover the development workflow for this project:
    1. Read CLAUDE.md if it exists — extract testing and quality conventions
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test command (e.g., make test, just test, npm test, pytest, bun test)
    4. Identify how to run a single test file or specific test
    5. Identify the lint command (e.g., make lint, npm run lint, ruff check)
    6. Identify the type-check command if applicable (e.g., pyright, tsc, mypy)
    7. Note any pre-commit hooks or quality gates
    8. Check for code coverage tooling (e.g., pytest --cov, nyc, c8)
    Return a structured summary of all available commands."
- subagent_type: "Explore"
- model: "haiku"
```

Store the discovered commands — every later phase's test/lint/type-check runs
use them.

## Phase 1: Scope Analysis Agents

Run in parallel only when the refactoring spans multiple files or the caller
list isn't obvious from one grep — otherwise just grep it yourself.

```
Agent 1 — Dependency & Caller Analysis (Explore, Haiku):
  prompt: "Analyze dependencies and callers for the refactoring target:

    Refactoring target: [DESCRIBE TARGET CODE]

    1. Read the target code — understand its current structure and public API
    2. Find ALL callers and dependents using Grep:
       - Direct function/method calls
       - Import statements referencing the target
       - Type references (if applicable)
       - Configuration or dependency injection references
    3. Map the dependency graph: what the target depends on, what depends on
       it, and any circular dependencies
    4. Identify the public API surface: externally-called vs internal-only
    5. Note any dynamic references (string-based lookups, reflection, decorators)

    Return: complete caller list with file:line references, the dependency
    graph, public-vs-internal split, and risks (dynamic references, external
    consumers, serialization)."
  subagent_type: "Explore"
  model: "haiku"

Agent 2 — Test Coverage Analysis (Explore, Haiku):
  prompt: "Analyze test coverage for the refactoring target:

    Refactoring target: [DESCRIBE TARGET CODE]

    1. Find ALL test files that test the target code (unit, integration, e2e)
    2. For each test, note what behavior it verifies, which code paths it
       exercises, and which inputs/edge cases it covers
    3. Identify coverage gaps: untested functions/methods, unexercised
       branches (error paths, edge cases), public API without direct tests
    4. Note test patterns: fixtures/helpers available, mocking patterns,
       naming conventions

    Return: test files with what they cover, coverage gaps requiring
    characterization tests, reusable patterns/fixtures, and risk areas
    (untested paths refactoring could break)."
  subagent_type: "Explore"
  model: "haiku"
```

After both complete: mark which parts of the target are safe to refactor
(well-tested, internal-only) vs risky (untested, public API, dynamic
references), decide whether Phase 2 is needed, and order the incremental
steps in Phase 3 to touch the safe parts first.
