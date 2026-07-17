---
name: refactor
description: "Restructures existing code without changing its behavior — maps callers and test coverage, adds characterization tests where coverage is thin, then applies the change in small steps verified against the full test suite after each one. Use when the user wants to refactor, extract a method or class, simplify logic, reduce duplication, improve naming, restructure modules, or pay down technical debt in code that already works. Not for adding new functionality (use implement-feature) or fixing broken behavior (use fix-bug)."
disable-model-invocation: false
argument-hint: "<refactoring_description> [--scope file|module|project] [--interactive]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
hooks:
  Stop:
    - hooks:
      - type: agent
        prompt: "Verify refactoring is safe and complete:\n\n1. **Behavior preserved**: Run the full test suite using the test command from Phase 0. All tests must pass — the same tests that passed before the refactoring must still pass.\n2. **No regressions**: Run linter and type checker. No new errors allowed.\n3. **Characterization tests**: If characterization tests were added in Phase 3, verify they still pass.\n4. **Clean diff**: Review git diff to confirm only intentional refactoring changes exist — no accidental behavior changes, debug code, or commented-out code.\n\nIf any verification fails, report it clearly and return decision: block with reason. Only allow stopping when the refactoring is verified safe.\n\nUse test commands discovered in Phase 0. If not available, discover them now from CLAUDE.md or project files."
        timeout: 180
---

# Refactor

Refactor code safely using characterization tests, incremental changes, and continuous verification. Every change preserves existing behavior while improving code structure, readability, and maintainability.

## Refactoring Goal

$ARGUMENTS

## Core Principle: Behavior Preservation

**CRITICAL**: Refactoring changes code structure WITHOUT changing behavior. Every step must be verified against existing tests. If tests break, the refactoring introduced a bug — revert and retry.

## Anti-Hallucination Guidelines

1. **Read before changing** — Never refactor code that has not been read and understood. Understand all callers and dependencies first.
2. **Test before and after** — Run the full test suite before starting. Run it again after every incremental change. The results must match.
3. **Characterization tests first** — If test coverage is insufficient for the target code, write characterization tests that capture current behavior BEFORE refactoring.
4. **Incremental changes** — Make one small, verifiable change at a time. Never combine multiple refactoring steps into a single edit.
5. **No feature changes** — Do not add features, fix bugs, or change behavior during refactoring. These are separate tasks.
6. **Reference real code** — Never make claims about code structure that has not been verified by reading the actual files.
7. **Prefer deletion over addition** — The best refactoring step is usually the one that removes duplicated or dead code, not the one that adds a new layer around it. When several call sites share the same logic, consolidate it into one place and delete the copies rather than introducing a new abstraction that wraps them.
8. **Never trim the floor** — Simplifying structure must not simplify away a validation check, an error/data-loss path, a security control, or an accessibility branch. If a step would drop one, it is a behavior change, not a refactor — stop and re-scope it as a separate change.

## Quality Gates

A Stop hook runs the same four checks listed above (tests, lint/type, characterization tests, clean diff) automatically before the skill is allowed to finish. If any fails, completion is blocked and Claude must revert or fix the break — see the hook prompt at the top of this file for the exact wording.

## Task Management

This skill uses Claude Code's Task Management System for strict sequential dependency tracking through the refactoring workflow.

**When to Use Tasks:**
- Multi-step refactoring across files or modules
- Extract method/class operations requiring dependency analysis
- Large-scale restructuring with many callers
- Work requiring progress tracking across sessions

**When to Skip Tasks:**
- Simple rename (single variable/function)
- Trivial formatting or style fix
- Single-line simplification

For these, skip the task chain and Phase 0-5 structure entirely. Do the inline flow instead: run the existing tests, make the change, run the tests again. If they still pass, done — no TaskCreate, no subagents.

**Task Structure (everything else):**
Refactoring creates a strict sequential chain where each phase must complete before the next can start, ensuring characterization tests exist before any structural changes begin. After finishing each phase, mark its task `completed` and run `TaskList` to confirm the next one is unblocked — this applies at the end of every phase below and isn't repeated per-phase.

**Portability:** No `Task`/`TaskCreate` tools here? Drop the task chain and subagent fan-out — just work through Phase 0-5 yourself, in order. The sequencing (characterization tests before structural change) is what matters, not the tracking mechanism.

## Implementation Workflow

**Task tracking replaces TodoWrite.** Create task chain at start, update as completing each phase.

### Phase 0: Project Discovery (REQUIRED)

**Step 0.1: Create Task Dependency Chain**

Before refactoring, create the strict sequential task structure:

```
TaskCreate:
  subject: "Phase 0: Discover project workflow"
  description: "Identify test, lint, type-check commands from CLAUDE.md and task runners"
  activeForm: "Discovering project workflow"

TaskCreate:
  subject: "Phase 1: Analyze refactoring scope"
  description: "Map dependencies, callers, and test coverage for target code"
  activeForm: "Analyzing refactoring scope"

TaskCreate:
  subject: "Phase 2: Write characterization tests"
  description: "Ensure sufficient test coverage before making structural changes"
  activeForm: "Writing characterization tests"

TaskCreate:
  subject: "Phase 3: Incremental refactoring"
  description: "Apply refactoring in small verified steps"
  activeForm: "Refactoring incrementally"

TaskCreate:
  subject: "Phase 4: Final verification"
  description: "Run full test suite, lint, type-check — confirm behavior preserved"
  activeForm: "Verifying refactoring safety"

TaskCreate:
  subject: "Phase 5: Final commit"
  description: "Create conventional commit with refactoring summary"
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
    1. Read CLAUDE.md if it exists - extract testing and quality conventions
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test command (e.g., make test, just test, npm test, pytest, bun test)
    4. Identify how to run a single test file or specific test
    5. Identify the lint command (e.g., make lint, npm run lint, ruff check)
    6. Identify the type-check command if applicable (e.g., pyright, tsc, mypy)
    7. Note any pre-commit hooks or quality gates
    8. Check for code coverage tooling (e.g., pytest --cov, nyc, c8)
    Return a structured summary of all available commands."
- subagent_type: "Explore"
- model: "haiku"  # Token-efficient for discovery
```

Store discovered commands for use in later phases.

**Step 0.3: Run Baseline Tests**

**CRITICAL**: Run the full test suite BEFORE making any changes. Record the results as the baseline. Every subsequent test run must match or exceed this baseline.

```bash
# Run full test suite and record results
[DISCOVERED_TEST_COMMAND]
```

If tests already fail before refactoring, document the pre-existing failures. These are not caused by the refactoring and should remain unchanged (same tests fail with same errors).

### Phase 1: Scope Analysis

**Goal**: Understand the full impact of the refactoring before touching any code.

**Step 1.1: Start Phase 1**

```
TaskUpdate: { taskId: "2", status: "in_progress" }
```

**Step 1.2: Scope Analysis**

If the refactoring touches more than one file, or the caller list isn't obvious, spawn two Explore agents in parallel to map the scope. For a single-file refactor with an obvious blast radius, skip the subagents and just run a quick Grep for callers yourself — the goal is the same information, not the delegation ceremony.

```
Agent 1 - Dependency & Caller Analysis (Explore, Haiku):
  prompt: "Analyze dependencies and callers for the refactoring target:

    Refactoring target: [DESCRIBE TARGET CODE]

    1. Read the target code — understand its current structure and public API
    2. Find ALL callers and dependents using Grep:
       - Direct function/method calls
       - Import statements referencing the target
       - Type references (if applicable)
       - Configuration or dependency injection references
    3. Map the dependency graph:
       - What does the target depend on?
       - What depends on the target?
       - Are there circular dependencies?
    4. Identify the public API surface:
       - Which functions/methods/classes are called externally?
       - Which are internal-only (safe to change freely)?
    5. Note any dynamic references (string-based lookups, reflection, decorators)

    Return:
    - Complete caller list with file:line references
    - Dependency graph (what depends on what)
    - Public vs internal API surface
    - Risks: dynamic references, external consumers, serialization"
  subagent_type: "Explore"
  model: "haiku"

Agent 2 - Test Coverage Analysis (Explore, Haiku):
  prompt: "Analyze test coverage for the refactoring target:

    Refactoring target: [DESCRIBE TARGET CODE]

    1. Find ALL test files that test the target code:
       - Unit tests directly testing target functions/classes
       - Integration tests exercising the target indirectly
       - E2E tests that flow through the target
    2. For each test, note:
       - What specific behavior it verifies
       - Which code paths it exercises
       - Which inputs and edge cases it covers
    3. Identify GAPS in test coverage:
       - Functions/methods with no tests
       - Code branches not exercised (error paths, edge cases)
       - Public API methods without direct test coverage
    4. Check for test patterns:
       - Test fixtures and helpers available
       - Mocking patterns used in the project
       - Test naming conventions

    Return:
    - List of test files with what they cover
    - Coverage gaps requiring characterization tests
    - Test patterns and fixtures available for reuse
    - Risk areas: untested code paths that refactoring could break"
  subagent_type: "Explore"
  model: "haiku"
```

**Step 1.3: Synthesize Analysis**

After both agents complete, synthesize findings:
1. Identify which parts of the target are safe to refactor (well-tested, internal-only)
2. Identify which parts are risky (untested, public API, dynamic references)
3. Determine if characterization tests are needed (Phase 2)
4. Plan the order of incremental changes

**Step 1.4: Get Approval for Large Refactorings**

If the refactoring involves: changes to >5 files, modifications to public APIs, moving code between modules, or changes affecting external consumers, use `AskUserQuestion` to present the scope analysis and get approval before proceeding.

### Phase 2: Characterization Tests

**Goal**: Ensure sufficient test coverage exists to detect any behavioral change from the refactoring.

**Step 2.1: Start Phase 2**

```
TaskUpdate: { taskId: "3", status: "in_progress" }
```

**Step 2.2: Assess Coverage Needs**

Based on Phase 1 coverage analysis, determine which characterization tests are needed:

- **Well-tested code** (>80% path coverage): Skip to Phase 3
- **Partially tested** (some gaps): Add targeted characterization tests for untested paths
- **Poorly tested** (major gaps): Add comprehensive characterization tests before proceeding

**Step 2.3: Write Characterization Tests**

For each coverage gap identified:

1. **Read the target code** to understand current behavior (including edge cases)
2. **Write tests that capture current behavior exactly**:
   - Test the function/method with representative inputs
   - Test edge cases (null, empty, boundary values)
   - Test error paths (invalid inputs, failure modes)
   - Test return values AND side effects
3. **Run the characterization tests** — they must ALL pass against the current (pre-refactoring) code
4. **Name tests clearly**: Use prefix `test_char_` or equivalent to distinguish characterization tests from behavioral tests

```
Example characterization test (Python):
  def test_char_calculate_total_with_discount():
      """Characterization: captures current discount calculation behavior."""
      result = calculate_total(items=[100, 200], discount=0.1)
      assert result == 270.0  # Current behavior: discount applied to sum

  def test_char_calculate_total_empty_items():
      """Characterization: captures current behavior with empty input."""
      result = calculate_total(items=[], discount=0.1)
      assert result == 0.0
```

**IMPORTANT**: Characterization tests document CURRENT behavior, not desired behavior. If the current code has a quirk, the test captures that quirk. The refactoring must preserve it.

**Step 2.4: Verify Characterization Tests**

Run the full test suite (including new characterization tests). All must pass.

```bash
[DISCOVERED_TEST_COMMAND]
```

### Phase 3: Incremental Refactoring

**Goal**: Apply the refactoring in small, verified steps. Each step must pass all tests.

**Step 3.1: Start Phase 3**

```
TaskUpdate: { taskId: "4", status: "in_progress" }
```

**Step 3.2: Plan Incremental Steps**

Break the refactoring into the smallest possible independent steps. Each step should be:
- **Self-contained**: Makes sense on its own
- **Verifiable**: Tests can confirm behavior is preserved
- **Reversible**: Easy to revert if something breaks

Common refactoring step sequences (see `references/patterns.md` for details):

| Refactoring Type | Step Sequence |
|---|---|
| Extract method | 1. Create new method with copied code → 2. Test → 3. Replace original with call → 4. Test |
| Extract class | 1. Create class with methods → 2. Test → 3. Delegate from original → 4. Test → 5. Update callers → 6. Test |
| Rename | 1. Add new name alongside old → 2. Test → 3. Update callers → 4. Test → 5. Remove old name → 6. Test |
| Move function | 1. Copy to destination → 2. Test → 3. Re-export from source → 4. Update callers → 5. Test → 6. Remove source → 7. Test |
| Simplify conditional | 1. Extract condition to named variable/method → 2. Test → 3. Simplify logic → 4. Test |
| Remove duplication | 1. Identify shared pattern → 2. Extract shared code → 3. Test → 4. Replace first usage → 5. Test → 6. Replace next usage → 7. Test |

**Step 3.3: Execute Each Step**

For EACH incremental step:

1. **Make the change** — one small structural change using Edit tool
2. **Run tests immediately** — using discovered test command
   ```bash
   [DISCOVERED_TEST_COMMAND]
   ```
3. **If tests pass** — proceed to next step
4. **If tests fail** — STOP. Analyze the failure:
   - Is it a behavioral change? → Revert and find a smaller step
   - Is it a test that needs updating? → Only if the test was testing implementation details (not behavior)
   - Is it a pre-existing failure? → Compare with baseline from Phase 0

**CRITICAL**: Never skip the test run between steps. Never batch multiple steps before testing. The discipline of test-after-every-change is what makes refactoring safe.

**Step 3.4: Handle Complex Refactorings**

For refactorings spanning multiple files:

1. **Update the target first** — make the structural change in the primary file
2. **Update callers one at a time** — change each caller individually, testing after each
3. **Clean up** — remove old code, update imports, testing after each removal

For refactorings requiring temporary duplication:

1. **Create the new structure** alongside the old
2. **Test** — both old and new should work
3. **Migrate callers** one at a time to the new structure, testing after each
4. **Remove the old structure** once all callers are migrated
5. **Final test** — full suite

### Phase 4: Final Verification

**Step 4.1: Start Phase 4**

```
TaskUpdate: { taskId: "5", status: "in_progress" }
```

**Step 4.2: Run All Quality Checks**

Run all quality checks using discovered commands from Phase 0.

**Quality Gates Checklist**:
- [ ] Full test suite passes (matches or exceeds Phase 0 baseline)
- [ ] Characterization tests pass (behavior preserved)
- [ ] No new linting errors introduced
- [ ] No new type errors (if typed language)
- [ ] Code is cleaner/simpler than before (the purpose of refactoring)
- [ ] No accidental behavior changes
- [ ] No debug code, commented-out code, or TODO comments left behind
- [ ] All callers updated (no dangling references)

**If any check fails**: Fix the issue before proceeding. Do not commit broken code. Keep task as `in_progress` until all gates pass.

**Step 4.3: Review the Diff**

Read the complete diff to verify only intentional changes exist:

```bash
git diff
```

Look for:
- Unintended behavioral changes
- Leftover debug statements
- Unnecessary whitespace or formatting changes
- Missing import updates
- Orphaned code that should have been removed

### Phase 5: Final Commit

**Step 5.1: Start Phase 5**

```
TaskUpdate: { taskId: "6", status: "in_progress" }
```

**Step 5.2: Create Commit**

If the git-commit skill is available, use it. Otherwise, create a conventional commit manually:

```bash
git add [files modified]
git commit -m "refactor: [concise description of structural change]

- [What was restructured and why]
- [Key technique used: extract method, rename, simplify, etc.]
- [Impact: files changed, callers updated]

No behavioral changes."
```

**Commit message guidelines for refactoring:**
- Type: `refactor:` (always — this is a structural change, not a fix or feature)
- Subject: Describe WHAT was restructured
- Body: Explain WHY this improves the codebase
- Footer: Always include "No behavioral changes." to signal safety

### Phase 6: Summary Report

Report to the user with:
- **Refactoring performed**: What structural changes were made
- **Technique used**: Extract method, rename, simplify, move, etc.
- **Files modified**: List with brief description of changes
- **Behavior verification**: Test results before and after (matching)
- **Characterization tests added**: List of new tests if any
- **Code quality improvements**: Metrics if available (reduced duplication, fewer lines, better naming)
- **Commit info**: Commit hash and message

## Additional Resources

For detailed refactoring patterns, step sequences, and safety practices, see:
- [references/patterns.md](references/patterns.md) - Refactoring catalog with step-by-step procedures

## Important Notes

- **Always run Phase 0 first**: Never assume which tools are available
- **Tests before and after every change**: This is non-negotiable
- **Characterization tests for untested code**: Never refactor code without test coverage
- **One step at a time**: Never combine multiple refactoring operations
- **No behavior changes**: Refactoring changes structure only — if tests break, revert
- **Ask when unsure**: Better to clarify scope than to over-refactor
- **Minimal scope**: Refactor only what was requested — resist the urge to "improve" adjacent code
- **Document the change**: Clear commit message explaining what and why
