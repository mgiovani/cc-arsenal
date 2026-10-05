---
name: test-suite
description: "Generates a test suite by analyzing coverage gaps, prioritizing critical and untested code paths, then writing tests in parallel that match the project's existing patterns. Use when the user wants to write tests, add test coverage, generate test cases, improve testing, or analyze coverage gaps. Supports pytest, vitest, jest, and all major test frameworks. Not for debugging a specific failing test (use fix-bug)."
disable-model-invocation: false
argument-hint: "[target_files_or_modules] [--coverage] [--framework name]"
hooks:
  Stop:
    - hooks:
      - type: agent
        prompt: "Verify test suite generation is complete and correct:\n\n1. **Run tests**: Execute the test command discovered in Phase 0. ALL tests must pass (both new and existing).\n2. **Check coverage**: If a coverage command was discovered, run it and verify coverage improved or meets target.\n3. **Run linter**: Use the lint command discovered in Phase 0. No linting errors in test files.\n\nIf any check fails, report the failure clearly and return decision: block with reason. Only allow stopping when all tests pass and no regressions exist.\n\nUse commands discovered in Phase 0. If not available, discover them now from CLAUDE.md or project files (Makefile, package.json, pyproject.toml)."
        timeout: 180
metadata:
  summary: "Generate test suites by analyzing coverage gaps and writing tests that match project conventions"
---

# Test Suite Generator

Generate comprehensive test suites with coverage gap analysis and parallel test writing, following testing best practices across any project type and framework.

## Target

$ARGUMENTS

## Anti-hallucination guidelines

Test generation must be grounded in code you actually read and patterns you actually verified: a test for a method that doesn't exist, or a coverage number you didn't measure, is worse than no test at all:

1. Read the source file before writing any test for it.
2. Discover the test framework from the project itself (Phase 0) rather than assuming pytest/vitest/jest.
3. Match the project's existing test style exactly, down to its fixtures and other conventions.
4. Run every generated test: a test that has never executed is unverified.
5. Only reference methods and functions that exist in the code you read, along with their real interfaces.
6. Every test needs a meaningful assertion, not just "does not throw."
7. Target untested code paths; don't duplicate coverage that already exists.
8. Any coverage percentage or baseline you report must come from a command you actually ran; the same goes for any file path. Never estimate or invent one, even under time pressure.

A Stop hook re-runs the discovered test/coverage/lint commands automatically before letting the session end (see frontmatter). Phase 4 below exists only to catch failures before that automatic gate fires, not to duplicate it.

## Scope: pick a track before starting

- Small (1-2 tests, a single file, a quick fix): skip task creation and the approval gate. Discover the test command (Phase 0), write the tests, run them, done. Don't spin up task ceremony for a two-test add.
- Large (multiple files/modules, a coverage push, anything needing parallel subagents): use the full Phase 0-5 workflow with the checklist below.

If unsure, default to Small and escalate only if the target turns out to span several modules.

Portability: No `Task`/`TaskCreate` tools in this environment? Skip task tracking and the parallel subagent fan-out in Phase 3: do discovery and gap analysis yourself with Read/Grep/Glob, and write the tests for each module group yourself, one group at a time. The phase structure is the contract; parallelism is just a speedup. All Task, Explore and subagent boilerplate lives in [references/subagent-template.md](references/subagent-template.md).

## Implementation Workflow (Large track)

Copy this checklist and tick it as you go:

```
- [ ] Phase 0: discover test, coverage and lint commands and 2-3 existing test files
- [ ] Phase 1: run coverage baseline, rank targets
- [ ] Phase 2: user approves the test plan (no approval -> do not start Phase 3)
- [ ] Phase 3: write tests per module group
      - new tests fail for the wrong reason (import error, wrong interface) -> back to the Phase 3 writing step, re-read the source
      - existing suite breaks -> stop, find the side effect, report before going on
- [ ] Phase 4: run the full test command (max 3 fix rounds, then report what still fails)
- [ ] Phase 5: commit with measured coverage numbers
```

### Phase 0: Project Discovery

Create the phase tasks per "Task structure" in [references/subagent-template.md](references/subagent-template.md#task-structure), then discover the test workflow with the Haiku Explore prompt in [Discovery prompt](references/subagent-template.md#discovery-prompt). Without subagent tools, read CLAUDE.md, the task runner files and 2-3 existing test files yourself.

Store the discovered test, coverage and lint commands plus the style patterns for later phases.

### Phase 1: Coverage Gap Analysis

Goal: Identify what code lacks test coverage and prioritize test generation targets.

Run the discovered coverage command to get the current state:

```bash
# Examples (use the ACTUAL discovered command):
pytest --cov --cov-report=term-missing
vitest --coverage
jest --coverage
make coverage
```

Capture the output. If no coverage tooling exists, map untested code with the [Gap-analysis prompt](references/subagent-template.md#gap-analysis-prompt), or by comparing source and test file lists yourself.

Rank files/modules for test generation by:

| Priority | Signal |
| --- | --- |
| 1 | Critical business logic: authentication, payments, data processing |
| 2 | Untested code: files with zero test coverage |
| 3 | Complex code: high cyclomatic complexity, many branches |
| 4 | Recently changed: code modified in recent commits (use `git log --oneline -20 --name-only`) |
| 5 | Error-prone areas: code with known bugs or frequent changes |

If the user specified target files/modules, prioritize those. Otherwise, use the ranking above.

### Phase 2: Test Plan (User Approval)

Goal: Present a test plan for user review before generating tests.

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

The plan should include, for each target:

| Field | Content |
| --- | --- |
| File/module path | The path being tested |
| Functions/methods | Which ones to cover |
| Test types | Unit tests, integration tests, edge cases |
| Estimated test count | Per file |
| Test file location | Following project conventions |

### Phase 3: Parallel Test Generation

Goal: Write tests for each approved module group, in parallel where subagents exist.

Group approved targets into logical units (module, feature area, related files). For each group, create a child task ([Parallel child tasks](references/subagent-template.md#parallel-child-tasks)) and spawn a Sonnet subagent with the [Test-writer subagent template](references/subagent-template.md#test-writer-subagent-template), spawning independent groups at once. Review each subagent's test files against project conventions as it finishes.

No subagent tool? Take the groups one at a time and write the tests yourself, applying the same template requirements: read the source and existing tests first, follow the Test Quality Principles, run the test command after each group.

### Phase 4: Quality Verification

Goal: Catch failures before the Stop hook's automatic final check.

Run the discovered test command once:

```bash
# Use the ACTUAL discovered command, e.g.:
make test
pytest
npm test
bun test
```

If a test fails, figure out whether it's a new test (fix the test, it made a wrong assumption about behavior) or an existing test (the new code introduced a side effect, investigate and fix). Re-run until everything passes, at most 3 rounds; then report what still fails instead of looping.

That's it: the Stop hook already re-runs tests, coverage, and lint automatically before the session ends, so don't duplicate a full separate coverage-and-lint pass here. This step exists only so failures surface while you're still working, not at the very last gate.

### Phase 5: Final Commit

Use the `cc-arsenal:git-commit` skill to create the commit where available; otherwise create a conventional commit manually, using the actual coverage numbers from the command you ran in Phase 4/Phase 1, never an estimate:

```bash
git add [test files created/modified]
git commit -m "test: add comprehensive tests for [modules]

- [N] test files, [M] test cases added
- Coverage: [X]% → [Y]% (+[diff]%)
- Covers: [brief list of modules/features tested]
- Frameworks: [test framework used]"
```

## Output Summary

Provide a summary including:

| Field | Content |
| --- | --- |
| Tests generated | Number of test files and test cases |
| Coverage improvement | Baseline to new coverage percentage (from the commands actually run, not estimated) |
| Modules covered | List of modules/files that received new tests |
| Test types | Unit, integration, edge cases breakdown |
| Remaining gaps | What still lacks coverage and recommendations |
| Commit | Reference to the commit created |

## Test Quality Principles

Generated tests must follow these principles:

| Principle | Detail |
| --- | --- |
| Arrange-Act-Assert | Clear structure in every test |
| Single responsibility | Each test verifies one behavior |
| Descriptive names | Test name explains the scenario and expected outcome |
| Independence | Tests do not depend on execution order or shared state |
| Deterministic | Same result every time, no flaky tests |
| Fast | Unit tests run quickly; minimize I/O and external calls |
| Readable | Tests serve as documentation for the code under test |
| Maintainable | Avoid testing implementation details; test behavior and contracts |
| Lean coverage | Over-testing is the failure mode in the other direction. Skip trivial getters and pure pass-throughs, as well as framework-guaranteed behavior. Don't add a snapshot test or an assert-nothing test just to move a coverage number. The one exception: never skip a test for a security or validation path, or one touching data loss, just because it's tedious to set up; that risk is always worth the test. |

## Additional Resources

- [references/subagent-template.md](references/subagent-template.md) - Task setup, Explore prompts and the test-writer subagent template for the Large track.
- [references/framework-patterns.md](references/framework-patterns.md) - pytest, vitest/jest, Go, and Rust idioms (file layout, naming, fixtures, mocking, common anti-patterns). Load it when writing tests for a framework whose conventions you're not confident about, or when the Phase 0 discovery didn't surface enough existing test files to infer the pattern yourself.

## Important Notes

- Run Phase 0 first, every time, never assume which test framework a project uses.
- Match the project's existing test style exactly; don't introduce a new convention alongside the old one.
- Coverage is a guide, not a goal: a meaningful test beats a percentage bump.
- All existing tests must keep passing; a new test that breaks an old one is a regression, not progress.
- When scope or approach is genuinely unclear, ask via `AskUserQuestion` (or its text fallback) rather than guessing.
- Prefer one clean commit with all tests over many small commits.
