---
name: implement-feature
description: "Implement features using senior staff engineer best practices with parallel subagent orchestration. Automatically activates when users want to implement a new feature, add functionality, build a component, or create new capabilities. Follows SOLID, DRY, and YAGNI principles with automated project discovery and quality verification."
disable-model-invocation: false
argument-hint: "<feature_description>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, EnterPlanMode, AskUserQuestion
hooks:
  Stop:
    - hooks:
      - type: agent
        prompt: "Verify implementation is complete and correct:\n\n1. **Run tests**: Use the test command discovered in Phase 0. All tests must pass.\n2. **Run linter**: Use the lint command discovered in Phase 0. No linting errors allowed.\n3. **Run type check**: If applicable, run type-check/build command.\n\nIf any check fails, report the failure clearly and return decision: block with reason. Only allow stopping when all checks pass.\n\nDiscovered commands should be in the task context from Phase 0. If Phase 0 was not completed, discover them now by reading CLAUDE.md, checking for Makefile/package.json/pyproject.toml, and identifying test/lint/build commands."
        timeout: 180
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

## Quality Gates

This skill includes automatic implementation verification before completion:

### Completion Verification (Stop Hook)

When you attempt to stop working (mark implementation as complete), an automated verification agent runs to ensure quality:

**Verification Steps:**
1. **Test Suite**: Runs discovered test command from Phase 0 (e.g., `make test`, `npm test`, `pytest`)
2. **Linting**: Runs discovered lint command from Phase 0 (e.g., `make lint`, `npm run lint`, `ruff check`)
3. **Type Checking**: If applicable, runs type-check or build command

**Behavior:**
- ✅ **All checks pass**: Implementation marked complete
- ❌ **Any check fails**: Completion blocked, error details provided, Claude continues working to fix issues
- ℹ️ **Commands not found**: Hook attempts to discover commands from CLAUDE.md or project files

**Example blocked completion:**
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
Implement [specific task description].

First, read the project's CLAUDE.md to understand conventions and patterns.

Requirements:
1. Follow existing codebase patterns and conventions
2. Apply SOLID, DRY, YAGNI principles
3. Write comprehensive tests (unit + integration where applicable)
4. All tests MUST pass before completion
5. Handle errors appropriately
6. Add necessary type definitions (if typed language)

Project-specific commands (discovered in Phase 0):
- Test command: [INSERT DISCOVERED TEST COMMAND]
- Lint command: [INSERT DISCOVERED LINT COMMAND]

After implementation:
1. Run the test suite to verify all tests pass
2. Run linting to ensure code quality
3. Report back what was implemented (do NOT commit - the main agent will handle commits)

If tests fail, fix them before reporting completion.
If you encounter ambiguous requirements, report back and ask for clarification instead of guessing.
```

**Model Selection for Subagents:**
- **Use Sonnet (default)** for code implementation, test writing, and complex changes
- **Use Haiku** only if the subagent is doing pure exploration/research (rare in Phase 3)

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

## Quality Gates

Each subagent MUST ensure:
- [ ] All new code has tests
- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors (if applicable)
- [ ] Code follows existing patterns
- [ ] Security best practices followed
- [ ] No over-engineering (YAGNI)

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
