# Task Dependency Patterns

Reference diagrams for structuring the 6-phase task chain (and any child tasks)
described in SKILL.md's Task Management section. For breaking down large,
multi-track projects from scratch, use the `project-planner` skill instead —
this file only covers the patterns implement-feature itself needs.

## Sequential Chain (Most Common)

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

## Parallel with Convergence

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

## Diamond Pattern

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
| Too many tasks (one per file read, per command lookup) | Overhead exceeds benefit | One task per phase (e.g. "Project Discovery" covers reading CLAUDE.md + finding commands) |
| No dependencies between tasks | Nothing enforces workflow order — implementation can start before planning | Chain phases with `addBlockedBy` |
| Marking a task completed while its tests still fail | Misleading progress, breaks trust in the task system | Keep `in_progress` until all quality gates pass |
| Forgetting to run `TaskList` after completing a phase | User loses visibility into progress | Run `TaskList` after every `TaskUpdate` to `completed` |
