---
name: gh-daily
description: Generate a GitHub-based standup report from assigned issues, open/merged PRs, review requests, and git commit history. Use when the user asks for a standup, daily update, or status report and works with GitHub Issues/PRs. Trigger phrases include "standup report", "daily update", "what did I do yesterday", "GitHub status report". Not for Jira-based standups (use jira-daily), gh-daily is GitHub-only and never queries Jira.
metadata:
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
---

# GitHub Daily - Standup Meeting Preparation

Generates a standup report from GitHub Issues, PRs, notifications, and git history.

## Anti-Hallucination Guidelines

Standup reports must reflect actual work done, not guesses:
1. Only list issues/PRs that came back from `gh` CLI output.
2. Only mark "Completed" if state is `closed` or PR is `merged`.
3. Use real `git log` counts, never estimate.
4. Only mention blockers that are explicitly labeled or commented in GitHub.
5. Only include a report section if Phase 3 actually gathered data for it. Never fill a section with placeholder text like "[List any risks]": omit the section entirely instead.

## Phase 1: Determine Repository and User

Detect context in order of priority: `--repo owner/repo` argument, current git remote, then `gh` CLI default.

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
  echo "ERROR: Not in a GitHub repository. Use --repo owner/repo to specify."
fi
echo "Detected repo: $REPO"

GH_USER=$(gh api user -q .login 2>/dev/null)
echo "Authenticated as: $GH_USER"
```

If no repo is detected and none provided, ask the user to specify with `--repo owner/repo`.

If `--all-repos` is passed, skip the single-repo detection above and instead collect the repo list to scan:

```bash
REPOS=$(gh search issues --assignee @me --state open --limit 20 --json repository --jq '[.[].repository.nameWithOwner] | unique | .[]')
```

Run Phase 3 once per repo in `$REPOS`, passing each as `--repo` in turn, and concatenate the results before Phase 4. Without `--all-repos`, `$REPO` is a single value and every Phase 3 command below must pass `--repo "$REPO"`.

## Phase 2: Calculate Date Range

```bash
# Report from Friday if today is Monday, otherwise from yesterday
if [[ $(date +%u) == 1 ]]; then
  SINCE_DATE=$(date -v-3d +%Y-%m-%d 2>/dev/null || date -d "3 days ago" +%Y-%m-%d)
else
  SINCE_DATE=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
fi
echo "Reporting since: $SINCE_DATE"
```

`--since <date>` overrides `$SINCE_DATE` directly.

## Phase 3: Gather Activity Data

Every `gh issue`/`gh pr` command below takes `--repo "$REPO"` (or the current repo in the `--all-repos` loop): omitting it lets `gh` fall back to whatever repo the CLI feels like, silently pulling data for the wrong project.

```bash
# Issues assigned to me (open)
gh issue list --repo "$REPO" --assignee @me --state open --json number,title,state,labels,milestone,updatedAt,createdAt --limit 50

# Issues closed recently (by me)
gh issue list --repo "$REPO" --assignee @me --state closed --json number,title,state,labels,closedAt,milestone --limit 20 | jq --arg since "$SINCE_DATE" '[.[] | select(.closedAt >= $since)]'

# PRs authored by me (open)
gh pr list --repo "$REPO" --author @me --state open --json number,title,state,reviewDecision,isDraft,labels,updatedAt --limit 30

# PRs merged recently
gh pr list --repo "$REPO" --author @me --state merged --json number,title,mergedAt,labels --limit 20 | jq --arg since "$SINCE_DATE" '[.[] | select(.mergedAt >= $since)]'

# Git activity
git log --author="$(git config user.email)" --since="$SINCE_DATE" --oneline --all --no-merges
git rev-list --count --since="$SINCE_DATE" --author="$(git config user.email)" --all 2>/dev/null || echo "0"
```

Run these two only when reviews are in scope, always for `--format detailed` (the default), and for any other format when `--include-reviews` is passed. Skip them otherwise; don't spend the extra API calls on a report that won't use the data.

```bash
# PRs where my review is requested
gh pr list --repo "$REPO" --search "review-requested:@me" --state open --json number,title,author,updatedAt,labels --limit 20

# Unread notifications (mentions, review requests, assignments)
gh api notifications --jq '.[] | select(.unread == true) | {reason: .reason, title: .subject.title, type: .subject.type, url: .subject.url}'
```

## Phase 4: Classify and Score

Classify each issue/PR from the JSON already gathered above: no subagents needed, this is a direct pass over data you already have:
- **Completed**: state is `closed` (issues) or `merged` (PRs) since `$SINCE_DATE`.
- **In Progress**: open, `updatedAt` within the window.
- **Blocked**: has a `blocked`/`blocking` label or a comment mentioning a blocker.
- **Review Needed**: open PRs from the review-requested query (only present when reviews were gathered in Phase 3).

Match git commits to issues/PRs by number references in commit messages (`#123`, `fixes #456`) to show which issues have code changes.

Optionally prioritize within each category using label/milestone signals: `priority: critical`/`P0` and `blocked` labels surface first, then items closest to a milestone due date, then stale items (>7 days no update).

## Phase 5: Generate Report

Track sections completed with TodoWrite, then render using one of the formats below. Every section in the template is conditional on having matching data from Phase 3/4: a report with nothing blocked has no Blockers section, a report with no milestone data has no Milestone section. Never invent numbers or fill a heading with placeholder brackets to keep a section "complete."

## Output Formats

For the default, brief, and slack templates, see [references/output-formats.md](references/output-formats.md) (load when rendering the final report).

- **Default (detailed)**: full report with completed work, in-progress items, PRs, blockers, reviews requested.
- **Brief** (`--format brief`): one line per section, for quick standups.
- **Slack** (`--format slack`): markdown formatted for posting in Slack/Teams.

## Command Options

- `--repo <owner/repo>` / `-r <owner/repo>`: specify the repository explicitly.
- `--since <date>`: override the automatic date calculation, e.g. `--since 2025-01-20`.
- `--format <brief|detailed|slack>`: choose output format (default: detailed).
- `--all-repos`: scan all repos where you have recent assigned issues (see Phase 1); runs Phase 3 once per repo.
- `--include-reviews`: include PRs where your review was requested. Detailed format gathers this by default; brief and slack need the flag to include it.

## Usage Examples

```bash
gh-daily                                                              # auto-detect repo, yesterday's activity
gh-daily --repo myorg/backend                                        # specify repo
gh-daily --format brief                                               # quick standup
gh-daily --format slack                                               # for Slack posting
gh-daily --since 2025-01-15                                            # custom date range
gh-daily --all-repos                                                   # all repos you contribute to
gh-daily --since $(date -v-7d +%Y-%m-%d 2>/dev/null || date -d "7 days ago" +%Y-%m-%d) --format detailed  # weekly summary
```

## Important Notes

- Requires `gh` CLI installed and authenticated (`gh auth login`, verify with `gh auth status`).
- Repository context is auto-detected from git remote or set with `--repo`.
- Git commit analysis uses the local git repository.
- All metrics come from actual GitHub and git data, never estimated.
- Not for Jira: this skill only talks to `gh`/`git`. Use `jira-daily` for a Jira-ticket-based standup, including in mixed environments where both trackers are in play.
