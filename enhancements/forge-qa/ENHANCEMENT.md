---
# Enhancement for: forge-qa
disable-model-invocation: false
argument-hint: "<story-path>"
allowed-tools: "Read, Write, Edit, Bash(make *), Bash(pytest *), Bash(npm *), Bash(bun *), Grep, Glob, Task, TaskCreate, TaskUpdate"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify QA validation is complete before stopping:

        1. Check that a QA report file exists at docs/qa-reports/<story-id>.md
        2. Verify the report contains:
           - Overall status (PASS / FAIL / PARTIAL)
           - Acceptance Criteria Results table (every AC from the story listed)
           - Recommendation (APPROVE or NEEDS WORK with specifics)
        3. If the overall status is FAIL: ensure the stop is intentional (QA found failures, which is valid output)
        4. Run the test suite and verify that test count matches what's reported in the QA report

        Block only if the QA report is missing or incomplete (not if it says FAIL — that's a valid outcome).
      timeout: 60
---

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
