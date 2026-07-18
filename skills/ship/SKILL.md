---
name: ship
description: >-
  Orchestrates the current branch from "code done" to "merged" — runs the
  review-code skill, then any project-specific pre-merge checks it detects
  (visual regression like `just visual-diff`, tests, lint), then a conventional
  commit per git-commit, a PR per git-create-pr, and optionally watches CI and
  merges on green. Use when the user says "ship it", "ship this", "ship train",
  "get this merged", or wants the whole review-to-merge pipeline in one go.
  Reuses the sibling skills and stops on the first red gate (failing review,
  failing check, red CI). Owns "ship it" for the default case — a feature branch
  merging straight to its base. Not for a single step in isolation (use
  review-code, git-commit, or git-create-pr directly). Not for release/hotfix
  branch topology, versioning, or promoting dev to main — use gitflow for that,
  including "ship it" said in a repo that runs gitflow.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: "[--no-merge] [--base branch]"
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Bash(just *), Bash(make *), Bash(npm *), Bash(pnpm *), Bash(bun *), Bash(yarn *), Task, TodoWrite, Skill, AskUserQuestion
---

# Ship

Take the current branch from "code done" to "merged" in one pass. This is a thin orchestrator: every step delegates to the sibling skill that already owns that logic. Do not re-implement review rules, commit conventions, or PR templates here — invoke the skill.

## Pipeline integrity

Every stage's reported result must quote the actual command you ran and its actual exit status or output. A stage you did not run is reported as **SKIPPED: <reason>** — never as passed, never estimated, never inferred from a similar-looking earlier run. The whole value of a ship train is that green means green; one fabricated gate poisons every stage after it, because the human trusts stage 6 only because they trust stages 1-5.

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
- `git status --porcelain` — if dirty, use `AskUserQuestion` (or ask in plain text if that tool isn't available) whether to include the changes or stop.
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

No `Task` tool available: run the same detection inline — `just --list` (or read the justfile), `grep` the Makefile's target names, `cat` `package.json`'s `scripts` block — then run whatever it finds directly.

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

Every report — stopped or completed — ends with a stage table: `# | Stage | Command | Result`. One row per step in "The train", in order. `Command` is the literal command (or skill invocation) you actually ran for that stage; `Result` is its actual exit status or a one-line summary of its actual output. Any stage not reached gets `Command: —` and `Result: SKIPPED: not reached`. This table is what makes fabrication visible — never fill a row from what a stage "should" produce, only from what it did.

If everything went green and merged, say so plainly — the user should not have to re-check `gh pr view`. Every number, check name, or pass/fail verdict in the table must come from a command actually run this session.

### Example: stopped at code review (Step 2)

```
Ship train stopped at step 2/6 — code review.

| # | Stage        | Command                          | Result                              |
|---|--------------|-----------------------------------|--------------------------------------|
| 1 | Pre-flight   | git log main..HEAD --oneline     | 4 commits ahead — OK                 |
| 2 | Code review  | Skill: review-code (diff vs main)| 1 High: session.ts:42 uses `==` on token — BLOCKED |
| 3 | Pre-merge    | —                                 | SKIPPED: not reached                 |
| 4 | Commit       | —                                 | SKIPPED: not reached                 |
| 5 | PR           | —                                 | SKIPPED: not reached                 |
| 6 | CI + merge   | —                                 | SKIPPED: not reached                 |

Fix the finding and re-run, or tell me to accept the risk and continue.
```

### Example: stopped at a pre-merge check (Step 3)

```
Ship train stopped at step 3/6 — pre-merge checks.

| # | Stage        | Command            | Result                                  |
|---|--------------|---------------------|------------------------------------------|
| 1 | Pre-flight   | git log main..HEAD  | 6 commits ahead — OK                    |
| 2 | Code review  | Skill: review-code  | 0 Critical/High — OK                    |
| 3 | Pre-merge    | just visual-diff     | exit 1, 3 snapshots differ — BLOCKED    |
| 4 | Commit       | —                    | SKIPPED: not reached                    |
| 5 | PR           | —                    | SKIPPED: not reached                    |
| 6 | CI + merge   | —                    | SKIPPED: not reached                    |

Fix the diffs (or run `just visual-update` if they're intended) and re-run.
```

### Example: full train, merged on green

```
Ship train complete — merged.

| # | Stage        | Command                                    | Result                                   |
|---|--------------|---------------------------------------------|--------------------------------------------|
| 1 | Pre-flight   | git log main..HEAD --oneline               | feature/search-filters, 4 commits ahead    |
| 2 | Code review  | Skill: review-code (diff vs main)          | 0 Critical/High, 2 Low (non-blocking)      |
| 3 | Pre-merge    | just test; just visual-diff                | 42 passed; 0 diffs                          |
| 4 | Commit       | git commit -m "feat(search): ..."          | committed 4f2a91c                           |
| 5 | PR           | gh pr create ...                            | https://github.com/org/repo/pull/213        |
| 6 | CI + merge   | gh pr checks 213 --watch; gh pr merge --squash | lint/test/build green — squash-merged  |
```
