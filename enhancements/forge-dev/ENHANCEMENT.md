---
# Enhancement for: forge-dev
disable-model-invocation: false
argument-hint: "<story-path>"
allowed-tools: "Read, Write, Edit, MultiEdit, Bash(git *), Bash(make *), Bash(pytest *), Bash(npm *), Bash(bun *), Bash(ruff *), Bash(mypy *), Grep, Glob, Task, TaskCreate, TaskUpdate, AskUserQuestion"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify story implementation is complete before stopping:

        1. Discover the test command: check Makefile for `make test`, check package.json for test script, check pyproject.toml for pytest config
        2. Run the test suite — ALL tests must pass
        3. Discover the lint command: check for `make lint`, `ruff check .`, `npm run lint`, `bun run lint`
        4. Run the linter — NO linting errors allowed
        5. Read the story file referenced in context (or find it under docs/stories/) and verify:
           - All Technical Tasks are marked complete (check boxes or status)
           - Story status is updated to "done" or "in-progress" (not "draft")
        6. Check that no TODO comments were left in newly created files

        If tests fail, lint fails, or story tasks are incomplete: report failures and return decision: block.
        Only allow stopping when all checks pass.
      timeout: 180
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Story to Implement

$ARGUMENTS

If a path is provided, read that story file. Otherwise search for the next "ready" story:
```
Glob: "docs/stories/**/*.md"
```
Then read each file to find one with `Status: ready`.

## Progress Tracking

Use TaskCreate to track implementation phases:

```
TaskCreate: "Read and understand story" → comprehension phase
TaskCreate: "Explore codebase for context" → discover existing patterns
TaskCreate: "Implement story tasks" → one sub-task per technical task in the story
TaskCreate: "Write/update tests" → test coverage for all ACs
TaskCreate: "Run DoD checklist" → verification before marking done
```

## Project Discovery (Always First)

Before writing any code, discover project commands:

```bash
# Check for Makefile targets
make help 2>/dev/null || cat Makefile | grep "^[a-z]"

# Check package.json scripts
cat package.json | grep '"scripts"' -A 20

# Check pyproject.toml
cat pyproject.toml | grep -A 10 "\[tool.pytest"
```

## Codebase Exploration

Before implementation, read existing code to match patterns:

```
Grep: pattern to find similar implementations in the codebase
Glob: "src/**/*.ts" or "**/*.py" to find relevant files
Read: key files to understand conventions
```

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent runs:

1. **Tests**: Runs the project's test suite — must all pass
2. **Lint**: Runs linter — no errors allowed
3. **Story validation**: Verifies story file tasks are marked done

**Blocked example:**
```
⚠️ Implementation verification failed:

Tests: ❌ FAILED
  - test_user_login: AssertionError — expected 200, got 401

Lint: ✅ PASSED

Story tasks: ⚠️ INCOMPLETE
  - [ ] "Add JWT refresh endpoint" — still unchecked

Cannot mark implementation complete until all checks pass.
```

## Multi-Stack Patterns

This skill handles both common SaaS stacks:

**Next.js / TypeScript stack:**
- Components in `src/components/`, pages in `src/app/`
- Use Server Components by default, Client Components only when needed
- API routes in `src/app/api/`
- Supabase client patterns

**Python / FastAPI stack:**
- Routes in `app/routers/`, models in `app/models/`
- Pydantic schemas for request/response
- SQLAlchemy for ORM, Alembic for migrations
- Pytest for testing

Match the stack discovered in `docs/architecture.md` or project files.
