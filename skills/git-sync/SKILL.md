---
name: git-sync
description: Syncs the current feature branch with its base or upstream branch via merge (default) or rebase, with conflict detection and stash handling. Use for ad-hoc requests like "sync my branch with main", "rebase onto main", "rebase on latest dev", "pull upstream into my fork", or "update my branch". Not for release/hotfix branch promotion or cutting versioned releases — use gitflow or git-release for those.
metadata:
  author: mgiovani
  version: 1.1.0
argument-hint: '[--rebase] [--base main] [--upstream] [--stash]'
allowed-tools:
- Bash(git *)
- Bash(gh pr view*)
- Read
- AskUserQuestion
---

# Git Sync

Sync the current branch with its base or upstream branch. Defaults to merge to preserve history; rebase is opt-in only. Only ever act on what `git status` and `git log` actually show — never guess branch state or conflicts.

## Workflow

### Phase 1: Detect & Decide

Run the following to understand current branch state:

```bash
git branch --show-current
git status --porcelain
git remote -v
git log --oneline HEAD..origin/main 2>/dev/null | head -20
git log --oneline origin/main..HEAD 2>/dev/null | head -20
```

Also check whether the branch is pushed to remote (`git log origin/<branch>..HEAD` — an error means local-only).

**Determine the base branch** (once, reuse the result for the rest of the run):
1. User passed `--base <branch>` — use it.
2. Otherwise `gh pr view --json baseRefName -q .baseRefName 2>/dev/null` (if an open PR exists).
3. Otherwise `git config branch.<name>.merge`.
4. Otherwise ask the user which base branch to use.

Determine sync strategy:

**Merge (default)** — use when the branch has been pushed to remote, the user did not pass `--rebase`, or you are unsure.

**Rebase (opt-in)** — use only when the user explicitly passed `--rebase`.

**Fork sync** (`--upstream`) — sync from the `upstream` remote instead of `origin`: `git fetch upstream && git merge upstream/<base>`.

Display the detected state and proposed strategy before proceeding:

```
Current branch: feature/my-feature
Base branch:    main
Strategy:       merge (default)
Commits behind: 5
Commits ahead:  2
Dirty tree:     no
```

### Phase 2: Pre-sync Safety

1. **Dirty working tree**: with `--stash`, run `git stash push -m "git-sync auto-stash"` before syncing. Without `--stash`, abort and tell the user to commit, stash, or re-run with `--stash`.
2. **Fetch latest**: `git fetch origin` (and `git fetch upstream` for fork sync).
3. **Re-check divergence** after fetch so the numbers you report are accurate, not the pre-fetch snapshot.

### Phase 3: Execute & Report

**Merge**: `git merge origin/<base>`

**Rebase, local-only branch**: `git rebase origin/<base>`

**Rebase, pushed branch** — warn before rewriting shared history:

```
WARNING: This branch has been pushed to remote.
Rebasing will require a force-push, which rewrites history.
This is ONLY safe if no one else has pulled this branch.
Proceed? [y/N]
```

If confirmed:
```bash
git rebase origin/<base>
git push --force-with-lease origin <branch>
```

**On merge/rebase conflict** — do not guess how to resolve them:
1. `git diff --name-only --diff-filter=U` to list conflicting files.
2. Report the exact file list, e.g.:
   ```
   Conflicts in 2 files:
     src/api/client.ts
     src/api/types.ts
   Resolve manually, then run `git merge --continue` (or `git rebase --continue`).
   Or run `git merge --abort` (or `git rebase --abort`) to back out.
   ```
3. Stop and wait — do not attempt automatic resolution.

**After a successful sync**:
1. If a stash was auto-created in Phase 2, pop it now: `git stash pop`. If the pop itself conflicts, report those conflicting files the same way as a merge conflict.
2. Gather real numbers, don't estimate:
   ```bash
   git log --oneline -5
   git log --oneline origin/<base>..HEAD | wc -l
   ```
3. Report, using only values from the commands above:
   ```
   Synced feature/my-feature onto main (merge).
   Now 2 commits ahead of main, 0 behind.
   Stash popped cleanly.
   ```
   Include whether force-push was used, and mention `git rerere` if conflicts occurred during this run.

## Argument Parsing

- `--rebase`: use rebase instead of merge
- `--base <branch>`: specify the base branch (default: auto-detect)
- `--upstream`: sync from `upstream` remote instead of `origin` (fork workflow)
- `--stash`: auto-stash dirty changes before sync, pop after

## Important Notes

- **Never force push to main/master**, regardless of flags or user insistence.
- Merge is the safe default for shared branches; only rebase branches you're sure are local-only or where the user explicitly accepted the force-push warning.
- Use `--force-with-lease`, never bare `--force`, so a rebase-push can't clobber someone else's commits.
- Fork workflow requires the `upstream` remote to already be configured (`git remote add upstream <url>`).

## Examples

```bash
# Sync with main using merge (default)
/git-sync

# Sync with develop branch
/git-sync --base develop

# Rebase onto main (will warn if branch is already pushed)
/git-sync --rebase

# Sync, stashing local changes first
/git-sync --stash

# Fork sync: pull upstream changes into your fork
/git-sync --upstream --base main
```
