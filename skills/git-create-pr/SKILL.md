---
name: git-create-pr
description: Create a GitHub Pull Request from the current branch, following conventional commit format and pre-filling the repo's PR template. Activates on "create a PR", "open a pull request", "push this for review", or similar. Use after commits are made and pushed is not yet done; for the commits themselves use git-commit, for release/hotfix branch PRs use gitflow, and for the full review-then-commit-then-PR pipeline in one go use ship.
metadata:
  author: mgiovani
  version: 2.1.0
disable-model-invocation: false
argument-hint: '[--base branch] [--draft]'
allowed-tools:
- Bash(git *)
- Bash(gh *)
- Read
- Write
---

# Create Pull Request

Create a GitHub Pull Request following conventional commits, pre-filled with the repo's PR template, and opened in the browser for final review.

Every PR bullet must map to an actual commit or diff hunk — drop claims you can't back with evidence in `git log` or `git diff`.

**Invariant: never mutate the user's files to satisfy a precondition.** If a check in step 1 fails, report it and stop. Do not run `git checkout`, `git restore`, `git reset`, `git stash`, or `git clean` against the user's tracked files to "fix" a dirty tree, and do not switch branches to route around a main/master check — those are the user's decisions, not this skill's. The only git commands this skill runs against the working tree are read-only until step 7's `git push`.

## Workflow

1. **Validate preconditions — run this before anything else, including branch analysis**
   - Check working tree is clean: `git status --porcelain`. Any output means it's dirty.
     - If dirty: **stop immediately**. Show the `git status --porcelain` output and tell the user to commit or stash their changes first, e.g. `Working tree has uncommitted changes: M README.md. Commit or stash before opening a PR.` Do not proceed to step 2, and do not touch the listed files.
   - Get current branch: `git branch --show-current`.
     - If it's `main` or `master`: **stop immediately**. Tell the user there's no feature branch to open a PR from, e.g. `Currently on main — check out a feature branch first.` Do not proceed.
   - Check commits exist: `git log origin/<base>..HEAD --oneline`. If empty, stop and say there's nothing to open a PR for.
   - Extract ticket ID from branch name (e.g., `ABC-123` from `feature/ABC-123_description`)

2. **Determine base branch**
   - Use `--base`/`-b` argument if provided
   - Otherwise: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
   - Fall back to `main` if detection fails

3. **Analyze changes**
   - `git log origin/<base>..HEAD --format="%h %s"` for commits
   - `git diff origin/<base>...HEAD --stat` for file changes
   - Synthesize these directly in the main thread — a subagent fan-out is overkill for what one `git log` + one `diff --stat` already summarizes. Only reach for a subagent if the diff is too large to fit in context.

4. **Generate PR title** (conventional commit format, max 72 chars)
   - `type(scope): [TICKET-123] description` or `type(scope): description` if no ticket
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
   - Examples: `feat(auth): [ABC-123] add OAuth2 login support`, `fix(api): resolve null pointer in user endpoint`

5. **Fill PR template**
   - Look for `.github/pull_request_template.md` and fill it without changing its structure
   - If none exists, use:
     ```markdown
     ## Summary
     [Brief description]

     ## Changes
     - [Bullet points from commits]

     ## Testing
     - [ ] Tests added/updated
     - [ ] Manual testing completed
     ```
   - Save to `BODY_FILE="/tmp/pr-body-$(date +%s).md"`

6. **Ask for confirmation**
   - Show a compact summary: ticket, commit count, authors (keep lines under 60 chars)
   - Preview the generated title and body
   - If the repo has CI configured (`.github/workflows/*.yml`) and tests haven't been verified locally this session, suggest running the `cc-arsenal:ci-local` skill first — cheaper to catch a failure now than after the PR is open
   - Ask: `Create PR? (y/n/e to edit):` — accept `y`/`yes`/`n`/`no`/`e`/`edit`
   - On `e`, ask for custom title/body

7. **Push and create PR** (after confirmation)
   ```bash
   # Push first — required before gh pr create can reference the branch
   git push -u origin $(git branch --show-current)

   # BODY_FILE is the file written in step 5
   gh pr create \
     --title "type(scope): [TICKET] description" \
     --body-file "$BODY_FILE" \
     --base <determined-base-branch> \
     --web
   ```
   - Do not combine `--reviewer`, `--assignee`, or `--label` with `--web` — they conflict. The user adds those in the web UI.

## Argument Parsing

- `--base branch` / `-b branch` — target branch, defaults to repo default
- `--draft` / `-d` — adds `--draft` to `gh pr create`

## Examples

```bash
git-create-pr                    # uses repo default base branch
git-create-pr --base develop     # target a specific base branch
git-create-pr --draft            # create as draft PR
git-create-pr -b develop -d      # both
```

After pushing, the PR opens in the browser pre-filled with title and body. Add reviewers/labels there.

**Precondition failure** — dirty tree, stop before any analysis:
```
Working tree has uncommitted changes:
 M README.md
Commit or stash before opening a PR. Not proceeding.
```
No `git checkout`, `git push`, or `gh pr create` runs after this — the turn ends here.
