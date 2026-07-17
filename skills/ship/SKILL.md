---
name: ship
description: Orchestrates the current branch from "code done" to "merged" — runs
  the review-code skill, then any project-specific pre-merge checks it can detect
  (visual regression like `just visual-diff`, test suites, lint), then a conventional
  commit following the git-commit skill's conventions, then a PR following the
  git-create-pr skill's conventions, then optionally watches CI and reports or merges
  on green. Use when the user says "ship it", "ship this", "ship train", "get this
  merged", "run the ship workflow", or wants the whole review-to-merge pipeline run
  in one go instead of one step at a time. Reuses the sibling skills rather than
  reimplementing them — stops and reports on the first red gate (failing review,
  failing check, red CI) instead of pushing through. Not for a single step in
  isolation — use review-code for review only, git-commit for a commit only,
  git-create-pr for a PR only. Not for gitflow branch topology questions (feature
  vs release vs hotfix roles, versioning, promoting dev to main) — use gitflow for
  that; ship is the mechanical pipeline for landing whatever is on the current
  branch, regardless of branching model.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: "[--no-merge] [--base branch]"
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Bash(just *), Bash(make *), Bash(npm *), Bash(pnpm *), Bash(bun *), Bash(yarn *), Task, TodoWrite, Skill, AskUserQuestion
---

# Ship

Take the current branch from "code done" to "merged" in one pass. This is a thin orchestrator: every step delegates to the sibling skill that already owns that logic. Do not re-implement review rules, commit conventions, or PR templates here — invoke the skill.

## The train

Run these in order. Stop at the first red gate and report it — do not skip a step or push through a failure.

| # | Step | How |
|---|------|-----|
| 1 | Pre-flight | Confirm there's a diff to ship, working tree state, target base branch |
| 2 | Code review | Invoke the `review-code` skill on the current diff |
| 3 | Pre-merge checks | Auto-detect and run project checks (tests, lint, visual diff) |
| 4 | Commit | Invoke the `git-commit` skill's conventions |
| 5 | PR | Invoke the `git-create-pr` skill's conventions |
| 6 | CI + merge | Watch CI (optional), report or merge on green |

Track progress with `TodoWrite` (one line per step above) so the user sees where the train is if a gate stops it.

## Step 1: Pre-flight

- `git branch --show-current` — refuse to run on `main`/`master`/`dev` directly (nothing to ship from a target branch).
- `git status --porcelain` — if dirty, ask whether to include the changes or stop.
- Determine base branch: use `--base` if given, else `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `main`.
- `git log <base>..HEAD --oneline` — if empty, there's nothing to ship; stop and say so.

## Step 2: Code review

Invoke the `review-code` skill (via the `Skill` tool) scoped to the diff against the base branch. This is analysis only — it does not touch files.

- Any **Critical/High** finding: stop, report it with file:line, and let the user decide (fix and re-run, or explicitly accept the risk). Do not proceed silently.
- Medium/Low findings: report them but continue — they don't block the train.

## Step 3: Pre-merge checks (auto-detected)

The project's own gates matter more than a generic test run. Detect what's actually configured before running anything — never invent a command:

1. `justfile` — look for `visual-diff`, `test`, `check` recipes (`just --list` if present).
2. `Makefile` — look for `test`, `check`, `lint` targets.
3. `package.json` — look at `scripts` for `test`, `lint`, `typecheck`, `e2e`.
4. Framework-native fallback (`pytest`, `cargo test`, etc.) only if none of the above exist.

A Haiku `Explore` subagent is the cheap way to do this detection without burning main-thread context:

```
Task tool with Explore agent:
- prompt: "Find pre-merge check commands for this repo: look for a justfile
    (especially a visual-diff or visual regression recipe), Makefile targets,
    and package.json scripts. Return the exact commands to run, do not invent any."
- subagent_type: "Explore"
- model: "haiku"
```

Run every command found. Any non-zero exit: stop, show the failing output, do not proceed to commit. This includes visual regression diffs — a passing test suite with a failing visual diff is still a red gate.

## Step 4: Commit

Follow the `git-commit` skill's conventions (invoke it if available, otherwise apply the same rules inline): Conventional Commits format, imperative mood, stage only the files that belong to this change, split into multiple commits if the diff mixes unrelated concerns.

## Step 5: Pull request

Follow the `git-create-pr` skill's conventions (invoke it if available, otherwise apply the same rules inline): conventional-commit-style title, PR body filled from the actual commits/diff (no invented claims), push the branch, open against the base branch determined in Step 1.

## Step 6: CI + merge (optional)

- If `--no-merge` was passed, or the user only asked to get the PR open, stop here and report the PR URL.
- Otherwise watch CI: `gh pr checks <number> --watch` or poll `gh pr checks <number>` every couple of minutes — don't tight-loop.
- **Red CI**: stop, show the failing check name and a log excerpt, do not merge, do not retry blindly.
- **Green CI**: only merge if the user asked to get this merged (e.g. "get this merged", "merge when green") or confirms when asked. Otherwise just report green and let the user merge themselves.
- When merging, use squash unless the repo's own convention says otherwise (check for a CONTRIBUTING.md or existing merge history via `gh pr list --state merged --limit 5`). Never force-push, never bypass hooks or required checks to get a merge through.

## Reporting

After each stopped or completed run, summarize: which step the train reached, what passed, what's still open, and the PR URL if one was created. If everything went green and merged, say so plainly — the user should not have to re-check `gh pr view`.
