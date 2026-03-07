---
name: git-sync
description: Sync current branch with base branch using merge (default) or rebase. Handles fork sync, conflict detection, and stash management.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[--rebase] [--base main] [--upstream] [--stash]'
allowed-tools:
- Bash(git *)
- Read
- AskUserQuestion
---

# Git Sync

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

Sync the current branch with its base or upstream branch. Defaults to merge to preserve history; rebase is opt-in only.

## Anti-Hallucination Guidelines

**CRITICAL**: Only sync based on what `git status` and `git log` actually show:
1. **Read before acting** — Run `git status` and `git branch` before any sync operation
2. **Verify branch state** — Check commits ahead/behind before proposing a strategy
3. **Never force push main/master** — Hard rule, no exceptions
4. **Confirm conflicts** — Report exact conflicting files; do not guess

## Workflow

### Phase 1: Analyze State

Run the following to understand current branch state:

```bash
# Current branch and status
git branch --show-current
git status --porcelain

# Remote tracking info
git remote -v
git fetch --dry-run 2>&1 || true

# Commits ahead/behind base
git log --oneline HEAD..origin/main 2>/dev/null | head -20
git log --oneline origin/main..HEAD 2>/dev/null | head -20
```

Also check:
- Is working tree dirty? (uncommitted changes)
- Is branch pushed to remote? (`git log origin/<branch>..HEAD` — if error, branch is local-only)
- What is the base branch? (check PR info via `gh pr view --json baseRefName -q .baseRefName 2>/dev/null` or ask user)

### Phase 2: Strategy Selection

Determine sync strategy:

**Merge (default)** — Use when:
- Branch has been pushed to remote (shared branches)
- User did not pass `--rebase`
- You are unsure

**Rebase (opt-in)** — Use only when:
- User explicitly passed `--rebase`, OR
- Branch is local-only (never pushed) and `--rebase` is passed

**Fork sync** (`--upstream`) — Use when:
- User wants to sync from upstream remote (fork workflow)
- Run: `git fetch upstream && git merge upstream/<base>`

Display the detected state and proposed strategy clearly before proceeding:

```
Current branch: feature/my-feature
Base branch:    main
Strategy:       merge (default)
Commits behind: 5
Commits ahead:  2
Dirty tree:     no
```

If user did not provide `--base`, infer base from:
1. `gh pr view --json baseRefName` (if GitHub CLI available)
2. Git config: `git config branch.<name>.merge`
3. Fallback: ask with `AskUserQuestion`

### Phase 3: Pre-sync Safety

1. **Handle dirty working tree**:
   - If `--stash` flag: run `git stash push -m "git-sync auto-stash"` before sync
   - If dirty tree without `--stash`: abort with clear message asking user to commit, stash, or use `--stash`

2. **Fetch latest from remote**:
   ```bash
   git fetch origin
   # For fork sync:
   git fetch upstream
   ```

3. **Re-check divergence** after fetch to report accurate numbers

### Phase 4: Execute Sync

**Merge strategy**:
```bash
git merge origin/<base>
```

**Rebase strategy** (local-only branch):
```bash
git rebase origin/<base>
```

**Rebase strategy** (pushed branch — warn user first):
```
WARNING: This branch has been pushed to remote.
Rebasing will require a force-push, which rewrites history.
This is ONLY safe if no one else has pulled this branch.
Proceed? [y/N]
```
If yes:
```bash
git rebase origin/<base>
git push --force-with-lease origin <branch>
```

**On merge/rebase conflict**:
1. Run `git diff --name-only --diff-filter=U` to list conflicting files
2. Report exact files with conflict markers
3. Do NOT attempt to resolve conflicts automatically
4. Offer two options:
   - Continue: user resolves conflicts manually, then runs `git merge --continue` or `git rebase --continue`
   - Abort: run `git merge --abort` or `git rebase --abort`

### Phase 5: Post-sync Report

After successful sync:

```bash
# Show new position
git log --oneline -5
git log --oneline origin/<base>..HEAD | wc -l
```

Report:
- New commit count ahead of base
- Whether force-push was used
- Whether stash was popped (`git stash pop` if `--stash` was used)
- Tip: mention `git rerere` if conflicts were present

Pop stash if it was auto-stashed:
```bash
git stash pop
```

## Argument Parsing

- `--rebase`: Use rebase instead of merge
- `--base <branch>`: Specify the base branch (default: auto-detect)
- `--upstream`: Sync from `upstream` remote instead of `origin` (fork workflow)
- `--stash`: Auto-stash dirty changes before sync, pop after

## Important Notes

- **NEVER force push to main/master** — regardless of flags or user insistence
- **Merge is safer** for shared branches; only rebase local-only branches
- **`--force-with-lease`** instead of `--force` to prevent overwriting others' work
- **Conflicts require manual resolution** — do not guess how to resolve them
- **Fork workflow**: requires `upstream` remote to be configured (`git remote add upstream <url>`)

## Examples

```bash
# Sync with main using merge (default)
/git-sync

# Sync with develop branch
/git-sync --base develop

# Rebase onto main (local-only branch)
/git-sync --rebase

# Sync, stashing local changes first
/git-sync --stash

# Fork sync: pull upstream changes into your fork
/git-sync --upstream --base main
```
