---
name: implement-feature
description: Implements a new feature end-to-end as a senior staff engineer would —
  discovers project conventions, researches current best practices, drafts a plan for
  approval, then builds it with parallel subagents that reuse existing code, skip
  speculative abstractions, and verify with tests before completion. Use when the user
  wants to implement, build, add, or ship new functionality (a feature, endpoint,
  component, module, or integration) — not for fixing an existing bug (use fix-bug) or
  restructuring code that already works (use refactor).
disable-model-invocation: false
argument-hint: "<feature_description>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, EnterPlanMode, AskUserQuestion, ExitPlanMode
---

# Feature Implementation

Implement a new feature as a **Senior Staff Engineer** following best practices (SOLID, DRY, YAGNI) to create a secure, fast, and reliable production application.

## Feature to Implement

$ARGUMENTS

## Anti-Hallucination Guidelines

**CRITICAL**: Before implementing anything:
1. **Discover project commands first** - Do NOT assume `bun`, `npm`, `make`, etc. exist
2. **Read CLAUDE.md** - Every project may have different conventions
3. **Verify tools exist** - Check for `Makefile`, `justfile`, `package.json`, `pyproject.toml`, etc.
4. **Never guess test commands** - Find the actual test runner used by this project

## Lean Code

Write the smallest change that fully does the job — and that the next person can change without fear. Two goals at once: minimal footprint, easy to change.

**Before you add code**
- **Does it already exist?** Search this codebase, the standard library, the framework, and installed dependencies before writing anything new. Reuse beats reimplementation.
- **Does it need to exist?** Build only what a current, concrete requirement needs — no speculative flags, options, or extension points for a future that may never come.
- **Is the abstraction earning its keep?** No interface with a single implementation, no factory for one product, no wrapper that only forwards. Add indirection when a second caller actually appears.

**While you write it**
- **Change it in one place.** Put logic where a future change touches one spot — fix the shared function once instead of guarding every caller.
- **Smallest correct surface.** Prefer the change that reuses or deletes code over the one that adds it. Fewer files, shorter diff — as long as it stays complete.
- **Read before you change.** Trace the real flow of the code you touch, end to end, first. A tiny diff written without understanding is a liability, not lean.

**The line you never cross — lean, never negligent**
"Only what the task needs" is about scope, not corner-cutting. Input/trust-boundary validation, error and data-loss handling, security, and accessibility are **always** in scope, however small the change. A version that drops one of these isn't leaner — it's unfinished.

**When you deliberately simplify**
Leave an auditable trail instead of a silent gap:
`// LEAN-DEBT: <the limitation>. Upgrade when <the trigger>.`
e.g. `// LEAN-DEBT: in-memory rate limit, single instance only. Upgrade to Redis when we run >1 replica.`
A marker is for a shortcut you chose on purpose — never a license to skip the never-negligent line above.

## Verification Gates

Before marking an implementation complete, run these verification steps:

### Completion Verification

**Verification Steps:**
1. **Test Suite**: Run the discovered test command from Phase 0 (e.g., `make test`, `npm test`, `pytest`). All tests must pass.
2. **Linting**: Run the discovered lint command from Phase 0 (e.g., `make lint`, `npm run lint`, `ruff check`). No lint errors.
3. **Type Checking**: If applicable, run the type-check or build command.

**Completion Criteria:**
- ✅ **All checks pass**: Implementation is complete
- ❌ **Any check fails**: Do not mark complete — keep working to fix the issues
- ℹ️ **Commands not found**: Discover them from CLAUDE.md or project files (Makefile/package.json/pyproject.toml)

**Example of an incomplete implementation:**
```
⚠️ Implementation verification failed:

Tests: ❌ FAILED (3 tests failing)
  - test_user_authentication: AssertionError
  - test_oauth_flow: Connection timeout
  - test_token_refresh: Invalid token

Lint: ✅ PASSED
Type Check: ✅ PASSED

🔧 Cannot complete implementation until all tests pass. Please fix the failing tests.
```

**Benefits:**
- Prevents marking features "complete" when tests are failing
- Catches regressions before moving on
- Enforces test-driven development discipline
- Ensures production-ready code quality

## Task Management

This skill uses Claude Code's Task Management System to track implementation progress with dependency-aware task tracking.

**When to Use Tasks:**
- Complex multi-step implementations (3+ phases)
- Features with parallel subagent work
- Work requiring progress tracking across sessions

**When to Skip Tasks:**
- Simple 1-2 file changes
- Trivial bug fixes
- Quick refactorings

**Task Structure:**
Each implementation creates tasks for all 6 phases with dependencies, tracking progress and blocking relationships. Tasks support parallel execution where independent work can proceed simultaneously.

## Implementation Workflow

**Task tracking replaces TodoWrite.** Create task structure at start, update as completing each phase.

### Phase 0: Project Discovery (REQUIRED)

**Step 0.1: Create Task Structure**

Before starting implementation, create the dependency-aware task structure:

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

# Set up dependencies (strict sequential chain)
TaskUpdate: { taskId: "2", addBlockedBy: ["1"] }  # Research after Discovery
TaskUpdate: { taskId: "3", addBlockedBy: ["2"] }  # Plan after Research
TaskUpdate: { taskId: "4", addBlockedBy: ["3"] }  # Implement after Plan
TaskUpdate: { taskId: "5", addBlockedBy: ["4"] }  # Verify after Implement
TaskUpdate: { taskId: "6", addBlockedBy: ["5"] }  # Commit after Verify

# Mark first task as in progress
TaskUpdate: { taskId: "1", status: "in_progress" }
```

**Step 0.2: Discover Project Workflow**

Use Haiku-powered Explore agent for token-efficient discovery:

```
Use Task tool with Explore agent:
- prompt: "Discover the development workflow for this project:
    1. Read CLAUDE.md if it exists - extract all development commands
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test command (e.g., make test, just test, npm test, pytest, bun test)
    4. Identify the lint command (e.g., make lint, npm run lint, ruff check)
    5. Identify the build/type-check command
    6. Identify the dev server command if applicable
    7. Note any pre-commit hooks or quality gates
    Return a structured summary of all available commands."
- subagent_type: "Explore"
- model: "haiku"  # Token-efficient for discovery
```

Store discovered commands for use in later phases. Example output:
```
Project Commands:
- Test: `make test` or `pytest`
- Lint: `make lint` or `ruff check`
- Type Check: `make type-check` or `pyright`
- Build: `make build` or `npm run build`
- Dev Server: `make dev` or `npm run dev`
- Quality: `make check` (runs all checks)
```

**Step 0.3: Complete Phase 0**

```
TaskUpdate: { taskId: "1", status: "completed" }
TaskList  # Check that Task 2 is now unblocked
```

### Phase 1: Research & Discovery

**Step 1.1: Start Phase 1**

```
TaskUpdate: { taskId: "2", status: "in_progress" }
```

**Step 1.2: Research Best Practices**

Before implementing, research best practices and understand the codebase context using Haiku-powered Explore agent:

```
Use Task tool with Explore agent:
- prompt: "Research and gather context for implementing [FEATURE]:

    1. **Best Practices Research**: Search the web for 'latest best practices' and 'current year best practices' related to [FEATURE]. Look for:
       - Current industry standards and patterns
       - Security considerations
       - Performance recommendations
       - Common pitfalls to avoid

    2. **Library Documentation** (if using external libraries/frameworks):
       - Use Context7 MCP to fetch up-to-date documentation
       - Validate API usage patterns against current docs
       - Check for deprecated methods or breaking changes

    3. **Codebase Exploration**:
       - Find similar existing implementations to reference
       - Identify coding patterns and conventions used
       - Locate test patterns and fixtures
       - Note file organization and naming conventions

    Return a comprehensive summary with:
    - Relevant best practices (with sources)
    - Library API patterns to follow (if applicable)
    - Specific file paths and existing patterns from the codebase"
- subagent_type: "Explore"
- model: "haiku"  # Token-efficient for research
```

**Step 1.3: Complete Phase 1**

```
TaskUpdate: { taskId: "2", status: "completed" }
TaskList  # Check that Task 3 is now unblocked
```

### Phase 2: Planning

**Step 2.1: Start Phase 2**

```
TaskUpdate: { taskId: "3", status: "in_progress" }
```

**Step 2.2: Create Implementation Plan**

1. **Enter Plan Mode**: Use `EnterPlanMode` to create a detailed implementation plan
2. **Plan Contents**:
   - Break down the feature into discrete, parallelizable tasks
   - Identify which tasks can be done by subagents concurrently
   - Define clear interfaces between components
   - Consider security implications
   - Plan test coverage strategy
   - **Apply Lean Code to every proposed component**: for each one, note why it needs to exist (which concrete requirement drives it) and what it reuses (existing utility, library, framework feature) instead of adding new code. A component that can't answer "why does this need to exist" is a candidate to cut from the plan.
3. **Get User Approval**: Exit plan mode only after user approves the plan

**Step 2.3: Complete Phase 2**

```
TaskUpdate: { taskId: "3", status: "completed" }
TaskList  # Check that Task 4 is now unblocked
```

### Phase 3: Parallel Implementation with Subagents

**Step 3.1: Start Phase 3**

```
TaskUpdate: { taskId: "4", status: "in_progress" }
```

**Step 3.2: Create Parallel Subagent Tasks**

For features with independent components, create parallel child tasks:

```
# Example: API + UI + Tests in parallel
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

# All parallel tasks blocked only by planning phase
TaskUpdate: { taskId: "api-task", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "ui-task", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "test-task", addBlockedBy: ["3"] }

# Phase 5 (Verification) blocked by ALL parallel tasks
TaskUpdate: { taskId: "5", addBlockedBy: ["api-task", "ui-task", "test-task"] }
```

**Step 3.3: Execute Parallel Subagents**

For each parallelizable task group, spawn subagents using the Task tool:

**Subagent Instructions Template:**
```
Task tool call:
- subagent_type: "general-purpose"
- model: "sonnet"  # REQUIRED - never leave unset (defaults to parent model)
- prompt: |
    Implement [specific task description].

    First, read the project's CLAUDE.md to understand conventions and patterns.
    Then trace the real flow of the code you're about to touch, end to end —
    a diff written without understanding the existing flow is a liability, not lean.

    Lean Code — write the smallest change that fully does the job:
    1. Before adding anything new, search this codebase, the standard library, the
       framework, and installed dependencies for something that already does it.
       Reuse beats reimplementation.
    2. Build only what this task concretely needs — no speculative flags, options,
       or extension points, no interface/factory/wrapper for a single caller.
    3. If a bug or gap is shared by multiple call sites, fix it once in the shared
       function rather than patching every caller.
    4. Follow existing codebase patterns and conventions.
    5. Never cut the floor: input/trust-boundary validation, error and data-loss
       handling, security, and accessibility stay in scope no matter how small the
       change is. A version that drops one of these isn't leaner — it's unfinished.
    6. If you deliberately simplify something (defer a real limitation rather than
       skip the floor above), leave `// LEAN-DEBT: <limitation>. Upgrade when <trigger>.`
       instead of a silent gap.
    7. If the leanest correct solution differs from what was asked, implement what
       was asked but flag the leaner alternative in your report — do not silently
       substitute your own approach.
    8. Write comprehensive tests (unit + integration where applicable). All tests
       MUST pass before completion.
    9. Add necessary type definitions (if typed language).

    Project-specific commands (discovered in Phase 0):
    - Test command: [INSERT DISCOVERED TEST COMMAND]
    - Lint command: [INSERT DISCOVERED LINT COMMAND]

    After implementation:
    1. Run the test suite to verify all tests pass
    2. Run linting to ensure code quality
    3. Report back what was implemented, any LEAN-DEBT markers left, and any leaner
       alternative you flagged (do NOT commit - the main agent will handle commits)

    If tests fail, fix them before reporting completion.
    If you encounter ambiguous requirements, report back and ask for clarification instead of guessing.
```

**Model Selection for Subagents:**
- **Use `model: "sonnet"`** for code implementation, test writing, documentation writing, architecture decisions, and complex changes
- **Use `model: "haiku"`** ONLY for exploration and research tasks
- **Never use Opus** - too expensive for team/subagent workflows
- **Always set `model` explicitly** - unset defaults to the parent model (which may be opus)

**After each subagent completes:**
1. Review the changes
2. Update the corresponding child task: `TaskUpdate: { taskId: "child-task-id", status: "completed" }`
3. Run `/cc-arsenal:git:commit` to commit the subagent's work (if available) or create a conventional commit manually
4. Proceed to the next subagent or phase

**Parallelization Strategy:**
- Group independent tasks together and spawn multiple subagents simultaneously
- Use sequential subagents for dependent tasks
- Track each subagent's work with its own task for visibility

**Step 3.4: Complete Phase 3**

```
# After all subagent tasks complete
TaskUpdate: { taskId: "4", status: "completed" }
TaskList  # Verify Phase 5 is now unblocked
```

### Phase 4: Integration & Verification

**Step 4.1: Start Phase 4**

```
TaskUpdate: { taskId: "5", status: "in_progress" }
```

**Step 4.2: Run Quality Checks**

After all subagents complete, run verification using the **discovered commands from Phase 0**:

1. **Run Full Test Suite**: Use discovered test command
2. **Lint Check**: Use discovered lint command
3. **Type Check**: Use discovered type-check/build command
4. **Fix All Issues**: If any test, lint, or build errors occur, fix them before proceeding. Repeat until all checks pass.

**Example verification (commands vary by project):**
```bash
# Python project with Makefile
make test && make lint && make type-check

# Node.js project with package.json
npm test && npm run lint && npm run build

# Python project with just
just test && just lint

# Simple Python project
pytest && ruff check . && pyright
```

**Step 4.3: Complete Phase 4**

```
TaskUpdate: { taskId: "5", status: "completed" }
TaskList  # Check that Task 6 is now unblocked
```

### Phase 5: Final Commit

**Step 5.1: Start Phase 5**

```
TaskUpdate: { taskId: "6", status: "in_progress" }
```

**Step 5.2: Create Final Commit**

Only proceed when all checks pass:
1. Review all changes made by subagents
2. Create a final integration commit if needed using conventional commit format
3. Summarize what was implemented

**Step 5.3: Complete Phase 5 and Feature Implementation**

```
TaskUpdate: { taskId: "6", status: "completed" }
TaskList  # Show final status - all tasks should be completed
```

### Phase 6: Manual Testing (Optional - For UI Features)

If the feature has a UI component, use the `agent-browser` skill for browser automation:

1. **Start the Development Server** (using discovered dev command)
2. **Navigate to the Feature**: `agent-browser open <url>`
3. **Visual Verification**: `agent-browser snapshot -i`
4. **Interactive Testing**: Use refs to interact with elements (`agent-browser click @e1`)
5. **Screenshot Evidence**: `agent-browser screenshot page.png`
6. **Cleanup**: `agent-browser close`

**When to Skip Manual Testing:**
- Backend-only changes (API routes, server actions)
- Pure refactoring with no UI changes
- Test-only changes
- CLI tools without UI

## Subagent Quality Checklist

Each subagent's output should satisfy:
- [ ] All new code has tests, and all tests pass
- [ ] No linting errors, no type errors (if applicable)
- [ ] Code follows existing patterns
- [ ] Security best practices followed
- [ ] Reuse checked first — no code that duplicates an existing utility, library, or framework feature
- [ ] No unrequested abstractions — no interface/factory/wrapper introduced for a single caller
- [ ] The never-negligent floor is intact: validation, error/data-loss handling, security, and accessibility were not trimmed for scope
- [ ] Any deliberate shortcut carries a `LEAN-DEBT:` marker instead of a silent gap

## Error Handling

If a subagent encounters issues:
1. Log the error clearly
2. Attempt to fix within scope
3. If unable to fix, report back with details
4. Do NOT commit broken code

## Handling Ambiguity

If encountering unclear or ambiguous requirements at any phase:
1. Use `AskUserQuestion` to clarify before proceeding
2. Do NOT guess or make assumptions about critical decisions
3. Present options with trade-offs when multiple valid approaches exist

## Output Format

Provide a summary including:
- Features implemented
- Files created/modified
- Tests added
- Manual testing results (if performed)
- Any known limitations or follow-up items

## Usage

```bash
# Implement a specific feature
/implement-feature Add user authentication with OAuth2

# Implement with more context
/implement-feature Create a REST API endpoint for managing user preferences with validation

# Implement a refactoring task
/implement-feature Refactor the payment module to use the strategy pattern
```

## Important Notes

- **Always run Phase 0 first** - Never assume which tools are available
- **Project-specific workflows** - Each project may have unique quality gates
- **Commit strategy** - Prefer smaller, logical commits over one big commit
- **Ask when unsure** - Better to clarify than to guess incorrectly
