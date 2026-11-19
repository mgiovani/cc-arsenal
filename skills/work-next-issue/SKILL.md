---
name: work-next-issue
description: Takes the next open issue from pick to pull request in one run. Picks the next unblocked issue, makes a fresh worktree, plans, reviews the plan, implements, reviews the diff, fixes the findings and opens the PR. Use for "work the next issue", "pick up the next ticket", "what should I build next and do it", or an unattended backlog run. Works with GitHub issues, beads, Linear or Jira. Stops at the PR, never merges. Not for a branch that is already implemented (use ship), one feature or issue you name (use implement-feature or fix-bug), turning a PRD into issues (use prd-to-issues), or splitting a project into tasks (use project-planner or orchestrate).
metadata:
  summary: "Pick the next unblocked issue, then plan, build, review and open the PR with sibling skills"
---

# Work the Next Issue

Take one issue from the backlog to an open pull request. This skill only sequences sibling skills and adds no review logic of its own: each stage runs the skill that owns it. A run handles one issue and ends at the PR.

## Stage checklist

Copy this list and tick each stage. A red gate stops the run; report it instead of pushing on.

```
- [ ] 1. Pick the issue, state the pick and the reason
- [ ] 2. Create a worktree off the up-to-date default branch
- [ ] 3. Plan (implement-feature, planning phase)
- [ ] 4. Review the plan (review-plan), fix what it finds
- [ ] 5. Implement (implement-feature, or fix-bug for a bug)
- [ ] 6. Review the diff (review-code, every lane that applies)
- [ ] 7. Fix every finding, file the out-of-scope ones as new issues
- [ ] 8. Open the PR (git-create-pr) linking the issue
```

## 1. Pick

Detect the tracker from the repo: a `.beads/` directory means beads, a GitHub remote means `gh`, and a Linear or Jira key in branch names or the project config means that tool. If two fit, use the one the project docs name. If none fits, report that no tracker was found and stop.

| Tracker | Candidates | Blockers and in-progress |
|---|---|---|
| GitHub | `gh issue list --state open --json number,title,labels,milestone,assignees` | `gh api repos/{owner}/{repo}/issues/<n>/dependencies/blocked_by`, or "blocked by #N" in the body; assigned or `in progress` labelled means taken |
| beads | `bd ready --json` | `bd list --status in_progress`; `bd show <id>` lists dependents |
| Linear | `list_issues` through the Linear tool, filtered to unstarted | relations on each issue; a started status means taken |
| Jira | `jira issue list` (jira-cli) or the Jira tool, status To Do | linked "is blocked by" issues; In Progress means taken |

An issue is unblocked when every blocker is closed. Order the unblocked set:

1. P0 first (label or priority field).
2. Skip anything already in progress.
3. Then the issue that unblocks the most others, or the nearest deadline or milestone due date.

State the pick in one line with its reason, for example "#42, P0, unblocks 3 issues". If the top two differ only by a tie-break, take the lowest issue number and say so, so an unattended run never waits on a question. If the set is empty, report what blocks the nearest issue and stop.

## 2. Worktree

Never work in the main checkout; a failed run then leaves it untouched.

```bash
base=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||')
git fetch origin "$base"
git worktree add ../<repo>-<issue-id> -b <type>/<issue-id>-<slug> "origin/$base"
```

Use the project's branch naming when it has one (the ticket key in the branch lets `git-create-pr` find it). If both lookups fail, stop with an error rather than guess the base. If the worktree or branch already exists, reuse it when it is clean and belongs to the same issue, and stop and report when it holds uncommitted work. Do all later work inside the worktree. If the project already has a worktree convention, follow that.

## 3. Plan

Say "Using implement-feature to plan the issue", then invoke it via the skill tool where available, otherwise apply its SKILL.md steps inline. Stop after its discovery, research and planning phases. Feed it the issue body, comments and acceptance criteria. Stop before its approval step and hold the plan; stage 5 resumes at its Phase 3, so the earlier phases do not run twice.

For a bug, plan with fix-bug's analysis, reproduction and fix planning phases (1-2) instead. A bug is an issue labelled `bug` or one that reports wrong behaviour of existing code.

## 4. Review the plan

Say "Using review-plan to attack the plan against the repository", then invoke it via the skill tool where available, otherwise apply its SKILL.md steps inline. A plan has no diff for review-code to read, so review-plan is the sibling built for it. Tell the user why you chose it.

Pass it the plan and the repo, not your reasoning, since it works by not seeing the author's justification. Fix every `blocker` and `gap` in the plan. Re-run review-plan after fixing. After 2 rounds with a blocker left, stop and report it; list any leftover gap in the PR body. Then take the plan approval that implement-feature asks for.

## 5. Implement

Say "Using implement-feature to build the approved plan" (fix-bug for a bug), then invoke it via the skill tool where available, otherwise apply its SKILL.md steps inline. Start at Phase 3 with the held plan and skip the earlier phases. Run the project's tests, lint and type checks as those skills direct. Failing tests are a red gate: fix them within 3 rounds, then stop and report the failure output.

## 6. Review the diff

Say "Using review-code to review the branch diff", then invoke it against the base via the skill tool where available, otherwise apply its SKILL.md steps inline. Let it pick lanes from the diff, and include every lane that applies: security, dependencies, deep performance, design. Do not narrow it to save time.

## 7. Fix or file

Fix every finding in this branch, Nit included, then re-run the affected checks and re-run step 6 once. After 2 review rounds, an unresolved Critical finding is a red gate: stop and report it, and list any unresolved Major finding in the PR body.

A finding that is out of scope for the issue does not get fixed here. File it as a new issue in the same milestone, with labels, and link it from the PR:

```bash
gh issue create --title "<finding>" --body "<file:line, why, found while working #<n>>" \
  --milestone "<same milestone>" --label "<labels>"
# beads: bd create "<finding>" -d "<file:line, why>" -p 2
```

Check the issue did not already exist before filing. If the pick had no milestone, say so in the PR and use the labels alone.

## 8. Open the PR

Say "Using git-create-pr to open the pull request", then invoke it via the skill tool where available, otherwise apply its SKILL.md steps inline. Commit first with the git-commit conventions if work is uncommitted. The body must link the issue (`Closes #<n>` on GitHub, the key for Linear or Jira, the id for beads) and list any follow-up issues from step 7.

## Rules

- Stop at the PR. Merging belongs to the owner, or to ship when asked. A merge here would skip the human gate.
- Leave the issue open and unedited by hand. The merge closes it through the PR link; a manual close hides unfinished work.
- Start a second issue only in a new run. One issue per run keeps the failure surface small.
- Report each gate with the command you ran and its real output. A stage you skipped is reported as skipped with the reason, never as passed.
- For an unattended run, set a call budget and stop after 2 consecutive crashes instead of relaunching.
- Finish with the issue, the branch, the worktree path, the PR link and the follow-up issues.
