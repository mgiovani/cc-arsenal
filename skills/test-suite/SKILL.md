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

**CRITICAL**: Test generation must be based on ACTUAL code and VERIFIED project patterns:
1. **Read source code first** - Never write tests for code that has not been read and understood
2. **Discover test framework** - Do NOT assume pytest, vitest, jest, or any specific framework
3. **Follow existing patterns** - Match the project's existing test style, fixtures, and conventions exactly
4. **Verify tests run** - All generated tests must actually pass when executed
5. **No invented APIs** - Only test methods, functions, and interfaces that actually exist in the code
6. **Real assertions** - Every test must have meaningful assertions, not just "does not throw"
7. **Coverage-driven** - Focus on untested code paths, not duplicating existing coverage

## Quality Gates

This skill includes automatic verification before completion:

### Test Verification (Stop Hook)

When attempting to stop working, an automated verification agent runs to ensure quality:

**Verification Steps:**
1. **Test Execution**: Runs discovered test command. All tests (new and existing) must pass.
2. **Coverage Check**: If coverage tooling exists, verifies improvement over baseline.
3. **Lint Check**: Ensures test files pass linting rules.

**Behavior:**
- All checks pass: Test generation marked complete
- Any check fails: Completion blocked, error details provided, Claude continues fixing
- Commands not found: Hook discovers them from CLAUDE.md or project files

**Example blocked completion:**
```
Test verification failed:

Tests: FAILED (2 new tests failing)
  - test_user_service_create: AttributeError: 'UserService' has no method 'create_user'
  - test_parse_config_empty: Expected ValueError, got None

Coverage: IMPROVED (72% → 78%)
Lint: PASSED

Cannot complete until all tests pass. Fix the failing tests.
```

## Task Management

This skill uses Claude Code's Task Management System to track test generation progress with dependency-aware task tracking.

**When to Use Tasks:**
- Generating tests for multiple files or modules
- Coverage improvement across a codebase
- Complex test generation requiring parallel subagents

**When to Skip Tasks:**
- Adding 1-2 tests to a single file
- Simple unit test additions
- Quick test fixes

## Implementation Workflow

### Phase 0: Project Discovery (REQUIRED)

**Step 0.1: Create Task Structure**

Before generating tests, create the dependency-aware task structure:

```
TaskCreate:
  subject: "Phase 0: Discover project test workflow"
  description: "Identify test framework, coverage tools, and conventions"
  activeForm: "Discovering test workflow"

TaskCreate:
  subject: "Phase 1: Analyze coverage gaps"
  description: "Run coverage, identify untested code, prioritize targets"
  activeForm: "Analyzing coverage gaps"

TaskCreate:
  subject: "Phase 2: Create test plan"
  description: "Present test plan to user for approval"
  activeForm: "Creating test plan"

TaskCreate:
  subject: "Phase 3: Generate tests in parallel"
  description: "Spawn subagents to write tests for each module group"
  activeForm: "Generating tests"

TaskCreate:
  subject: "Phase 4: Quality verification"
  description: "Run all tests, check coverage improvement, lint"
  activeForm: "Verifying test quality"

TaskCreate:
  subject: "Phase 5: Final commit"
  description: "Commit tests with coverage summary"
  activeForm: "Committing tests"

# Set up strict sequential chain
TaskUpdate: { taskId: "2", addBlockedBy: ["1"] }
TaskUpdate: { taskId: "3", addBlockedBy: ["2"] }
TaskUpdate: { taskId: "4", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "5", addBlockedBy: ["4"] }
TaskUpdate: { taskId: "6", addBlockedBy: ["5"] }

# Start first task
TaskUpdate: { taskId: "1", status: "in_progress" }
```

**Step 0.2: Discover Test Workflow**

Use Haiku-powered Explore agent for token-efficient discovery:

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
TaskUpdate: { taskId: "1", status: "completed" }
TaskList  # Check that Task 2 is now unblocked
```

### Phase 1: Coverage Gap Analysis

**Goal**: Identify what code lacks test coverage and prioritize test generation targets.

**Step 1.1: Start Phase 1**

```
TaskUpdate: { taskId: "2", status: "in_progress" }
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
TaskUpdate: { taskId: "2", status: "completed" }
TaskList  # Check that Task 3 is now unblocked
```

### Phase 2: Test Plan (User Approval)

**Goal**: Present a test plan for user review before generating tests.

**Step 2.1: Start Phase 2**

```
TaskUpdate: { taskId: "3", status: "in_progress" }
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

The plan should include for each target:
- **File/module path** being tested
- **Functions/methods** to cover
- **Test types**: Unit tests, integration tests, edge cases
- **Estimated test count** per file
- **Test file location** following project conventions

**Step 2.3: Complete Phase 2**

```
TaskUpdate: { taskId: "3", status: "completed" }
TaskList  # Check that Task 4 is now unblocked
```

### Phase 3: Parallel Test Generation

**Goal**: Generate tests efficiently using parallel subagents, one per module or file group.

**Step 3.1: Start Phase 3**

```
TaskUpdate: { taskId: "4", status: "in_progress" }
```

**Step 3.2: Create Parallel Subagent Tasks**

Group approved test targets into logical units (by module, feature area, or related files) and create a child task for each:

```
# Example: 3 module groups to test in parallel
TaskCreate:
  subject: "Write tests for auth module"
  description: "Generate unit tests for src/auth/ (login, register, token management)"
  activeForm: "Writing auth module tests"
  metadata: { parent: "4", module: "auth" }

TaskCreate:
  subject: "Write tests for user service"
  description: "Generate unit tests for src/services/user.py (CRUD, validation)"
  activeForm: "Writing user service tests"
  metadata: { parent: "4", module: "user-service" }

TaskCreate:
  subject: "Write tests for API routes"
  description: "Generate integration tests for src/routes/ (endpoints, middleware)"
  activeForm: "Writing API route tests"
  metadata: { parent: "4", module: "api-routes" }

# Phase 5 (Verification) blocked by ALL parallel tasks
TaskUpdate: { taskId: "5", addBlockedBy: ["child-task-ids"] }
```

**Step 3.3: Spawn Parallel Subagents**

For each module group, spawn a Sonnet subagent using the Task tool:

**Subagent Instructions Template:**

```
Generate comprehensive tests for [MODULE/FILES].

IMPORTANT: Read these source files FIRST to understand the actual code:
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
1. Follow the EXACT test patterns from existing test files
2. Use the same import patterns, fixtures, and assertion style
3. Test coverage targets:
   - All public functions and methods
   - Happy path (normal inputs and expected outputs)
   - Edge cases (empty inputs, boundary values, null/undefined)
   - Error paths (invalid inputs, exceptions, error handling)
   - Branch coverage (if/else, switch, ternary paths)
4. Use descriptive test names that explain WHAT is being tested and EXPECTED behavior
5. Keep tests independent - no shared mutable state between tests
6. Mock external dependencies (databases, APIs, file system) appropriately
7. Do NOT test private/internal implementation details
8. Do NOT add unnecessary comments - test names should be self-documenting

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
3. Update the corresponding child task: `TaskUpdate: { taskId: "child-id", status: "completed" }`

**Step 3.5: Complete Phase 3**

```
# After all subagent tasks complete
TaskUpdate: { taskId: "4", status: "completed" }
TaskList  # Verify Phase 5 is now unblocked
```

### Phase 4: Quality Verification

**Goal**: Verify all tests pass together, coverage improved, and no regressions.

**Step 4.1: Start Phase 4**

```
TaskUpdate: { taskId: "5", status: "in_progress" }
```

**Step 4.2: Run Full Test Suite**

Execute the discovered test command to run ALL tests (new and existing):

```bash
# Use the ACTUAL discovered command, e.g.:
make test
pytest
npm test
bun test
```

**ALL tests must pass.** If any test fails:
1. Identify whether the failure is in a new test or an existing test
2. If new test fails: Fix the test (wrong assumption about code behavior)
3. If existing test fails: The new test introduced a side effect — investigate and fix
4. Re-run until all tests pass

**Step 4.3: Verify Coverage Improvement**

Run the coverage command and compare against the Phase 1 baseline:

```bash
# Use the ACTUAL discovered coverage command, e.g.:
pytest --cov --cov-report=term-missing
vitest --coverage
jest --coverage
make coverage
```

Record:
- **Baseline coverage**: [X]% (from Phase 1)
- **New coverage**: [Y]%
- **Improvement**: +[Y-X]%
- **Uncovered lines remaining**: [summary of what still lacks coverage]

**Step 4.4: Lint Test Files**

Run the discovered lint command on test files:

```bash
# Use the ACTUAL discovered lint command
make lint
ruff check tests/
npm run lint
```

Fix any linting errors in the generated test files.

**Step 4.5: Complete Phase 4**

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
git add [test files created/modified]
git commit -m "test: add comprehensive tests for [modules]

- [N] test files, [M] test cases added
- Coverage: [X]% → [Y]% (+[diff]%)
- Covers: [brief list of modules/features tested]
- Frameworks: [test framework used]"
```

**Step 5.3: Complete Phase 5 and Test Generation**

```
TaskUpdate: { taskId: "6", status: "completed" }
TaskList  # Show final status - all tasks should be completed
```

## Output Summary

Provide a summary including:
- **Tests generated**: Number of test files and test cases
- **Coverage improvement**: Baseline → new coverage percentage
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
9. **Lean coverage**: Over-testing is the failure mode in the other direction — skip trivial getters, pure pass-throughs, and framework-guaranteed behavior. Don't add a snapshot test or an assert-nothing test just to move a coverage number. The one exception: never skip a test for a security, validation, or data-loss path just because it is tedious to set up — that risk is always worth the test.

## Additional Resources

For framework-specific test patterns, fixtures, and examples, see:
- [references/framework-patterns.md](references/framework-patterns.md) - Patterns for pytest, vitest, jest, Go, Rust, and more

## Important Notes

- **Always run Phase 0 first** - Never assume which test framework is available
- **Follow existing patterns** - Match the project's test style exactly
- **Coverage is a guide, not a goal** - Meaningful tests matter more than 100% coverage
- **No regressions** - All existing tests must continue to pass
- **Ask when unsure** - Use AskUserQuestion to clarify test scope or approach
- **Commit strategy** - Prefer one clean commit with all tests over many small commits
