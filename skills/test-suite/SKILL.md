---
name: test-suite
description: "Generates a test suite by analyzing coverage gaps, prioritizing critical and untested code paths, then writing tests in parallel that match the project's existing patterns. Use when the user wants to write tests, add test coverage, generate test cases, improve testing, or analyze coverage gaps. Supports pytest, vitest, jest, and all major test frameworks. Not for debugging a specific failing test (use fix-bug)."
disable-model-invocation: false
argument-hint: "[target_files_or_modules] [--coverage] [--framework name]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
hooks:
  Stop:
    - hooks:
      - type: agent
        prompt: "Verify test suite generation is complete and correct:\n\n1. **Run tests**: Execute the test command discovered in Phase 0. ALL tests must pass (both new and existing).\n2. **Check coverage**: If a coverage command was discovered, run it and verify coverage improved or meets target.\n3. **Run linter**: Use the lint command discovered in Phase 0. No linting errors in test files.\n\nIf any check fails, report the failure clearly and return decision: block with reason. Only allow stopping when all tests pass and no regressions exist.\n\nUse commands discovered in Phase 0. If not available, discover them now from CLAUDE.md or project files (Makefile, package.json, pyproject.toml)."
        timeout: 180
---

# Test Suite Generator

Generate comprehensive test suites with coverage gap analysis and parallel test writing, following testing best practices across any project type and framework.

## Target

$ARGUMENTS

## Anti-Hallucination Guidelines

Test generation must be grounded in code you actually read and patterns you actually verified: a test for a method that doesn't exist, or a coverage number you didn't measure, is worse than no test at all:

1. Read the source file before writing any test for it.
2. Discover the test framework from the project itself (Step 0.2) rather than assuming pytest/vitest/jest.
3. Match the project's existing test style, fixtures, and conventions exactly.
4. Run every generated test: a test that has never executed is unverified.
5. Only reference methods, functions, and interfaces that exist in the code you read.
6. Every test needs a meaningful assertion, not just "does not throw."
7. Target untested code paths; don't duplicate coverage that already exists.
8. Any coverage percentage, baseline, or file path you report must come from a command you actually ran, never estimate or invent one, even under time pressure.

A Stop hook re-runs the discovered test/coverage/lint commands automatically before letting the session end (see frontmatter). Phase 4 below exists only to catch failures before that automatic gate fires, not to duplicate it.

## Scope: pick a track before starting

- **Small** (1-2 tests, a single file, a quick fix): skip task creation and the approval gate. Discover the test command (Step 0.2), write the tests, run them, done. Don't spin up Task Management ceremony for a two-test add.
- **Large** (multiple files/modules, a coverage push, anything needing parallel subagents): use the full Phase 0-5 workflow with Task Management below.

If unsure, default to Small and escalate only if the target turns out to span several modules.

**Portability:** No `Task`/`TaskCreate` tools in this environment? Skip task tracking and the parallel subagent fan-out in Phase 3: write the tests for each module group yourself, one group at a time. The phase structure is the contract; parallelism is just a speedup.

## Implementation Workflow (Large track)

### Phase 0: Project Discovery

**Step 0.1: Create Task Structure**

Create one task per phase, in order. `TaskCreate` returns the task's real ID: capture it and reuse that captured value everywhere below. Never assume IDs are literally `"1"`, `"2"`, etc.

```
discoverId = TaskCreate({ subject: "Phase 0: Discover project test workflow", description: "Identify test framework, coverage tools, and conventions", activeForm: "Discovering test workflow" })

gapsId = TaskCreate({ subject: "Phase 1: Analyze coverage gaps", description: "Run coverage, identify untested code, prioritize targets", activeForm: "Analyzing coverage gaps" })
TaskUpdate: { taskId: gapsId, addBlockedBy: [discoverId] }

planId = TaskCreate({ subject: "Phase 2: Create test plan", description: "Present test plan to user for approval", activeForm: "Creating test plan" })
TaskUpdate: { taskId: planId, addBlockedBy: [gapsId] }

genId = TaskCreate({ subject: "Phase 3: Generate tests in parallel", description: "Spawn subagents to write tests for each module group", activeForm: "Generating tests" })
TaskUpdate: { taskId: genId, addBlockedBy: [planId] }

verifyId = TaskCreate({ subject: "Phase 4: Quality verification", description: "Run all tests, check coverage improvement, lint", activeForm: "Verifying test quality" })
TaskUpdate: { taskId: verifyId, addBlockedBy: [genId] }

commitId = TaskCreate({ subject: "Phase 5: Final commit", description: "Commit tests with coverage summary", activeForm: "Committing tests" })
TaskUpdate: { taskId: commitId, addBlockedBy: [verifyId] }

TaskUpdate: { taskId: discoverId, status: "in_progress" }
```

**Step 0.2: Discover Test Workflow**

Use a Haiku-powered Explore agent for token-efficient discovery:

```
Use Task tool with Explore agent:
- prompt: "Discover the testing workflow for this project:
    1. Read CLAUDE.md if it exists - extract testing conventions and commands
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test framework:
       - Python: pytest, unittest, nose2
       - JavaScript/TypeScript: vitest, jest, mocha, playwright, cypress
       - Other: go test, cargo test, etc.
    4. Identify the test command (e.g., make test, npm test, pytest, bun test)
    5. Identify the coverage command (e.g., pytest --cov, vitest --coverage, jest --coverage, make coverage)
    6. Identify the lint command
    7. Find existing test directory structure and naming conventions
    8. Look at 2-3 existing test files to understand:
       - Import patterns and test utilities
       - Fixture/mock patterns used
       - Assertion style (assert, expect, etc.)
       - Test organization (describe/it vs test functions)
       - Setup/teardown patterns
       - Factory or fixture patterns
    9. Check for test configuration files:
       - pytest.ini, conftest.py, setup.cfg [tool.pytest]
       - vitest.config.ts, jest.config.js
       - .nycrc, c8 config, istanbul config
    10. Note any test-related CI/CD configuration
    Return a structured summary of all testing infrastructure."
- subagent_type: "Explore"
- model: "haiku"
```

Store discovered commands and patterns for use in later phases.

**Step 0.3: Complete Phase 0**

```
TaskUpdate: { taskId: discoverId, status: "completed" }
TaskList  # Check that the Phase 1 task (gapsId) is now unblocked
```

### Phase 1: Coverage Gap Analysis

**Goal**: Identify what code lacks test coverage and prioritize test generation targets.

**Step 1.1: Start Phase 1**

```
TaskUpdate: { taskId: gapsId, status: "in_progress" }
```

**Step 1.2: Establish Coverage Baseline**

Run the discovered coverage command to get the current state:

```bash
# Examples (use the ACTUAL discovered command):
pytest --cov --cov-report=term-missing
vitest --coverage
jest --coverage
make coverage
```

Capture the output. If no coverage tooling exists, use an Explore agent to manually identify untested code:

```
Use Task tool with Explore agent:
- prompt: "Analyze test coverage gaps for this project:
    1. List all source files/modules in the project (exclude test files, configs, migrations)
    2. List all test files
    3. For each source file, check if a corresponding test file exists
    4. For files with tests, skim the test file to estimate which functions/methods are tested
    5. Identify files with no tests at all
    6. Identify complex files (many functions, classes, branching logic) that likely need more tests
    Return a structured report:
    - Files with NO test coverage (highest priority)
    - Files with PARTIAL coverage (functions/methods missing tests)
    - Files with GOOD coverage (low priority)
    - Overall estimated coverage percentage"
- subagent_type: "Explore"
- model: "haiku"
```

**Step 1.3: Prioritize Test Targets**

Rank files/modules for test generation by:
1. **Critical business logic** - Authentication, payments, data processing
2. **Untested code** - Files with zero test coverage
3. **Complex code** - High cyclomatic complexity, many branches
4. **Recently changed** - Code modified in recent commits (use `git log --oneline -20 --name-only`)
5. **Error-prone areas** - Code with known bugs or frequent changes

If the user specified target files/modules, prioritize those. Otherwise, use the ranking above.

**Step 1.4: Complete Phase 1**

```
TaskUpdate: { taskId: gapsId, status: "completed" }
TaskList  # Check that the Phase 2 task (planId) is now unblocked
```

### Phase 2: Test Plan (User Approval)

**Goal**: Present a test plan for user review before generating tests.

**Step 2.1: Start Phase 2**

```
TaskUpdate: { taskId: planId, status: "in_progress" }
```

**Step 2.2: Present Test Plan**

Use `AskUserQuestion` to present the plan and get approval:

```
AskUserQuestion:
  question: "Here's the test generation plan based on coverage analysis. Which approach do you prefer?"
  header: "Test Plan"
  options:
    - label: "Full coverage (Recommended)"
      description: "Generate tests for all [N] identified gaps: [list of modules]. Estimated [M] test files."
    - label: "Critical paths only"
      description: "Focus on [top modules] with highest business impact. Estimated [K] test files."
    - label: "Specific modules"
      description: "Let me specify which modules to test."
```

No `AskUserQuestion` tool available? Present the same plan as plain text and wait for the user's reply before moving on to Phase 3.

The plan should include for each target:
- **File/module path** being tested
- **Functions/methods** to cover
- **Test types**: Unit tests, integration tests, edge cases
- **Estimated test count** per file
- **Test file location** following project conventions

**Step 2.3: Complete Phase 2**

```
TaskUpdate: { taskId: planId, status: "completed" }
TaskList  # Check that the Phase 3 task (genId) is now unblocked
```

### Phase 3: Parallel Test Generation

**Goal**: Generate tests efficiently using parallel subagents, one per module or file group.

**Step 3.1: Start Phase 3**

```
TaskUpdate: { taskId: genId, status: "in_progress" }
```

**Step 3.2: Create Parallel Subagent Tasks**

Group approved test targets into logical units (by module, feature area, or related files) and create a child task for each, capturing each returned ID:

```
# Example: 3 module groups to test in parallel
authChildId = TaskCreate({ subject: "Write tests for auth module", description: "Generate unit tests for src/auth/ (login, register, token management)", activeForm: "Writing auth module tests", metadata: { parent: genId, module: "auth" } })

userChildId = TaskCreate({ subject: "Write tests for user service", description: "Generate unit tests for src/services/user.py (CRUD, validation)", activeForm: "Writing user service tests", metadata: { parent: genId, module: "user-service" } })

apiChildId = TaskCreate({ subject: "Write tests for API routes", description: "Generate integration tests for src/routes/ (endpoints, middleware)", activeForm: "Writing API route tests", metadata: { parent: genId, module: "api-routes" } })

# Phase 4 (Verification) blocked by ALL parallel child tasks
TaskUpdate: { taskId: verifyId, addBlockedBy: [authChildId, userChildId, apiChildId] }
```

**Step 3.3: Spawn Parallel Subagents**

For each module group, spawn a Sonnet subagent using the Task tool:

**Subagent Instructions Template:**

```
Generate comprehensive tests for [MODULE/FILES].

Read these source files FIRST to understand the actual code:
[LIST OF SOURCE FILES TO READ]

Then read these existing test files for patterns to follow:
[LIST OF EXISTING TEST FILES]

Project testing conventions (discovered in Phase 0):
- Test framework: [FRAMEWORK]
- Test command: [COMMAND]
- Test file naming: [PATTERN e.g., test_*.py, *.test.ts, *.spec.js]
- Test directory: [PATH]
- Fixture patterns: [DESCRIBE]
- Mock patterns: [DESCRIBE]
- Assertion style: [DESCRIBE]

Requirements:
1. Follow the EXACT test patterns from existing test files: same imports, fixtures, assertion style
2. Cover public functions/methods: happy path, edge cases (empty/boundary/null), error paths, and branch coverage
3. Mock external dependencies (databases, APIs, file system) appropriately
4. Follow the Test Quality Principles below

After writing tests:
1. Run the test command to verify ALL tests pass
2. Fix any failures before reporting completion
3. Report: files created, test count, what is covered

Do NOT commit - the main agent handles commits.
```

**Model Selection:**
- **Use Sonnet (default)** for test generation (requires code understanding and writing)
- **Use Haiku** only for pure exploration tasks (not applicable in Phase 3)

**Parallelization Strategy:**
- Spawn all independent module subagents simultaneously
- Each subagent writes tests for its assigned module group
- Subagents run tests locally to verify before completion

**Step 3.4: Review Subagent Output**

After each subagent completes:
1. Review the generated test files
2. Verify the tests follow project conventions
3. Update the corresponding child task: `TaskUpdate: { taskId: <that child's captured ID>, status: "completed" }`

**Step 3.5: Complete Phase 3**

```
# After all subagent tasks complete
TaskUpdate: { taskId: genId, status: "completed" }
TaskList  # Verify Phase 4 (verifyId) is now unblocked
```

### Phase 4: Quality Verification

**Goal**: Catch failures before the Stop hook's automatic final check.

Run the discovered test command once:

```bash
# Use the ACTUAL discovered command, e.g.:
make test
pytest
npm test
bun test
```

If a test fails, figure out whether it's a new test (fix the test, it made a wrong assumption about behavior) or an existing test (the new code introduced a side effect, investigate and fix). Re-run until everything passes.

That's it: the Stop hook already re-runs tests, coverage, and lint automatically before the session ends, so don't duplicate a full separate coverage-and-lint pass here. This step exists only so failures surface while you're still working, not at the very last gate.

```
TaskUpdate: { taskId: verifyId, status: "completed" }
TaskList  # Check that the Phase 5 task (commitId) is now unblocked
```

### Phase 5: Final Commit

**Step 5.1: Start Phase 5**

```
TaskUpdate: { taskId: commitId, status: "in_progress" }
```

**Step 5.2: Create Commit**

Use the `cc-arsenal:git-commit` skill to create the commit where available; otherwise create a conventional commit manually, using the actual coverage numbers from the command you ran in Phase 4/Phase 1, never an estimate:

```bash
git add [test files created/modified]
git commit -m "test: add comprehensive tests for [modules]

- [N] test files, [M] test cases added
- Coverage: [X]% → [Y]% (+[diff]%)
- Covers: [brief list of modules/features tested]
- Frameworks: [test framework used]"
```

**Step 5.3: Complete Phase 5 and Test Generation**

```
TaskUpdate: { taskId: commitId, status: "completed" }
TaskList  # Show final status - all tasks should be completed
```

## Output Summary

Provide a summary including:
- **Tests generated**: Number of test files and test cases
- **Coverage improvement**: Baseline → new coverage percentage (from the commands actually run, not estimated)
- **Modules covered**: List of modules/files that received new tests
- **Test types**: Unit, integration, edge cases breakdown
- **Remaining gaps**: What still lacks coverage and recommendations
- **Commit**: Reference to the commit created

## Test Quality Principles

Generated tests must follow these principles:

1. **Arrange-Act-Assert**: Clear structure in every test
2. **Single responsibility**: Each test verifies one behavior
3. **Descriptive names**: Test name explains the scenario and expected outcome
4. **Independence**: Tests do not depend on execution order or shared state
5. **Deterministic**: Same result every time, no flaky tests
6. **Fast**: Unit tests run quickly; minimize I/O and external calls
7. **Readable**: Tests serve as documentation for the code under test
8. **Maintainable**: Avoid testing implementation details; test behavior and contracts
9. **Lean coverage**: Over-testing is the failure mode in the other direction: skip trivial getters, pure pass-throughs, and framework-guaranteed behavior. Don't add a snapshot test or an assert-nothing test just to move a coverage number. The one exception: never skip a test for a security, validation, or data-loss path just because it's tedious to set up, that risk is always worth the test.

## Additional Resources

- [references/framework-patterns.md](references/framework-patterns.md) - pytest, vitest/jest, Go, and Rust idioms (file layout, naming, fixtures, mocking, common anti-patterns). Load it when writing tests for a framework whose conventions you're not confident about, or when the Phase 0 discovery didn't surface enough existing test files to infer the pattern yourself.

## Important Notes

- Run Phase 0 first, every time, never assume which test framework a project uses.
- Match the project's existing test style exactly; don't introduce a new convention alongside the old one.
- Coverage is a guide, not a goal: a meaningful test beats a percentage bump.
- All existing tests must keep passing; a new test that breaks an old one is a regression, not progress.
- When scope or approach is genuinely unclear, ask via `AskUserQuestion` (or its text fallback) rather than guessing.
- Prefer one clean commit with all tests over many small commits.
