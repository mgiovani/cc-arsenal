# Story Definition of Done Checklist

Use this checklist before marking any story as "done". Go through every item honestly — it is better to catch issues now than during review.

## 1. Acceptance Criteria

Complete this for each acceptance criterion:

| AC | Description | Verified? | How verified |
|----|-------------|-----------|--------------|
| 1  | [AC text]   | [ ]       | [test name or manual step] |
| 2  | [AC text]   | [ ]       | [test name or manual step] |
| N  | [AC text]   | [ ]       | [test name or manual step] |

**Rule**: Every AC must be verified by either an automated test or a documented manual verification step. "Assumed to work" is not acceptable.

Checklist:
- [ ] All acceptance criteria are implemented
- [ ] Every AC has a corresponding test OR explicit manual verification documented
- [ ] No AC is partially implemented ("mostly works")
- [ ] Edge cases implied by ACs are handled (empty state, max values, error paths)

## 2. Technical Tasks

- [ ] Every task in the story is checked off `[x]`
- [ ] No tasks are marked complete prematurely (verify the implementation before checking off)
- [ ] Subtasks are complete, not just parent tasks

If a task could not be completed, document why in the story's notes. Do not mark it complete.

## 3. Code Quality

### Standards Compliance

- [ ] Code follows the naming conventions of the surrounding codebase
  - Variables and functions: consistent with project style (camelCase, snake_case, etc.)
  - File names: consistent with project pattern
  - Directory structure: files placed where architecture specifies
- [ ] No magic numbers or strings — use named constants or config values
- [ ] No commented-out code blocks (delete unused code; version control preserves history)
- [ ] No TODO or FIXME comments (implement now or create a follow-up story)
- [ ] No debug statements (`console.log`, `print`, `debugger`, `pdb.set_trace`)

### Input Validation

- [ ] All user inputs are validated at the API boundary (not just client-side)
- [ ] Validation error messages are clear and user-facing (not stack traces)
- [ ] Unexpected inputs fail gracefully (no 500 errors from malformed input)

### Error Handling

- [ ] All operations that can fail have error handling
- [ ] Errors are logged with sufficient context for debugging
- [ ] Errors do not expose sensitive information (stack traces, database details) to users
- [ ] Network errors and timeouts are handled (retry logic or user-friendly error messages)

### Security Basics

- [ ] Authentication check is present on all protected endpoints
- [ ] Authorization check is present (user can only access their own data)
- [ ] No sensitive data logged (passwords, tokens, payment info)
- [ ] No hardcoded secrets, API keys, or credentials in code
- [ ] SQL queries use parameterized queries / ORM (no string concatenation for queries)

### TypeScript-Specific (if applicable)

- [ ] No `any` types introduced without justification
- [ ] No TypeScript errors or warnings suppressed with `@ts-ignore` without comment explaining why
- [ ] New types/interfaces are exported if they may be needed elsewhere

### Python-Specific (if applicable)

- [ ] Type hints on all new functions and return values
- [ ] No bare `except:` clauses — catch specific exceptions
- [ ] Structured logging used (not `print()`)

## 4. Tests

### Coverage

- [ ] Every acceptance criterion has at least one automated test
- [ ] Happy path is tested (the main success scenario)
- [ ] Error cases are tested (invalid input, unauthorized access, not found)
- [ ] Edge cases are tested (empty results, maximum values, boundary conditions)

### Test Quality

- [ ] Tests have descriptive names that explain what they verify
  - Good: `test_create_project_with_duplicate_name_returns_409`
  - Bad: `test_project_error`
- [ ] Tests are independent — no test depends on another test's side effects
- [ ] Tests use setup/teardown or fixtures for test data — no hardcoded database IDs
- [ ] External services are mocked (email, Stripe, external APIs)
- [ ] Tests do not call real external services

### Test Results

- [ ] All new tests pass
- [ ] All pre-existing tests still pass (no regressions)
- [ ] Test coverage has not decreased for the changed modules (if coverage reporting is configured)

If any pre-existing tests are failing that were not caused by this story's changes, document them — do not hide them.

## 5. Build and Lint

- [ ] Project builds successfully without errors
- [ ] Linter passes without new errors or warnings
  - TypeScript: `tsc --noEmit` passes; ESLint passes
  - Python: ruff/flake8/pylint passes; mypy passes
- [ ] No new dependency added without explicit user approval (if approval was given, it is documented)
- [ ] New dependencies are added to the correct manifest file (package.json, requirements.txt, pyproject.toml)

## 6. Database and Configuration

- [ ] Database migrations are written for schema changes (not just ORM model changes)
- [ ] Migrations are reversible (down migration exists) where the framework supports it
- [ ] New environment variables are documented:
  - Added to `.env.example` (with placeholder value, not real secret)
  - Mentioned in story notes for the next developer
- [ ] No schema changes break backwards compatibility unless explicitly intended

## 7. Story Administration

### Story File Updates

- [ ] Story status changed from "in-progress" to "done"
- [ ] All task checkboxes are marked `[x]`
- [ ] Story file Dev Notes updated with any implementation decisions that differ from the plan:
  - Different files created than listed
  - Alternative approach taken
  - Known limitations or follow-up items

### Documentation (as applicable)

- [ ] API changes are documented (if the project has API docs)
- [ ] Public functions/methods have docstrings (if the project's convention requires it)
- [ ] README updated if setup steps changed (new environment variables, new dependencies requiring install steps)

## 8. Final Self-Review

Before submitting, read through your own changes as if you were reviewing someone else's code:

- [ ] Does the code do what the story says it should do?
- [ ] Is there any code that is unnecessary for the story's requirements?
- [ ] Is there anything you would flag in a code review that you haven't fixed?
- [ ] Does the implementation handle the scenarios a user would actually encounter?

---

## Completing the Checklist

After going through all items:

**If all items are checked:**
Mark the story status as "done" and provide a completion summary.

**If some items are not checked:**
Do not mark the story as done. Either:
1. Fix the issue and re-check the item
2. Document why the item cannot be completed and report it as a blocker

**Completion summary format:**
```
Story [ID]: [Title] — DONE

Acceptance criteria: [N]/[N] verified
Tasks: [N]/[N] complete
Tests added: [N]
Files created: [list]
Files modified: [list]
Notes: [any deviations, follow-up items, or context for next story]
```
