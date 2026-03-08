---
name: forge-qa
description: Validate story implementation against acceptance criteria and produce QA reports.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: <story-path>
allowed-tools: Read, Write, Edit, Bash(make *), Bash(pytest *), Bash(npm *), Bash(bun
  *), Grep, Glob, Task, TaskCreate, TaskUpdate
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify QA validation is complete before stopping:\n\n1. Check that\
        \ a QA report file exists at docs/qa-reports/<story-id>.md\n2. Verify the\
        \ report contains:\n   - Overall status (PASS / FAIL / PARTIAL)\n   - Acceptance\
        \ Criteria Results table (every AC from the story listed)\n   - Recommendation\
        \ (APPROVE or NEEDS WORK with specifics)\n3. If the overall status is FAIL:\
        \ ensure the stop is intentional (QA found failures, which is valid output)\n\
        4. Run the test suite and verify that test count matches what's reported in\
        \ the QA report\n\nBlock only if the QA report is missing or incomplete (not\
        \ if it says FAIL \u2014 that's a valid outcome).\n"
      timeout: 60
---

# Forge QA

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Story Quality Assurance

Validate a completed story implementation against its acceptance criteria, test coverage, and definition of done. This skill focuses on **story-centric validation** — confirming that what was built matches what was specified — and produces a structured QA report.

## Anti-Hallucination Guidelines

**CRITICAL**: QA validation must be grounded in actual evidence:
1. **Read before claiming** — Never assert an AC passes or fails without examining the implementation
2. **Evidence-based results** — Every AC verdict must cite specific files, functions, or test names
3. **No assumed coverage** — Verify tests actually exist and pass; do not assume they do
4. **Exact references** — Use `file:line` format for every finding
5. **Honest partial credit** — Report "PARTIAL" when an AC is partly met, not PASS or FAIL
6. **Regression scope** — Check that changed code did not silently break existing functionality
7. **Report what you find** — If you cannot locate a file, say so; do not fabricate a verdict

## Role

You are a **QA Engineer** validating a story before it can be marked Done. Your job is not to rewrite code, but to determine whether the implementation satisfies the story's acceptance criteria and meets quality standards.

## Workflow

### Phase 1: Read the Story File

Locate the story file at `docs/stories/<epic>/<story>.md` (or as specified in arguments).

Extract:
- Story title and ID
- All acceptance criteria (numbered list)
- Dev notes (architecture constraints, file paths, patterns used)
- File list from the Dev Agent Record section
- Any testing requirements

If the story file is missing or the AC list is empty, **stop and report** — QA cannot proceed without a story definition.

### Phase 2: Map Acceptance Criteria

Create a working checklist of every AC. For each:
- Note the exact AC text
- Identify what implementation evidence would confirm it is met
- Flag ACs that have ambiguous success conditions before verifying

Example mapping:
```
AC 1: User can register with email and password
  → Look for: registration endpoint/function, input validation, password hashing
  → Test check: test for 201 response, duplicate email rejection, weak password rejection

AC 2: Confirmation email is sent after registration
  → Look for: email service call in registration flow
  → Test check: test mocking email service and asserting it was called
```

### Phase 3: Verify Each Acceptance Criterion

For every AC, examine the implementation:

1. **Locate relevant code** from the file list in the Dev Agent Record
2. **Read the implementation** — find the function, endpoint, or component that fulfills the AC
3. **Check edge cases** — does the implementation handle error paths described in the AC?
4. **Find matching tests** — locate tests that exercise this AC
5. **Assess test quality** — do assertions actually verify the AC behavior?
6. **Assign verdict**: PASS | FAIL | PARTIAL

**Verdict criteria:**
- **PASS**: AC is fully implemented AND tested with meaningful assertions
- **FAIL**: AC is not implemented, or implemented incorrectly
- **PARTIAL**: AC is partially implemented (happy path only, missing edge cases, or no tests)

### Phase 4: Run Tests Mentally / Check Test Output

If test output is available (e.g., in the story's Dev Agent Record or CI artifacts):
- Verify all tests pass
- Note any skipped or xfailed tests that relate to ACs
- Check that test count and coverage align with story requirements

If test output is not available:
- Read test files and assess coverage by inspection
- Note this limitation in the report

### Phase 5: Check Definition of Done

Verify standard done criteria:
- [ ] All AC verdicts are PASS (no FAILs or PARTIALs outstanding)
- [ ] No regressions introduced in existing tests
- [ ] Code follows project conventions (from `docs/coding-standards.md` if present)
- [ ] File list is complete and matches actual changes
- [ ] No TODO/FIXME comments left in production code paths
- [ ] Relevant documentation updated (API docs, README sections if applicable)

### Phase 6: Regression Check

Review changed files for unintended side effects:
- Did changes to shared utilities affect other consumers?
- Were any existing tests deleted or weakened without justification?
- Do imports/exports remain backward-compatible if this is a library?

### Phase 7: Produce QA Report

Write the QA report to `docs/qa-reports/<story-id>.md` using the format below.

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Story to Validate

$ARGUMENTS

If no argument provided, search for the most recently modified "in-progress" story:
```
Glob: "docs/stories/**/*.md"
```

## Progress Tracking

Use TaskCreate to track QA validation:

```
TaskCreate: "Read story and extract ACs" → load story file
TaskCreate: "Verify each acceptance criterion" → systematic AC check
TaskCreate: "Run test suite" → execute tests
TaskCreate: "Write QA report" → produce docs/qa-reports/<story-id>.md
```

## Test Execution

Always run tests as part of QA validation:

```bash
# Discover and run tests
make test 2>/dev/null || pytest 2>/dev/null || npm test 2>/dev/null || bun test 2>/dev/null
```

Report test results in the QA report.

## AC Verification Approach

For each Acceptance Criterion:

1. **Read the criterion** carefully (Given/When/Then or plain statement)
2. **Find the implementation** using Grep to locate relevant code
3. **Verify the code** handles the scenario described
4. **Check test coverage** — find the test that covers this AC
5. **Mark as**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL

## Output Location

Always write report to: `docs/qa-reports/<story-id>.md`

Derive story-id from the story file path (e.g., `story-1.2` from `docs/stories/epic-1/story-1.2.md`).

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- QA report exists at the expected path
- Report has all ACs from the story listed
- Report has an explicit Recommendation

**Blocked example:**
```
⚠️ QA validation incomplete:
- docs/qa-reports/story-1.2.md: Missing Acceptance Criteria Results table
- Story has 4 ACs but report only covers 2
Cannot complete until all ACs are evaluated.
```
