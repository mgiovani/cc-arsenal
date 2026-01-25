---
description: "Fix bugs using test-driven debugging and verification"
argument-hint: "[bug_description_or_issue_id] [--branch name] [--interactive]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task", "TodoWrite", "WebSearch", "WebFetch", "AskUserQuestion"]
---

# Bug Fix Command

Fix bugs systematically using test-driven development, root cause analysis, and comprehensive verification across any project type.

## Anti-Hallucination Guidelines

**CRITICAL**: Bug fixes must be based on ACTUAL code and VERIFIED test results:
1. **Reproduce the bug first** - Don't fix what you haven't seen fail. Run the failing test or scenario to confirm the bug exists.
2. **Test-driven approach** - Write/locate a failing test before implementing the fix. Verify it actually fails.
3. **Verify root cause** - Use grep/search to locate actual bug location with evidence (file paths, line numbers).
4. **Test verification** - Run full test suite to prove fix works. All tests must pass.
5. **No invented fixes** - Only implement solutions that address the demonstrated root cause.
6. **Reference real code** - Never make claims about code you haven't read.

## Your Task

### Bug Description

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

Store discovered commands for use in later phases. Example output:
```
Project Commands:
- Test All: `make test` or `pytest`
- Test Single: `pytest path/to/test.py::test_name` or `npm test -- path/to/test.spec.ts`
- Test Watch: `pytest --watch` or `npm run test:watch`
- Lint: `make lint` or `ruff check`
- Type Check: `make type-check` or `tsc --noEmit`
- Dev Server: `make dev` or `npm run dev`
- Debug: `pytest -vv -s` or `npm run test:debug`
```

**IMPORTANT**: Never assume which test framework or tools are available. Use only the discovered commands.

### Phase 1: Bug Analysis & Reproduction

**Goal**: Understand the bug, locate it in code, and reproduce it reliably.

```
Use TodoWrite to track analysis:

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

If the user didn't provide clear symptoms, use `AskUserQuestion`:
```
Ask user:
1. What is the expected behavior?
2. What actually happens (error messages, incorrect output)?
3. How to reproduce (steps, inputs, conditions)?
4. Is there an existing failing test?
```

**Step 1.2: Locate or Create Failing Test**

Search for existing test coverage:
```
Use Grep tool:
- pattern: [relevant test pattern based on bug description]
- output_mode: "files_with_matches"
- path: "tests/" or "test/" or "__tests__/" (discovered in Phase 0)
```

If no test exists for this bug:
- Create a minimal failing test that reproduces the bug
- Place it in appropriate test file following project conventions
- Use discovered test patterns from existing tests

**Step 1.3: Reproduce the Bug**

Run the specific test using discovered test command:
```bash
# Example (use actual discovered command from Phase 0):
pytest tests/test_feature.py::test_bug_case -vv
# or
npm test -- path/to/test.spec.ts
```

**CRITICAL**: Verify the test actually fails. Capture error output.

**Step 1.4: Root Cause Analysis**

Use parallel subagents for comprehensive analysis:

```
Agent 1 - Bug Location:
- prompt: "Based on the failing test output and error message:
    [PASTE ERROR OUTPUT]

    Use Grep and Read tools to:
    1. Find the exact location of the bug (file path, line numbers)
    2. Read the buggy code and surrounding context
    3. Identify why the code produces the wrong behavior
    4. Provide evidence (stack trace, variable values, control flow)

    Return: File paths, line numbers, root cause explanation with evidence."
- subagent_type: "Explore"

Agent 2 - Impact Analysis:
- prompt: "For the bug in [LOCATION], search the codebase to find:
    1. Other code that might be affected by the same issue
    2. Similar patterns that might have the same bug
    3. Related tests that might also fail
    4. Dependencies or callers of the buggy code

    Return: List of potentially affected files and patterns."
- subagent_type: "Explore"

Agent 3 - Research Similar Bugs (if external library involved):
- prompt: "Search for documented solutions or patterns for this type of bug:
    [BUG DESCRIPTION]

    Focus on: official docs, known issues, recommended fixes.
    Return: Best practices and recommended solutions."
- subagent_type: "general-purpose"
```

**Step 1.5: Confirm Root Cause**

Before proceeding, verify your analysis:
- Re-read the buggy code
- Confirm your theory explains all symptoms
- Check if there are edge cases or additional factors

If uncertain, use `AskUserQuestion` to validate your understanding.

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

**Step 2.1: Design Fix Strategy**

Use a subagent for fix design:
```
Agent - Fix Design:
- prompt: "Design a fix for this bug:

    Root Cause: [EXPLANATION FROM PHASE 1]
    Bug Location: [FILE:LINE]
    Failing Test: [TEST DESCRIPTION]

    Design a fix that:
    1. Addresses ONLY the root cause (no refactoring)
    2. Follows existing code patterns in this project
    3. Has minimal scope (fewest lines changed)
    4. Doesn't introduce breaking changes
    5. Handles edge cases identified

    Consider multiple approaches and recommend the best one.
    Return: Proposed fix with explanation and trade-offs."
- subagent_type: "general-purpose"
```

**Step 2.2: Plan Test Coverage**

Ensure the fix will be properly tested:
- Does the failing test adequately cover the bug?
- Are there edge cases that need additional tests?
- Should we add regression tests?

**Step 2.3: Get Approval for Non-Trivial Fixes**

If the fix involves:
- Changes to >3 files
- Modifications to public APIs
- Potential performance implications
- Breaking changes

Use `AskUserQuestion` to present the plan and get approval:
```
Ask user:
"I've identified the root cause: [EXPLANATION]

Proposed fix:
[DESCRIPTION]

This will modify:
- [FILE 1]: [CHANGES]
- [FILE 2]: [CHANGES]

Alternatives considered:
- [ALTERNATIVE 1]: [WHY NOT CHOSEN]

Proceed with this approach? (y/n/suggest alternative)
```

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

**Step 3.1: Implement the Fix**

Use the Edit tool to make minimal, focused changes:
```
For each file identified in Phase 2:
1. Read the file to confirm current state
2. Apply the fix using Edit tool
3. Verify the edit matches the plan
```

**Step 3.2: Verify the Fix Locally**

Run the specific failing test using discovered command:
```bash
# Use actual command from Phase 0
pytest tests/test_feature.py::test_bug_case -vv
```

**CRITICAL**: The test must now PASS. If it doesn't:
- Re-analyze the root cause
- Check for additional factors
- Debug the fix implementation
- Repeat until test passes

**Step 3.3: Test for Side Effects**

Check if the fix broke anything else:

For projects with test suites:
```bash
# Use discovered test command from Phase 0
make test
# or
npm test
# or
pytest
```

For projects with browser/UI testing capability:
- If the bug affects UI and agent-browser skill is available
- Start dev server using discovered command
- Navigate to affected UI
- Verify the fix works in the browser
- Take screenshots as evidence

**Step 3.4: Fix Any New Failures**

If tests fail:
1. Identify which tests failed
2. Understand why (related to your fix?)
3. Adjust the fix or update tests if they're incorrectly specified
4. Repeat until all tests pass

### Phase 4: Quality Verification

**Goal**: Ensure the fix meets all quality standards before committing.

```
TodoWrite:
- [ ] All tests pass (including the previously failing test)
- [ ] No linting errors
- [ ] No type errors (if applicable)
- [ ] Code follows project conventions
- [ ] No unnecessary changes
```

Run all quality checks using discovered commands from Phase 0:

```bash
# Example (use actual discovered commands):
make test && make lint && make type-check
# or
npm test && npm run lint && npm run build
# or
pytest && ruff check . && pyright
```

**Quality Gates Checklist**:
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

**Goal**: Create a proper conventional commit documenting the fix.

If `/cc-arsenal:git:commit` skill is available:
```bash
/cc-arsenal:git:commit
```

Otherwise, create a conventional commit manually:
```bash
git add [files modified]
git commit -m "fix: [concise description of what was fixed]

- [Detail about root cause]
- [Detail about solution approach]
- [Reference to issue/ticket if applicable]

Closes #[ISSUE_NUMBER]"
```

**Commit Message Guidelines**:
- Type: `fix:` (for bug fixes)
- Scope: `(module)` if applicable
- Subject: Describe WHAT was fixed (not how)
- Body: Explain WHY this fixes the bug
- Footer: Reference issue numbers

**Example**:
```
fix(auth): prevent token expiration on page reload

The authentication middleware was not refreshing tokens when
the user reloaded the page, causing premature logouts.

This fix adds token refresh logic to the middleware that
runs on every page load, checking token expiration and
refreshing when needed.

Closes #123
```

### Phase 6: Verification Summary

Report to the user:

```
## Bug Fix Complete ✅

**Bug**: [DESCRIPTION]
**Root Cause**: [EXPLANATION with file:line references]
**Solution**: [WHAT WAS CHANGED]

**Files Modified**:
- [FILE 1]: [CHANGE DESCRIPTION]
- [FILE 2]: [CHANGE DESCRIPTION]

**Test Results**:
- Previously failing test: ✅ PASS
- Full test suite: ✅ [X/X tests passed]
- Linting: ✅ No errors
- Type checking: ✅ No errors

**Commit**: [COMMIT SHA] - [COMMIT MESSAGE]

**Next Steps**:
- [ ] Push to remote: `git push`
- [ ] Create PR: `/cc-arsenal:git:create-pr` (if available)
- [ ] Manual testing: [STEPS if applicable]
```

## Argument Parsing

Parse optional arguments from the command invocation:

**Optional Flags**:
- `--branch name` or `-b name`: Create fix on a specific branch (default: current branch)
- `--interactive` or `-i`: Prompt for confirmation at each phase
- `--test-only`: Only reproduce and analyze the bug, don't implement fix

**Examples**:
```bash
/dev:fix-bug User login fails with invalid session error
/dev:fix-bug #123 --branch fix/auth-session-bug
/dev:fix-bug "Payment webhook returns 500 error" --interactive
/dev:fix-bug JIRA-456 --test-only
```

## Browser Testing Integration (Optional)

If the bug affects a web UI and the agent-browser skill is available:

**After Phase 3 (Implementation), before Phase 4**:

1. **Start Development Server**:
```bash
# Use discovered dev command from Phase 0
make dev
# or
npm run dev
```

2. **Browser Testing** (if agent-browser skill is available):
```
Use agent-browser skill to:
1. Navigate to the affected page/component
2. Reproduce the original bug scenario
3. Verify the bug is now fixed
4. Test edge cases
5. Take screenshots as evidence
```

3. **Report Browser Test Results**:
Include in final summary with screenshot evidence.

**When to Skip Browser Testing**:
- Backend-only bugs (API, database, services)
- CLI tool bugs
- Unit test failures (not integration/E2E)
- No development server available
- User explicitly requested to skip

## Error Handling

If you encounter issues during any phase:

**Test Failures After Fix**:
1. Re-run the specific test with verbose output
2. Analyze the new failure mode
3. Check if your fix introduced a regression
4. Adjust the fix or revert if necessary
5. Never commit code with failing tests

**Ambiguous Bug Description**:
1. Use `AskUserQuestion` to clarify:
   - Expected vs actual behavior
   - Steps to reproduce
   - Error messages or symptoms
2. Don't proceed with guesses

**Cannot Reproduce Bug**:
1. Verify you're using the correct test command
2. Check if the bug was already fixed
3. Ask user for more details on reproduction
4. Document findings and report inability to reproduce

**Multiple Root Causes**:
1. Identify all contributing factors
2. Ask user which to fix first
3. Consider if they should be fixed together or separately
4. Plan accordingly

## Usage Examples

### Example 1: Simple Bug Fix

```bash
/dev:fix-bug User profile page throws 404 on refresh
```

**Process**:
1. Discover project uses `npm test` and `npm run lint`
2. Find failing test or create one
3. Locate bug: routing issue in Next.js app
4. Fix: Add missing route configuration
5. Verify: All tests pass
6. Commit: `fix(routing): add profile route configuration`

### Example 2: Bug with Issue Number

```bash
/dev:fix-bug #789 --branch fix/payment-webhook
```

**Process**:
1. Fetch issue details with `gh issue view 789`
2. Discover project uses `make test` and `make lint`
3. Reproduce failing webhook call
4. Root cause: missing signature validation
5. Fix: Add HMAC signature verification
6. Verify with integration tests
7. Commit: `fix(webhooks): validate payment signatures\n\nCloses #789`

### Example 3: Interactive Bug Fix

```bash
/dev:fix-bug "Auth tokens expire too quickly" --interactive
```

**Process**:
1. Prompt user after Phase 0 (confirm discovered commands)
2. Prompt user after Phase 1 (confirm root cause analysis)
3. Prompt user after Phase 2 (approve fix plan)
4. Implement fix
5. Prompt user before commit (review changes)

### Example 4: Analysis Only

```bash
/dev:fix-bug Database query timeout in reports --test-only
```

**Process**:
1. Run Phases 0-2 only
2. Report root cause analysis
3. Suggest fix approaches
4. Don't implement or commit
5. Let user decide next steps

## Important Notes

- **Always run Phase 0 first**: Never assume which tools are available
- **Test-driven is critical**: See the test fail before fixing
- **Minimal changes**: Fix the bug, don't refactor unrelated code
- **Evidence-based**: Reference actual file paths and line numbers
- **All tests must pass**: Never commit code with failing tests
- **Ask when unsure**: Better to clarify than to guess incorrectly
- **Browser testing is optional**: Only when relevant and tools available
- **Document the fix**: Clear commit message explaining root cause and solution

## Quality Checklist

Before reporting completion, verify:

- [ ] Bug was reproduced with evidence (failing test output)
- [ ] Root cause was identified with file:line references
- [ ] Fix was implemented with minimal scope
- [ ] Previously failing test now passes
- [ ] Full test suite passes (no regressions)
- [ ] Linting passes (no new errors)
- [ ] Type checking passes (if applicable)
- [ ] Code follows project conventions
- [ ] Conventional commit was created
- [ ] Fix was verified (and browser-tested if applicable)

---

**Reference**: Based on `/dev:implement-feature` pattern with test-driven debugging workflow
**Output**: Bug fix with passing tests, quality checks, and conventional commit
