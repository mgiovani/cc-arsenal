---
name: git-commit
description: Generate conventional commits following conventionalcommits.org specification.
  Activates when users want to commit, stage changes, or need commit messages.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: false
argument-hint: ''
allowed-tools:
- Bash(git *)
- Read
- Edit
- Write
- Task
- TodoWrite
hooks:
  PreToolUse:
  - matcher: Bash(git commit*)
    hooks:
    - type: command
      command: ./skills/git-commit/scripts/pre-commit-lint.sh
      timeout: 60
---

# Git Commit

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Conventional Commit

Generate a conventional commit message following https://www.conventionalcommits.org/en/v1.0.0/ specification and create commits automatically.

## Quality Guidelines

**CRITICAL**: Commit messages must accurately describe ACTUAL changes:
1. **Read the diff** - Base message ONLY on what you see in the diff, not assumptions
2. **Verify scope** - Check which files/modules actually changed before setting scope
3. **Check breaking changes** - Look for removed exports, changed APIs, deleted functions
4. **No guessing** - If unsure about change purpose, ask user rather than assume

## Quality Gates

This skill includes automatic code quality verification before committing:

### Pre-commit Linting (PreToolUse Hook)

Before executing `git commit`, the following linting checks run automatically:

**Supported Project Types:**
- **Node.js** (package.json): Runs `npm run lint`, `bun run lint`, `pnpm run lint`, or `yarn run lint`
- **Python** (pyproject.toml): Runs `ruff check .` or `flake8 .`
- **Makefile**: Runs `make lint` if target exists
- **Ruby** (.rubocop.yml): Runs `rubocop`
- **Go** (.golangci.yml): Runs `golangci-lint run`

**Behavior:**
- ✅ **Linting passes**: Commit proceeds normally
- ❌ **Linting fails**: Commit is blocked with clear error message
- ℹ️ **No linter configured**: Commit proceeds without linting (non-blocking)

**Example blocked commit:**
```
🔍 Running: ruff check .
❌ Linting failed: ruff check reported errors. Fix lint errors before committing.

Found 3 errors in src/utils.py:
- Line 42: Undefined name 'foo'
- Line 55: Unused import 'os'
- Line 78: Line too long (120 > 88 characters)
**To fix**: Address the linting errors and run the commit command again.

**To bypass** (not recommended): Fix the underlying lint errors instead of bypassing. Quality gates ensure code meets project standards.

## Workflow

### Phase 1: Parallel Change Analysis (Use Parallel Analysis for Complex Changes)

For changes spanning multiple files or concerns, spawn parallel agents:

```
If git diff shows >100 lines or >5 files changed:

Agent 1 - Semantic Analysis:
- prompt: "Analyze this git diff and explain what the code changes actually DO. Focus on behavior changes, not just file names. What features were added? What bugs were fixed?"
- agent-type: "general-purpose"

Agent 2 - Breaking Change Detection:
- prompt: "Check this git diff for breaking changes: removed public functions, changed function signatures, deleted exports, renamed APIs. List any breaking changes found."
- agent-type: "general-purpose"

Agent 3 - Commit Splitting Analysis:
- prompt: "Should these changes be split into multiple commits? Look for: mixing features with fixes, unrelated changes, docs mixed with code. Recommend how to split if needed."
- agent-type: "general-purpose"

Merge results -> Generate accurate commit message(s)
### Track Progress with TodoWrite (For Multiple Commits)

When changes need to be split into multiple commits, use TodoWrite:

```
Example: Changes include a feature, a fix, and docs update

TodoWrite:
- [ ] Commit 1: feat(auth): add OAuth2 support
- [ ] Commit 2: fix(api): resolve null pointer exception
- [ ] Commit 3: docs: update authentication guide

Mark each as in_progress -> completed as you stage and commit.
### Phase 2: Analyze Changes

1. **Analyze Changes**: Run `git status` and `git diff --staged` to understand current changes
2. **Group Related Changes**: Identify logically separate changes that should be committed individually (e.g., separate feature additions from bug fixes, documentation updates from code changes)
3. **For Each Logical Group**:
 - Determine the appropriate commit type:
 - `feat`: New feature for the user
 - `fix`: Bug fix for the user
 - `docs`: Documentation only changes
 - `style`: Code style changes (formatting, missing semi-colons, etc.)
 - `refactor`: Code change that neither fixes a bug nor adds a feature
 - `perf`: Performance improvements
 - `test`: Adding missing tests or correcting existing tests
 - `build`: Changes to build system or external dependencies
 - `ci`: Changes to CI configuration files and scripts
 - `chore`: Other changes that don't modify src or test files
 - `revert`: Reverts a previous commit
 - Identify the scope if applicable (component, module, or area affected)
 - Write a concise description in imperative mood (max 50 characters)
 - Add a detailed body if the change is complex (wrap at 72 characters)
 - Include breaking change footer if applicable: `BREAKING CHANGE: description`
 - Format as: `type(scope): description`

4. **Commit Strategy**:
 - If changes represent a single logical unit: create one commit
 - If changes span multiple concerns: create separate commits for each logical group
 - Stage files appropriately for each commit using `git add`
 - Create each commit with the generated message

## Example Formats

```
feat(auth): add OAuth2 login support
fix(api): resolve null pointer in user endpoint
docs: update installation instructions
chore(deps): bump lodash to 4.17.21
refactor(parser): extract validation logic to separate module

feat(shopping-cart)!: remove deprecated calculate method

BREAKING CHANGE: calculate has been removed, use computeTotal instead
## Important Notes

- **Multiple Commits**: If different types of changes are identified (e.g., feat + fix + docs), create separate commits for each type
- **Staging**: Use `git add <specific-files>` to stage only relevant files for each commit
- **Imperative Mood**: Use "add" not "added", "fix" not "fixed"
- **Breaking Changes**: Append an exclamation mark after type/scope and add a `BREAKING CHANGE:` footer
- **Scope**: Optional but recommended for clarity (e.g., component name, module name)
- **Body**: Use for complex changes to explain the "what" and "why", not "how"
- **Pre-commit Hooks**: NEVER use `--no-verify` to skip pre-commit hooks - it bypasses important quality gates

Generate the most appropriate commit message(s) based on the changes and commit automatically. Ask for confirmation before committing if the changes are complex or span multiple concerns.

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Quality Gates

This skill includes automatic code quality verification before committing:

### Pre-commit Linting (PreToolUse Hook)

Before executing `git commit`, the following linting checks run automatically:

**Supported Project Types:**
- **Node.js** (package.json): Runs `npm run lint`, `bun run lint`, `pnpm run lint`, or `yarn run lint`
- **Python** (pyproject.toml): Runs `ruff check .` or `flake8 .`
- **Makefile**: Runs `make lint` if target exists
- **Ruby** (.rubocop.yml): Runs `rubocop`
- **Go** (.golangci.yml): Runs `golangci-lint run`

**Behavior:**
- ✅ **Linting passes**: Commit proceeds normally
- ❌ **Linting fails**: Commit is blocked with clear error message
- ℹ️ **No linter configured**: Commit proceeds without linting (non-blocking)

**Example blocked commit:**
```
🔍 Running: ruff check .
❌ Linting failed: ruff check reported errors. Fix lint errors before committing.

Found 3 errors in src/utils.py:
- Line 42: Undefined name 'foo'
- Line 55: Unused import 'os'
- Line 78: Line too long (120 > 88 characters)
```

**To fix**: Address the linting errors and run the commit command again.

**To bypass** (not recommended): Fix the underlying lint errors instead of bypassing. Quality gates ensure code meets project standards.

## Workflow

### Phase 1: Parallel Change Analysis (Use SubAgents for Complex Changes)

For changes spanning multiple files or concerns, spawn parallel agents:

```
If git diff shows >100 lines or >5 files changed:

Agent 1 - Semantic Analysis:
- prompt: "Analyze this git diff and explain what the code changes actually DO. Focus on behavior changes, not just file names. What features were added? What bugs were fixed?"
- subagent_type: "general-purpose"

Agent 2 - Breaking Change Detection:
- prompt: "Check this git diff for breaking changes: removed public functions, changed function signatures, deleted exports, renamed APIs. List any breaking changes found."
- subagent_type: "general-purpose"

Agent 3 - Commit Splitting Analysis:
- prompt: "Should these changes be split into multiple commits? Look for: mixing features with fixes, unrelated changes, docs mixed with code. Recommend how to split if needed."
- subagent_type: "general-purpose"

Merge results -> Generate accurate commit message(s)
```

### Track Progress with TodoWrite (For Multiple Commits)

When changes need to be split into multiple commits, use TodoWrite:

```
Example: Changes include a feature, a fix, and docs update

TodoWrite:
- [ ] Commit 1: feat(auth): add OAuth2 support
- [ ] Commit 2: fix(api): resolve null pointer exception
- [ ] Commit 3: docs: update authentication guide

Mark each as in_progress -> completed as you stage and commit.
```

### Phase 2: Analyze Changes

1. **Analyze Changes**: Run `git status` and `git diff --staged` to understand current changes
2. **Group Related Changes**: Identify logically separate changes that should be committed individually (e.g., separate feature additions from bug fixes, documentation updates from code changes)
3. **For Each Logical Group**:
  - Determine the appropriate commit type:
    - `feat`: New feature for the user
    - `fix`: Bug fix for the user
    - `docs`: Documentation only changes
    - `style`: Code style changes (formatting, missing semi-colons, etc.)
    - `refactor`: Code change that neither fixes a bug nor adds a feature
    - `perf`: Performance improvements
    - `test`: Adding missing tests or correcting existing tests
    - `build`: Changes to build system or external dependencies
    - `ci`: Changes to CI configuration files and scripts
    - `chore`: Other changes that don't modify src or test files
    - `revert`: Reverts a previous commit
  - Identify the scope if applicable (component, module, or area affected)
  - Write a concise description in imperative mood (max 50 characters)
  - Add a detailed body if the change is complex (wrap at 72 characters)
  - Include breaking change footer if applicable: `BREAKING CHANGE: description`
  - Format as: `type(scope): description`

4. **Commit Strategy**:
  - If changes represent a single logical unit: create one commit
  - If changes span multiple concerns: create separate commits for each logical group
  - Stage files appropriately for each commit using `git add`
  - Create each commit with the generated message
