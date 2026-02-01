---
name: fix-bug
description: "Fix bugs using test-driven debugging, root cause analysis, and comprehensive verification. This skill should be used when a user wants to fix a bug, debug an issue, resolve an error, or investigate failing tests across any project type."
disable-model-invocation: true
argument-hint: "[bug_description_or_issue_id] [--branch name] [--interactive]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TodoWrite, WebFetch, AskUserQuestion
---

# Bug Fix

Fix bugs systematically using test-driven development, root cause analysis, and comprehensive verification across any project type.

## Anti-Hallucination Guidelines

**CRITICAL**: Bug fixes must be based on ACTUAL code and VERIFIED test results:
1. **Reproduce the bug first** - Do not fix what has not been seen failing. Run the failing test or scenario to confirm the bug exists.
2. **Test-driven approach** - Write/locate a failing test before implementing the fix. Verify it actually fails.
3. **Verify root cause** - Use grep/search to locate actual bug location with evidence (file paths, line numbers).
4. **Test verification** - Run full test suite to prove fix works. All tests must pass.
5. **No invented fixes** - Only implement solutions that address the demonstrated root cause.
6. **Reference real code** - Never make claims about code that has not been read.

## Bug Description

$ARGUMENTS

## Implementation Workflow

**Use TodoWrite to track progress through each phase.**

### Phase 0: Project Discovery (REQUIRED)

Before any debugging, discover how this project works:

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
```

Store discovered commands for use in later phases.

**IMPORTANT**: Never assume which test framework or tools are available. Use only the discovered commands.

### Phase 1: Bug Analysis & Reproduction

**Goal**: Understand the bug, locate it in code, and reproduce it reliably.

```
TodoWrite:
- [ ] Understand bug symptoms and expected behavior
- [ ] Locate failing test or create reproduction test
- [ ] Run test to confirm failure (with evidence)
- [ ] Identify bug location in codebase
- [ ] Analyze root cause with evidence
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

Use parallel subagents for comprehensive analysis:

```
Agent 1 - Bug Location (Explore):
  Find the exact location of the bug (file path, line numbers),
  read the buggy code and surrounding context,
  identify why the code produces the wrong behavior,
  provide evidence (stack trace, variable values, control flow).

Agent 2 - Impact Analysis (Explore):
  Search the codebase for other code affected by the same issue,
  similar patterns with the same bug, related tests that might fail,
  dependencies or callers of the buggy code.

Agent 3 - Research (general-purpose, only if external library involved):
  Search for documented solutions or patterns for this type of bug.
```

**Step 1.5: Confirm Root Cause**

Before proceeding, verify the analysis:
- Re-read the buggy code
- Confirm the theory explains all symptoms
- Check for edge cases or additional factors

If uncertain, use `AskUserQuestion` to validate understanding.

### Phase 2: Fix Planning

**Goal**: Design a minimal, focused fix that addresses the root cause without side effects.

```
TodoWrite:
- [ ] Design fix approach
- [ ] Identify files to modify
- [ ] Plan test coverage for fix
- [ ] Consider edge cases and side effects
- [ ] Get user approval if fix is non-trivial
```

Use a subagent for fix design that:
1. Addresses ONLY the root cause (no refactoring)
2. Follows existing code patterns in this project
3. Has minimal scope (fewest lines changed)
4. Does not introduce breaking changes
5. Handles edge cases identified

**Get Approval for Non-Trivial Fixes**: If the fix involves changes to >3 files, modifications to public APIs, potential performance implications, or breaking changes, use `AskUserQuestion` to present the plan and get approval.

### Phase 3: Implementation

**Goal**: Implement the fix following the plan, ensuring tests pass.

```
TodoWrite:
- [ ] Implement the fix
- [ ] Verify failing test now passes
- [ ] Run full test suite
- [ ] Fix any new failures
- [ ] Verify no linting errors
```

1. **Implement the Fix** - Use the Edit tool to make minimal, focused changes
2. **Verify Locally** - Run the specific failing test. **CRITICAL**: The test must now PASS. If not, re-analyze and repeat.
3. **Test for Side Effects** - Run full test suite using discovered commands
4. **Fix Any New Failures** - Adjust the fix or update tests if incorrectly specified. Repeat until all tests pass.

### Phase 4: Quality Verification

Run all quality checks using discovered commands from Phase 0. **Quality Gates Checklist**:
- [ ] Previously failing test now passes
- [ ] All existing tests still pass
- [ ] No new linting errors introduced
- [ ] No type errors (if typed language)
- [ ] Fix addresses root cause only
- [ ] No unnecessary refactoring
- [ ] Minimal, focused changes
- [ ] Follows existing code patterns

**If any check fails**: Fix the issue before proceeding. Do not commit broken code.

### Phase 5: Final Commit

If `/cc-arsenal:git:commit` skill is available, use it. Otherwise, create a conventional commit manually:

```bash
git add [files modified]
git commit -m "fix: [concise description of what was fixed]

- [Detail about root cause]
- [Detail about solution approach]
- [Reference to issue/ticket if applicable]

Closes #[ISSUE_NUMBER]"
```

### Phase 6: Verification Summary

Report to the user with: bug description, root cause (with file:line references), solution, files modified, test results (previously failing test, full suite, linting, type checking), commit info, and next steps.

## Additional Resources

For detailed examples, argument parsing, browser testing integration, and error handling patterns, see:
- [references/examples.md](references/examples.md) - Usage examples, argument parsing, browser testing, and error handling

## Important Notes

- **Always run Phase 0 first**: Never assume which tools are available
- **Test-driven is critical**: See the test fail before fixing
- **Minimal changes**: Fix the bug, do not refactor unrelated code
- **Evidence-based**: Reference actual file paths and line numbers
- **All tests must pass**: Never commit code with failing tests
- **Ask when unsure**: Better to clarify than to guess incorrectly
- **Browser testing is optional**: Only when relevant and tools available
- **Document the fix**: Clear commit message explaining root cause and solution
