# Task Management Best Practices

This guide covers when and how to use Claude Code's Task Management System effectively during feature implementation.

## When to Use Tasks

### ✅ Use Tasks For:

- **Complex multi-step implementations** (3+ phases)
  - Feature development requiring discovery, research, planning, implementation, verification
  - Work that spans multiple sessions
  - Projects with parallel subagent orchestration

- **Work with dependencies**
  - Sequential phases where one must complete before the next starts
  - Parallel tasks that converge at verification
  - Mixed parallel/sequential workflows

- **Progress tracking needs**
  - Stakeholder visibility into implementation status
  - Resuming work across sessions
  - Multiple subagents working concurrently

### ❌ Skip Tasks For:

- **Simple changes** (1-2 files, <30 minutes)
  - Quick bug fixes
  - Typo corrections
  - Single-file refactorings
  - Documentation-only updates

- **Trivial implementations**
  - Adding a single function
  - Updating a constant
  - Simple configuration changes

## Task Granularity Guidelines

### Phase-Level Tasks (Recommended)

Create one task per major phase:
- Phase 0: Project Discovery
- Phase 1: Research & Best Practices
- Phase 2: Planning
- Phase 3: Implementation
- Phase 4: Verification
- Phase 5: Final Commit

**Benefits:**
- Clear progress tracking
- Manageable task list
- Easy to understand dependencies

### Component-Level Tasks (Optional)

For complex implementations, create child tasks for parallel work:
```
Phase 3: Implementation (parent task)
  ├── Implement API endpoint (child task)
  ├── Implement UI component (child task)
  └── Write integration tests (child task)
```

**When to use:**
- Multiple independent subagents
- Need to track parallel work separately
- Complex features with >3 major components

### Avoid Over-Granularization

❌ **Don't create tasks for:**
- Individual file edits
- Single function implementations
- Trivial steps (e.g., "Read CLAUDE.md", "Run tests")

✅ **Do create tasks for:**
- Complete phases with multiple steps
- Significant components requiring subagents
- Major milestones requiring approval gates

## Dependency Patterns

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

**Use when:**
- Standard feature implementation workflow
- Each phase requires outputs from the previous phase
- Linear progression with approval gates

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

**Use when:**
- Multiple independent components
- Parallel subagent work
- Components can be built simultaneously

### Diamond Pattern

Parallel middle phases with shared prerequisites and convergence:
```
Task 1: Prerequisites (pending)
Task 2a: Component A (blockedBy: [1])
Task 2b: Component B (blockedBy: [1])
Task 3: Integration (blockedBy: [2a, 2b])
```

**Use when:**
- Shared setup phase required
- Multiple parallel implementations
- Final integration step needed

## Handling Task Failures

### Test Failures During Implementation

If a subagent reports test failures:

1. **Don't mark task as completed**
   ```
   # Task remains in_progress
   TaskUpdate: { taskId: "4a", status: "in_progress" }
   ```

2. **Create a blocker task if needed**
   ```
   TaskCreate:
     subject: "Fix failing tests in component A"
     description: "3 unit tests failing due to validation logic"
     activeForm: "Fixing failing tests"

   TaskUpdate: { taskId: "4a", addBlockedBy: ["blocker-task-id"] }
   ```

3. **Only mark completed when all tests pass**

### Blocked by External Factors

If implementation blocked by external dependency:

```
TaskUpdate:
  taskId: "4"
  status: "in_progress"
  metadata: { blocked_reason: "Waiting for API key from stakeholder" }
```

Use `AskUserQuestion` to notify user and get resolution.

### Changing Requirements Mid-Implementation

If user changes requirements during implementation:

1. **Update task descriptions**
   ```
   TaskUpdate:
     taskId: "4"
     description: "Updated: Now includes OAuth integration instead of JWT"
   ```

2. **Add new tasks if scope grows significantly**
   ```
   TaskCreate:
     subject: "Implement OAuth provider integration"
     description: "New requirement: Google OAuth support"
     activeForm: "Implementing OAuth integration"

   TaskUpdate: { taskId: "5", addBlockedBy: ["new-oauth-task"] }
   ```

## Resuming Sessions with Existing Tasks

When resuming work on a feature with existing tasks:

1. **Check task status**
   ```
   TaskList  # View all tasks and their status
   ```

2. **Identify next unblocked task**
   - Look for tasks with `status: "pending"` and `blockedBy: []`
   - These are ready to start

3. **Resume work**
   ```
   TaskUpdate: { taskId: "next-task-id", status: "in_progress" }
   ```

4. **Review completed work**
   - Use `TaskGet` to see full descriptions of completed tasks
   - Check metadata for subagent results or notes

## Progress Visualization Patterns

### After Each Phase

Show progress with TaskList:
```
TaskList  # Shows all tasks with status and dependencies
```

Example output:
```
✓ Task 1: Discovery (completed)
✓ Task 2: Research (completed)
✓ Task 3: Planning (completed)
→ Task 4: Implementation (in_progress)
  Task 5: Verification (blocked by Task 4)
  Task 6: Commit (blocked by Task 5)
```

### During Parallel Subagent Work

Track individual subagent progress:
```
TaskList  # Shows all child tasks under Phase 3
```

Example output:
```
✓ Task 4a: Implement API (completed)
→ Task 4b: Implement UI (in_progress)
  Task 4c: Write Tests (pending, blocked by 4b)
```

## Task Metadata Patterns

Use metadata to enrich tasks with context:

```
TaskCreate:
  subject: "Implement payment processing"
  description: "Stripe integration with webhook handling"
  activeForm: "Implementing payment processing"
  metadata:
    component: "backend"
    subagent: "api-agent"
    estimated_files: ["api/stripe.ts", "webhooks/stripe.ts"]
    libraries: ["stripe", "@stripe/stripe-js"]
```

**Useful metadata fields:**
- `component`: Which part of the system (e.g., "backend", "frontend", "database")
- `subagent`: Which subagent owns this task
- `parent`: Parent task ID for child tasks
- `estimated_files`: Files expected to change
- `libraries`: External dependencies used
- `blocked_reason`: Why task is blocked (for external blockers)

## Common Antipatterns

### ❌ Too Many Tasks

```
Task 1: Read CLAUDE.md
Task 2: Find test command
Task 3: Find lint command
Task 4: Research best practices
Task 5: Search for similar code
...
```

**Why bad:** Overhead exceeds benefit, too granular

**Better:**
```
Task 1: Project Discovery (includes reading CLAUDE.md, finding commands)
Task 2: Research (includes best practices, similar code, Context7)
```

### ❌ No Dependencies

```
Task 1: Discovery (pending)
Task 2: Research (pending)
Task 3: Planning (pending)
Task 4: Implementation (pending)
```

**Why bad:** No enforcement of workflow order, can implement before planning

**Better:**
```
Task 1: Discovery (pending)
Task 2: Research (blockedBy: [1])
Task 3: Planning (blockedBy: [2])
Task 4: Implementation (blockedBy: [3])
```

### ❌ Completing Tasks Prematurely

```
# Tests still failing but marking completed
TaskUpdate: { taskId: "4", status: "completed" }
```

**Why bad:** Misleading progress, breaks trust in task system

**Better:**
```
# Keep in_progress until ALL quality gates pass
# Only mark completed when tests pass, linting passes, etc.
```

### ❌ Not Using TaskList

Forgetting to show progress to user after completing phases.

**Better:**
```
TaskUpdate: { taskId: "1", status: "completed" }
TaskList  # Show updated progress
```

## Task Management Checklist

At the start of implementation:
- [ ] Create all phase tasks upfront
- [ ] Set up dependency chain with `addBlockedBy`
- [ ] Mark first task as `in_progress`

During each phase:
- [ ] Update task to `in_progress` when starting
- [ ] Create child tasks for parallel subagent work (optional)
- [ ] Track subagent progress with task updates
- [ ] Only mark `completed` when all quality gates pass
- [ ] Run `TaskList` to show progress after completing each phase

When blocked:
- [ ] Keep task as `in_progress` (don't mark completed)
- [ ] Add metadata explaining blocker
- [ ] Use `AskUserQuestion` if user action needed
- [ ] Create blocker tasks if substantial work needed to unblock

Across sessions:
- [ ] Use `TaskList` to resume context
- [ ] Use `TaskGet` to read full task details
- [ ] Review completed task metadata for previous work results
