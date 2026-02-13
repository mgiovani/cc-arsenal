---
# Enhancement for: fix-bug
disable-model-invocation: false
argument-hint: "[bug_description_or_issue_id] [--branch name] [--interactive]"
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: 'Verify bug fix is complete and correct:


        1. **Reproduce fix**: Run the originally failing test or scenario. It must now
        pass.

        2. **No regressions**: Run full test suite using the test command from Phase
        0. All tests must pass.

        3. **Root cause addressed**: Verify the fix addresses the actual root cause,
        not just symptoms.


        If any verification fails, report it clearly and return decision: block with
        reason. Only allow stopping when the bug is truly fixed.


        Use test commands discovered in Phase 0. If not available, discover them now
        from CLAUDE.md or project files.'
      timeout: 120
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Quality Gates

This skill includes automatic bug fix verification before completion:

### Fix Verification (Stop Hook)

When you attempt to stop working (mark bug as fixed), an automated verification agent runs to ensure the fix is complete:

**Verification Steps:**
1. **Fix Confirmation**: Runs the originally failing test or reproduces the bug scenario. Must now pass/work.
2. **Regression Check**: Runs full test suite to ensure no new bugs introduced
3. **Root Cause Validation**: Verifies the fix addresses the actual root cause, not just symptoms

**Behavior:**
- ✅ **All verifications pass**: Bug marked as fixed
- ❌ **Any verification fails**: Completion blocked, Claude continues debugging
- ⚠️ **Original test not identified**: Hook attempts to find relevant tests or asks for clarification

**Example blocked completion:**
```
⚠️ Bug fix verification failed:

Original Issue: ❌ STILL FAILING
  - The bug still reproduces with the same error
  - Test: test_user_login still fails with AuthenticationError

Regression: ✅ PASSED (other tests still pass)

🔧 The fix does not resolve the original issue. Root cause analysis needed.
```

**Benefits:**
- Prevents marking bugs "fixed" when they still reproduce
- Catches regression bugs introduced by the fix
- Enforces test-driven debugging discipline
- Ensures actual root cause is addressed, not just symptoms

## Bug Description

$ARGUMENTS

## Task Management

This skill uses Claude Code's Task Management System for strict sequential dependency tracking through the debugging workflow.

**When to Use Tasks:**
- Multi-step debugging requiring root cause analysis
- Bugs spanning multiple files or components
- Work requiring progress tracking across sessions

**When to Skip Tasks:**
- Trivial 1-line fixes with obvious solutions
- Simple typo corrections
- Quick configuration changes

**Task Structure:**
Bug fixes create a strict sequential chain where each phase must complete before the next can start, ensuring test-driven development discipline.

## Implementation Workflow

**Task tracking replaces TodoWrite.** Create task chain at start, update as completing each phase.

### Phase 0: Project Discovery (REQUIRED)

**Step 0.1: Create Task Dependency Chain**

Before debugging, create the strict sequential task structure:

```
TaskCreate:
  subject: "Phase 0: Discover project workflow"
  description: "Identify test, lint, debug commands from CLAUDE.md and task runners"
  activeForm: "Discovering project workflow"

TaskCreate:
  subject: "Phase 1: Reproduce and analyze bug"
  description: "Locate failing test, reproduce bug, identify root cause"
  activeForm: "Analyzing bug"

TaskCreate:
  subject: "Phase 2: Plan fix"
  description: "Design minimal fix approach"
  activeForm: "Planning fix"

TaskCreate:
  subject: "Phase 3: Implement fix"
  description: "Apply fix and verify test passes"
  activeForm: "Implementing fix"

TaskCreate:
  subject: "Phase 4: Verify quality"
  description: "Run full test suite, lint, type-check"
  activeForm: "Verifying fix quality"

TaskCreate:
  subject: "Phase 5: Final commit"
  description: "Create conventional commit with fix details"
  activeForm: "Creating final commit"

# Set up strict sequential chain
TaskUpdate: { taskId: "2", addBlockedBy: ["1"] }
TaskUpdate: { taskId: "3", addBlockedBy: ["2"] }
TaskUpdate: { taskId: "4", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "5", addBlockedBy: ["4"] }
TaskUpdate: { taskId: "6", addBlockedBy: ["5"] }

# Start first task
TaskUpdate: { taskId: "1", status: "in_progress" }
```

**Step 0.2: Discover Project Workflow**

Use Haiku-powered Explore agent for token-efficient discovery:

```
Use Task tool with Explore agent:
- prompt: "Discover the development workflow for this project:
    1. Read CLAUDE.md if it exists - extract debugging and testing conventions
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test command (e.g., make test, just test, npm test, pytest, bun test)
    4. Identify how to run a single test or test file
    5. Identify the lint command (e.g., make lint, npm run lint, ruff check)
    6. Identify the type-check command if applicable
    7. Identify the dev server command if this is a web app
    8. Check for debugging tools (pytest -v, npm run test:debug, etc.)
    9. Note any pre-commit hooks or quality gates
    Return a structured summary of all available commands."
- subagent_type: "Explore"
- model: "haiku"  # Token-efficient for discovery
```

Store discovered commands for use in later phases.

**IMPORTANT**: Never assume which test framework or tools are available. Use only the discovered commands.

**Step 0.3: Complete Phase 0**

```
TaskUpdate: { taskId: "1", status: "completed" }
TaskList  # Check that Task 2 is now unblocked
```

### Phase 1: Bug Analysis & Reproduction

**Goal**: Understand the bug, locate it in code, and reproduce it reliably.

**Step 1.0: Start Phase 1**

```
TaskUpdate: { taskId: "2", status: "in_progress" }
```

**Step 1.1: Understand Bug Symptoms**

If the user provided an issue ID or bug description:
- Read the issue/ticket if accessible (use Bash with `gh issue view` or `jira issue view` if available)
- Understand expected vs actual behavior
- Identify error messages or symptoms

If the user did not provide clear symptoms, use `AskUserQuestion` to clarify expected behavior, actual behavior, reproduction steps, and whether an existing failing test exists.

**Step 1.2: Locate or Create Failing Test**

Search for existing test coverage using Grep. If no test exists for this bug:
- Create a minimal failing test that reproduces the bug
- Place it in appropriate test file following project conventions
- Use discovered test patterns from existing tests

**Step 1.3: Reproduce the Bug**

Run the specific test using discovered test command. **CRITICAL**: Verify the test actually fails. Capture error output.

**Step 1.4: Root Cause Analysis**

Use parallel subagents for comprehensive analysis with Haiku for exploration:

```
Agent 1 - Bug Location (Explore, Haiku):
  prompt: "Find the exact location of the bug (file path, line numbers),
          read the buggy code and surrounding context,
          identify why the code produces the wrong behavior,
          provide evidence (stack trace, variable values, control flow)."
  subagent_type: "Explore"
  model: "haiku"  # Token-efficient for code exploration

Agent 2 - Impact Analysis (Explore, Haiku):
  prompt: "Search the codebase for other code affected by the same issue,
          similar patterns with the same bug, related tests that might fail,
          dependencies or callers of the buggy code."
  subagent_type: "Explore"
  model: "haiku"  # Token-efficient for codebase search

Agent 3 - Research (general-purpose, Haiku, only if external library involved):
  prompt: "Search for documented solutions or patterns for this type of bug
          in [LIBRARY_NAME] library using Context7 and web search."
  subagent_type: "general-purpose"
  model: "haiku"  # Token-efficient for research
```

**Step 1.5: Confirm Root Cause**

Before proceeding, verify the analysis:
- Re-read the buggy code
- Confirm the theory explains all symptoms
- Check for edge cases or additional factors

If uncertain, use `AskUserQuestion` to validate understanding.

**Step 1.6: Complete Phase 1**

```
TaskUpdate: { taskId: "2", status: "completed" }
TaskList  # Check that Task 3 is now unblocked
```

### Phase 2: Fix Planning

**Goal**: Design a minimal, focused fix that addresses the root cause without side effects.

**Step 2.1: Start Phase 2**

```
TaskUpdate: { taskId: "3", status: "in_progress" }
```

**Step 2.2: Design Fix Approach**

Use a subagent for fix design that:
1. Addresses ONLY the root cause (no refactoring)
2. Follows existing code patterns in this project
3. Has minimal scope (fewest lines changed)
4. Does not introduce breaking changes
5. Handles edge cases identified

**Get Approval for Non-Trivial Fixes**: If the fix involves changes to >3 files, modifications to public APIs, potential performance implications, or breaking changes, use `AskUserQuestion` to present the plan and get approval.

**Step 2.3: Complete Phase 2**

```
TaskUpdate: { taskId: "3", status: "completed" }
TaskList  # Check that Task 4 is now unblocked
```

### Phase 3: Implementation

**Goal**: Implement the fix following the plan, ensuring tests pass.

**Step 3.1: Start Phase 3**

```
TaskUpdate: { taskId: "4", status: "in_progress" }
```

**Step 3.2: Apply Fix**

1. **Implement the Fix** - Use the Edit tool to make minimal, focused changes. Use Sonnet (default model) for code implementation.
2. **Verify Locally** - Run the specific failing test. **CRITICAL**: The test must now PASS. If not, re-analyze and repeat.
3. **Test for Side Effects** - Run full test suite using discovered commands
4. **Fix Any New Failures** - Adjust the fix or update tests if incorrectly specified. Repeat until all tests pass.

**Step 3.3: Complete Phase 3**

```
TaskUpdate: { taskId: "4", status: "completed" }
TaskList  # Check that Task 5 is now unblocked
```

### Phase 4: Quality Verification

**Step 4.1: Start Phase 4**

```
TaskUpdate: { taskId: "5", status: "in_progress" }
```

**Step 4.2: Run Quality Checks**

Run all quality checks using discovered commands from Phase 0. **Quality Gates Checklist**:
- [ ] Previously failing test now passes
- [ ] All existing tests still pass
- [ ] No new linting errors introduced
- [ ] No type errors (if typed language)
- [ ] Fix addresses root cause only
- [ ] No unnecessary refactoring
- [ ] Minimal, focused changes
- [ ] Follows existing code patterns

**If any check fails**: Fix the issue before proceeding. Do not commit broken code. Keep task as `in_progress` until all gates pass.

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

**Step 5.2: Create Commit**

If `/cc-arsenal:git:commit` skill is available, use it. Otherwise, create a conventional commit manually:

```bash
git add [files modified]
git commit -m "fix: [concise description of what was fixed]

- [Detail about root cause]
- [Detail about solution approach]
- [Reference to issue/ticket if applicable]

Closes #[ISSUE_NUMBER]"
```

**Step 5.3: Complete Phase 5 and Bug Fix**

```
TaskUpdate: { taskId: "6", status: "completed" }
TaskList  # Show final status - all tasks should be completed
```

### Phase 6: Verification Summary

Report to the user with: bug description, root cause (with file:line references), solution, files modified, test results (previously failing test, full suite, linting, type checking), commit info, and next steps.
