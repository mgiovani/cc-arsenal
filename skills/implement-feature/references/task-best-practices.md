# Task Dependency Patterns & Call Templates

Load this when SKILL.md's size threshold is crossed (4+ files, or 3+ phases tracked as
separately-blocked work). Covers the literal `TaskCreate`/`TaskUpdate` calls for the
6-phase chain, the parallel-subagent pattern, dependency-pattern diagrams, and common
antipatterns. For breaking down large, multi-track projects from scratch (not this
skill's per-feature chain), use the `project-planner` skill instead.

## The 6-Task Chain: Literal Calls

Create all six phase tasks up front, wire the sequential dependency chain, then mark
the first `in_progress`:

```
TaskCreate:
  subject: "Phase 0: Discover project workflow"
  description: "Identify test, lint, build, dev server commands from CLAUDE.md and task runners"
  activeForm: "Discovering project workflow"

TaskCreate:
  subject: "Phase 1: Research best practices"
  description: "Web search and Context7 research for [FEATURE]"
  activeForm: "Researching best practices"

TaskCreate:
  subject: "Phase 2: Create implementation plan"
  description: "Enter plan mode and get user approval"
  activeForm: "Creating implementation plan"

TaskCreate:
  subject: "Phase 3: Implement feature"
  description: "Execute implementation with parallel subagents"
  activeForm: "Implementing feature"

TaskCreate:
  subject: "Phase 4: Verify implementation"
  description: "Run full test suite, lint, type-check"
  activeForm: "Verifying implementation"

TaskCreate:
  subject: "Phase 5: Final commit"
  description: "Create conventional commit with summary"
  activeForm: "Creating final commit"

# Sequential chain
TaskUpdate: { taskId: "2", addBlockedBy: ["1"] }
TaskUpdate: { taskId: "3", addBlockedBy: ["2"] }
TaskUpdate: { taskId: "4", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "5", addBlockedBy: ["4"] }
TaskUpdate: { taskId: "6", addBlockedBy: ["5"] }

TaskUpdate: { taskId: "1", status: "in_progress" }
```

After finishing a phase: `TaskUpdate: { taskId: "N", status: "completed" }` then
`TaskList` to confirm the next task unblocked.

## Parallel Child Tasks (Phase 3)

When Phase 3 has independent components (e.g. API + UI + tests), create child tasks
blocked only by the planning phase, and block Phase 4 on all of them:

```
TaskCreate:
  subject: "Implement API endpoint"
  description: "Create /api/feature endpoint with validation"
  activeForm: "Implementing API endpoint"
  metadata: { parent: "4", component: "api" }

TaskCreate:
  subject: "Implement UI component"
  description: "Create FeatureComponent.tsx with tests"
  activeForm: "Implementing UI component"
  metadata: { parent: "4", component: "ui" }

TaskCreate:
  subject: "Write integration tests"
  description: "E2E tests for feature flow"
  activeForm: "Writing integration tests"
  metadata: { parent: "4", component: "tests" }

TaskUpdate: { taskId: "api-task", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "ui-task", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "test-task", addBlockedBy: ["3"] }

# Phase 4 (Verification) blocked by ALL parallel tasks
TaskUpdate: { taskId: "5", addBlockedBy: ["api-task", "ui-task", "test-task"] }
```

## Subagent Instructions Template

Use this for each Phase 3 subagent (`Task` tool, `subagent_type: "general-purpose"`,
`model: "sonnet"` — required, never leave unset):

```
Implement [specific task description].

First, read the project's CLAUDE.md to understand conventions and patterns.
Then trace the real flow of the code you're about to touch, end to end —
a diff written without understanding the existing flow is a liability, not lean.

Apply the Lean Code rules from SKILL.md (search before writing, no speculative
abstractions, fix shared bugs once, never cut the never-negligent floor, use
`LEAN-DEBT:` markers for deliberate shortcuts). In addition, for this task:
1. Follow existing codebase patterns and conventions.
2. If the leanest correct solution differs from what was asked, implement what
   was asked but flag the leaner alternative in your report — do not silently
   substitute your own approach.
3. Write comprehensive tests (unit + integration where applicable). All tests
   MUST pass before completion.
4. Add necessary type definitions (if typed language).

Project-specific commands (discovered in Phase 0):
- Test command: [INSERT DISCOVERED TEST COMMAND]
- Lint command: [INSERT DISCOVERED LINT COMMAND]

After implementation:
1. Run the test suite to verify all tests pass.
2. Run linting to ensure code quality.
3. Report back what was implemented, any LEAN-DEBT markers left, and any leaner
   alternative you flagged (do NOT commit — the main agent handles commits).

If tests fail, fix them before reporting completion. If requirements are
ambiguous, report back and ask for clarification instead of guessing.
```

## Dependency Pattern Diagrams

### Sequential Chain (Most Common)

Every phase depends on the previous one:
```
Task 1: Discovery (pending)
Task 2: Research (blockedBy: [1])
Task 3: Planning (blockedBy: [2])
Task 4: Implementation (blockedBy: [3])
Task 5: Verification (blockedBy: [4])
Task 6: Commit (blockedBy: [5])
```
Use for the standard feature workflow, where each phase needs the previous phase's output.

### Parallel with Convergence

Multiple independent tasks converging at verification:
```
Task 1-3: Discovery, Research, Planning (sequential)
Task 4a: Implement API (blockedBy: [3])
Task 4b: Implement UI (blockedBy: [3])
Task 4c: Write Tests (blockedBy: [3])
Task 5: Verification (blockedBy: [4a, 4b, 4c])
Task 6: Commit (blockedBy: [5])
```
Use when independent components can be built simultaneously by separate subagents.

### Diamond Pattern

Parallel middle phases with shared prerequisites and convergence:
```
Task 1: Prerequisites (pending)
Task 2a: Component A (blockedBy: [1])
Task 2b: Component B (blockedBy: [1])
Task 3: Integration (blockedBy: [2a, 2b])
```
Use when a shared setup phase feeds multiple parallel implementations that need a final integration step.

## Common Antipatterns

| Antipattern | Why it's bad | Do instead |
|---|---|---|
| Creating tasks below the size threshold | Overhead exceeds benefit for a 2-3 file change | Skip task creation entirely; run phases sequentially |
| Too many tasks (one per file read, per command lookup) | Overhead exceeds benefit | One task per phase (e.g. "Project Discovery" covers reading CLAUDE.md + finding commands) |
| No dependencies between tasks | Nothing enforces workflow order — implementation can start before planning | Chain phases with `addBlockedBy` |
| Marking a task completed while its tests still fail | Misleading progress, breaks trust in the task system | Keep `in_progress` until all quality gates pass |
| Forgetting to run `TaskList` after completing a phase | User loses visibility into progress | Run `TaskList` after every `TaskUpdate` to `completed` |
