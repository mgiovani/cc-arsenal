---
name: git-commit
description: Generate a conventional commit message (conventionalcommits.org) from the
  staged/unstaged diff and create the commit. Use when the user wants to commit, stage
  changes, or needs a commit message written. Not for release commits or changelogs (use
  git-release) or branch-finish workflows (use gitflow).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: ''
allowed-tools:
- Bash(git *)
- Read
- Edit
- Write
hooks:
  PreToolUse:
  - matcher: Bash(git commit*)
    hooks:
    - type: command
      command: ${CLAUDE_PLUGIN_ROOT}/skills/git-commit/scripts/pre-commit-lint.sh
      timeout: 60
---

# Git Commit

Generate a conventional commit message and create the commit.

## Quality Guidelines

Base the message only on what the diff actually shows, not assumptions:
1. Read `git status` and `git diff --staged` (or `git diff` if nothing is staged yet) before writing anything.
2. Check which files/modules changed before setting scope.
3. Look for removed exports, changed signatures, deleted functions to catch breaking changes.
4. If the purpose of a change is unclear, ask the user rather than guess.

## Pre-commit Linting (automatic)

A `PreToolUse` hook runs before every `git commit`: it detects the project's linter (Node's
`npm/bun/pnpm/yarn run lint`, Python's `ruff`/`flake8`, `make lint`, `rubocop`, `golangci-lint`)
and blocks the commit if it fails. No linter configured means the commit proceeds unblocked.
Never bypass a failing lint with `--no-verify` — fix the errors and re-run the commit instead.

## Workflow

1. Run `git status` and `git diff --staged` to see what actually changed.
2. If the diff mixes unrelated concerns (e.g. a feature plus an unrelated fix plus docs),
   split into separate commits by staging each group with `git add <files>` and committing
   them one at a time. Otherwise, one commit is enough — don't force a split.
3. For each commit, pick the type:
   - `feat`: new feature
   - `fix`: bug fix
   - `docs`: documentation only
   - `style`: formatting, no code meaning change
   - `refactor`: neither fixes a bug nor adds a feature
   - `perf`: performance improvement
   - `test`: adding or correcting tests
   - `build`: build system or dependency changes
   - `ci`: CI configuration/scripts
   - `chore`: everything else that doesn't touch src or tests
   - `revert`: reverts a previous commit
4. Format as `type(scope): description` — scope optional, description imperative mood
   ("add" not "added"), max ~50 characters. Add a wrapped body for non-trivial changes to
   explain why, not how. For breaking changes, append `!` after the scope and add a
   `BREAKING CHANGE: ...` footer.

## Example formats

```
feat(auth): add OAuth2 login support
fix(api): resolve null pointer in user endpoint
docs: update installation instructions
chore(deps): bump lodash to 4.17.21

feat(shopping-cart)!: remove deprecated calculate method

BREAKING CHANGE: calculate has been removed, use computeTotal instead
```

Ask for confirmation before committing if the changes are complex or span multiple concerns; otherwise just commit.
