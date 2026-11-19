---
name: git-commit
description: Generate a conventional commit message (conventionalcommits.org) from the
  staged/unstaged diff and create the commit. Use when the user wants to commit, stage
  changes, or needs a commit message written. Not for release commits or changelogs (use
  git-release) or branch-finish workflows (use gitflow).
metadata:
  summary: "Conventional commit message generation"
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: ''
---

# Git Commit

Generate a conventional commit message and create the commit.

## Quality Guidelines

Base the message only on what the diff actually shows, not assumptions:
1. Read `git status` and `git diff --staged` (or `git diff` if nothing is staged yet) before writing anything.
2. Check which files/modules changed before setting scope.
3. Look for removed exports, changed signatures, deleted functions to catch breaking changes.
4. If the purpose of a change is unclear, ask the user rather than guess.

## Pre-commit Linting

Run the project's lint command before every `git commit`. Use the first that exists: a `make lint`
target, the `lint` script in `package.json` (through the package manager whose lockfile is present),
`ruff check .` or `flake8` for a `pyproject.toml` project, `rubocop` with a `.rubocop.yml`,
`golangci-lint run` with a `.golangci.yml`. For a `uv` project run `uv run ruff check .`. Skip a linter whose command is not installed. No linter configured means the commit proceeds. If lint
fails, fix the errors and run it again; never bypass a failing lint with `--no-verify`.

## Workflow

1. Run `git status` and `git diff --staged` to see what actually changed.
2. If the diff mixes unrelated concerns (e.g. a feature plus an unrelated fix plus docs),
   split into separate commits by staging each group with `git add <files>` and committing
   them one at a time. Otherwise, one commit is enough, don't force a split.
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
4. Format as `type(scope): description`, scope optional, description imperative mood
   ("add" not "added"), max ~50 characters. Skip the body for a typo fix or a single
   dependency bump; add a wrapped body (why, not how) once the change alters behavior or
   touches multiple files. For breaking changes, append `!` after the scope and add a
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
