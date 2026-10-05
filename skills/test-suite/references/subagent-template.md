# Subagent and Task Boilerplate

Task-tool scaffolding, Explore prompts and the test-writer subagent template for the Large track in `SKILL.md`. Without `Task`/`TaskCreate` tools, skip all of this and do the work inline, one module group at a time.

## Contents

- [Task structure](#task-structure)
- [Discovery prompt](#discovery-prompt)
- [Gap-analysis prompt](#gap-analysis-prompt)
- [Parallel child tasks](#parallel-child-tasks)
- [Test-writer subagent template](#test-writer-subagent-template)
- [Model selection and parallelism](#model-selection-and-parallelism)

## Task structure

Create one task per phase, in order. `TaskCreate` returns the task's real ID: capture it and reuse that value everywhere. Never assume IDs are literally `"1"`, `"2"`, etc.

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

At each phase boundary, mark that phase's task `completed`, run `TaskList` to confirm the next one is unblocked, then mark it `in_progress`.

## Discovery prompt

Phase 0. Use a Haiku-powered Explore agent for token-efficient discovery:

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

## Gap-analysis prompt

Phase 1, only when no coverage tooling exists:

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

The percentage this returns is a rough estimate: never report it as measured coverage.

## Parallel child tasks

Phase 3. Group approved targets into logical units (module, feature area, related files) and create a child task for each, capturing each returned ID:

```
authChildId = TaskCreate({ subject: "Write tests for auth module", description: "Generate unit tests for src/auth/ (login, register, token management)", activeForm: "Writing auth module tests", metadata: { parent: genId, module: "auth" } })

userChildId = TaskCreate({ subject: "Write tests for user service", description: "Generate unit tests for src/services/user.py (CRUD, validation)", activeForm: "Writing user service tests", metadata: { parent: genId, module: "user-service" } })

# Phase 4 is blocked by ALL parallel child tasks
TaskUpdate: { taskId: verifyId, addBlockedBy: [authChildId, userChildId] }
```

After each subagent finishes, review its test files against project conventions, then `TaskUpdate: { taskId: <that child's captured ID>, status: "completed" }`.

## Test-writer subagent template

One subagent per module group. Fill every bracket from Phase 0 discovery; leave none unresolved.

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
4. Follow the Test Quality Principles in SKILL.md

After writing tests:
1. Run the test command to verify ALL tests pass
2. Fix any failures before reporting completion
3. Report: files created, test count, what is covered

Do NOT commit - the main agent handles commits.
```

## Model selection and parallelism

- Sonnet (default) for test generation: it needs code understanding and writing.
- Haiku only for pure exploration (Phase 0 and the Phase 1 fallback), never for writing tests.
- Spawn all independent module subagents at once; give each its own files so no two write the same path.
- Each subagent runs its tests before reporting; the main agent still runs the full suite in Phase 4.
