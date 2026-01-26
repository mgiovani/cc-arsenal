---
description: "Implement a feature using senior staff engineer best practices with parallel subagents"
argument-hint: "<feature_description>"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task", "TodoWrite", "WebFetch", "EnterPlanMode", "AskUserQuestion"]
---

# Feature Implementation Command

You are implementing a new feature as a **Senior Staff Engineer** following best practices (SOLID, DRY, YAGNI) to create a secure, fast, and reliable production application.

## Feature to Implement

$ARGUMENTS

## Anti-Hallucination Guidelines

**CRITICAL**: Before implementing anything:
1. **Discover project commands first** - Do NOT assume `bun`, `npm`, `make`, etc. exist
2. **Read CLAUDE.md** - Every project may have different conventions
3. **Verify tools exist** - Check for `Makefile`, `justfile`, `package.json`, `pyproject.toml`, etc.
4. **Never guess test commands** - Find the actual test runner used by this project

## Implementation Workflow

**Use TodoWrite to track progress through each phase.** Update task status as you complete each step.

### Phase 0: Project Discovery (REQUIRED)

Before any implementation, discover how this project works:

```
Use Task tool with Explore agent:
- prompt: "Discover the development workflow for this project:
    1. Read CLAUDE.md if it exists - extract all development commands
    2. Check for task runners: Makefile, justfile, package.json scripts, pyproject.toml scripts
    3. Identify the test command (e.g., make test, just test, npm test, pytest, bun test)
    4. Identify the lint command (e.g., make lint, npm run lint, ruff check)
    5. Identify the build/type-check command
    6. Identify the dev server command if applicable
    7. Note any pre-commit hooks or quality gates
    Return a structured summary of all available commands."
- subagent_type: "Explore"
```

Store discovered commands for use in later phases. Example output:
```
Project Commands:
- Test: `make test` or `pytest`
- Lint: `make lint` or `ruff check`
- Type Check: `make type-check` or `pyright`
- Build: `make build` or `npm run build`
- Dev Server: `make dev` or `npm run dev`
- Quality: `make check` (runs all checks)
```

### Phase 1: Research & Discovery

Before implementing, research best practices and understand the codebase context by spawning an Explore agent:

```
Use Task tool with Explore agent:
- prompt: "Research and gather context for implementing [FEATURE]:

    1. **Best Practices Research**: Search the web for 'latest best practices' and 'current year best practices' related to [FEATURE]. Look for:
       - Current industry standards and patterns
       - Security considerations
       - Performance recommendations
       - Common pitfalls to avoid

    2. **Library Documentation** (if using external libraries/frameworks):
       - Use Context7 MCP to fetch up-to-date documentation
       - Validate API usage patterns against current docs
       - Check for deprecated methods or breaking changes

    3. **Codebase Exploration**:
       - Find similar existing implementations to reference
       - Identify coding patterns and conventions used
       - Locate test patterns and fixtures
       - Note file organization and naming conventions

    Return a comprehensive summary with:
    - Relevant best practices (with sources)
    - Library API patterns to follow (if applicable)
    - Specific file paths and existing patterns from the codebase"
- subagent_type: "Explore"
```

### Phase 2: Planning

1. **Enter Plan Mode**: Use `EnterPlanMode` to create a detailed implementation plan
2. **Plan Contents**:
   - Break down the feature into discrete, parallelizable tasks
   - Identify which tasks can be done by subagents concurrently
   - Define clear interfaces between components
   - Consider security implications
   - Plan test coverage strategy
3. **Get User Approval**: Exit plan mode only after user approves the plan

### Phase 3: Parallel Implementation with Subagents

For each parallelizable task group, spawn subagents using the Task tool:

**Subagent Instructions Template:**
```
Implement [specific task description].

First, read the project's CLAUDE.md to understand conventions and patterns.

Requirements:
1. Follow existing codebase patterns and conventions
2. Apply SOLID, DRY, YAGNI principles
3. Write comprehensive tests (unit + integration where applicable)
4. All tests MUST pass before completion
5. Handle errors appropriately
6. Add necessary type definitions (if typed language)

Project-specific commands (discovered in Phase 0):
- Test command: [INSERT DISCOVERED TEST COMMAND]
- Lint command: [INSERT DISCOVERED LINT COMMAND]

After implementation:
1. Run the test suite to verify all tests pass
2. Run linting to ensure code quality
3. Report back what was implemented (do NOT commit - the main agent will handle commits)

If tests fail, fix them before reporting completion.
If you encounter ambiguous requirements, report back and ask for clarification instead of guessing.
```

**After each subagent completes**, the main agent should:
1. Review the changes
2. Run `/cc-arsenal:git:commit` to commit the subagent's work (if available) or create a conventional commit manually
3. Proceed to the next subagent or phase

**Parallelization Strategy:**
- Group independent tasks together
- Spawn multiple subagents simultaneously for unrelated work
- Use sequential subagents for dependent tasks

### Phase 4: Integration & Verification

After all subagents complete, run verification using the **discovered commands from Phase 0**:

1. **Run Full Test Suite**: Use discovered test command
2. **Lint Check**: Use discovered lint command
3. **Type Check**: Use discovered type-check/build command
4. **Fix All Issues**: If any test, lint, or build errors occur, fix them before proceeding. Repeat until all checks pass.

**Example verification (commands vary by project):**
```bash
# Python project with Makefile
make test && make lint && make type-check

# Node.js project with package.json
npm test && npm run lint && npm run build

# Python project with just
just test && just lint

# Simple Python project
pytest && ruff check . && pyright
```

### Phase 5: Final Commit

Only proceed when all checks pass:
1. Review all changes made by subagents
2. Create a final integration commit if needed using conventional commit format
3. Summarize what was implemented

### Phase 6: Manual Testing (Optional - For UI Features)

If the feature has a UI component, use the `agent-browser` skill for browser automation:

1. **Start the Development Server** (using discovered dev command)
2. **Navigate to the Feature**: `agent-browser open <url>`
3. **Visual Verification**: `agent-browser snapshot -i`
4. **Interactive Testing**: Use refs to interact with elements (`agent-browser click @e1`)
5. **Screenshot Evidence**: `agent-browser screenshot page.png`
6. **Cleanup**: `agent-browser close`

**When to Skip Manual Testing:**
- Backend-only changes (API routes, server actions)
- Pure refactoring with no UI changes
- Test-only changes
- CLI tools without UI

## Quality Gates

Each subagent MUST ensure:
- [ ] All new code has tests
- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors (if applicable)
- [ ] Code follows existing patterns
- [ ] Security best practices followed
- [ ] No over-engineering (YAGNI)

## Error Handling

If a subagent encounters issues:
1. Log the error clearly
2. Attempt to fix within scope
3. If unable to fix, report back with details
4. Do NOT commit broken code

## Handling Ambiguity

If you encounter unclear or ambiguous requirements at any phase:
1. Use `AskUserQuestion` to clarify before proceeding
2. Do NOT guess or make assumptions about critical decisions
3. Present options with trade-offs when multiple valid approaches exist

## Output Format

Provide a summary including:
- Features implemented
- Files created/modified
- Tests added
- Manual testing results (if performed)
- Any known limitations or follow-up items

## Usage

```bash
# Implement a specific feature
/dev:implement-feature Add user authentication with OAuth2

# Implement with more context
/dev:implement-feature Create a REST API endpoint for managing user preferences with validation

# Implement a refactoring task
/dev:implement-feature Refactor the payment module to use the strategy pattern
```

## Important Notes

- **Always run Phase 0 first** - Never assume which tools are available
- **Project-specific workflows** - Each project may have unique quality gates
- **Commit strategy** - Prefer smaller, logical commits over one big commit
- **Ask when unsure** - Better to clarify than to guess incorrectly
