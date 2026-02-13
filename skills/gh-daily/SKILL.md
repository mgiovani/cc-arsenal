---
name: gh-daily
description: Generate smart standup reports from GitHub Issues activity and git history.
  This skill should be used when users want to prepare for daily standups, generate
  activity reports, or summarize recent work across GitHub Issues, pull requests,
  and git commits.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
---

# Gh Daily

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# GitHub Daily - Standup Meeting Preparation

Smart standup report generator that analyzes GitHub Issues activity, pull requests, notifications, and git history to provide structured updates for daily meetings.

## Anti-Hallucination Guidelines

**CRITICAL**: Standup reports must reflect ACTUAL work done:
1. **Only list real issues** - Every issue/PR must come from `gh` CLI output
2. **Verify completion** - Only mark as "Completed" if state is `closed` or PR is `merged`
3. **Real commit counts** - Use actual `git log` output, never estimate
4. **Actual blockers** - Only mention blockers explicitly labeled or commented in GitHub
5. **True metrics** - All numbers from actual GitHub and git data

## Context Detection

### Phase 1: Determine Repository and User

Detect the working context in order of priority:
1. **Command argument**: `--repo owner/repo` or `-r owner/repo`
2. **Current git remote**: Parse from `git remote get-url origin`
3. **gh CLI default**: Use `gh repo view --json nameWithOwner -q .nameWithOwner`

```bash
# Detect current repo from git remote
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
 echo "ERROR: Not in a GitHub repository. Use --repo owner/repo to specify."
fi
echo "Detected repo: $REPO"

# Detect authenticated user
GH_USER=$(gh api user -q .login 2>/dev/null)
echo "Authenticated as: $GH_USER"
If no repo is detected and none provided, ask the user to specify with `--repo owner/repo`.

If the user works across multiple repos, offer to scan all repos where they have recent activity:
```bash
# Find repos with recent activity (issues assigned to user)
gh search issues --assignee @me --state open --limit 20 --json repository --jq '[.[].repository.nameWithOwner] | unique | .[]'
## Workflow

### Phase 2: Calculate Date Range

```bash
# Calculate since date (yesterday, or Friday if today is Monday)
if [[ $(date +%u) == 1 ]]; then
 # Monday - report from Friday
 SINCE_DATE=$(date -v-3d +%Y-%m-%d 2>/dev/null || date -d "3 days ago" +%Y-%m-%d)
else
 # Other days - report from yesterday
 SINCE_DATE=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
fi
echo "Reporting since: $SINCE_DATE"
### Phase 3: Gather Activity Data

```bash
# Get issues assigned to me (open)
gh issue list --assignee @me --state open --json number,title,state,labels,milestone,updatedAt,createdAt --limit 50

# Get issues closed recently (by me)
gh issue list --assignee @me --state closed --json number,title,state,labels,closedAt,milestone --limit 20 | jq --arg since "$SINCE_DATE" '[.[] | select(.closedAt >= $since)]'

# Get PRs authored by me (open)
gh pr list --author @me --state open --json number,title,state,reviewDecision,isDraft,labels,updatedAt --limit 30

# Get PRs merged recently
gh pr list --author @me --state merged --json number,title,mergedAt,labels --limit 20 | jq --arg since "$SINCE_DATE" '[.[] | select(.mergedAt >= $since)]'

# Get PRs where my review is requested
gh pr list --search "review-requested:@me" --state open --json number,title,author,updatedAt,labels --limit 20

# Get notifications (mentions, review requests, assignments)
gh api notifications --jq '.[] | select(.unread == true) | {reason: .reason, title: .subject.title, type: .subject.type, url: .subject.url}'

# Get git activity
git log --author="$(git config user.email)" --since="$SINCE_DATE" --oneline --all --no-merges

# Count commits and files changed
git rev-list --count --since="$SINCE_DATE" --author="$(git config user.email)" --all 2>/dev/null || echo "0"
git diff --stat $(git log --since="$SINCE_DATE" --author="$(git config user.email)" --format=%H --all | tail -1)..HEAD --shortstat 2>/dev/null
### Phase 4: Analyze with SubAgents (For Comprehensive Reports)

For detailed format, use parallel analysis:

```
Agent 1 - Work Classification:
- prompt: "Classify these GitHub issues and PRs into: Completed (closed/merged since date), In Progress (open, recently updated), Blocked (has 'blocked' label or mentioned in comments), Review Needed (PRs awaiting review). Base ONLY on actual state/label fields. Return categorized list."
- agent-type: "general-purpose"

Agent 2 - Impact Analysis:
- prompt: "For completed issues and merged PRs, summarize the business/technical impact based on title, labels, and milestone context. Keep it factual."
- agent-type: "general-purpose"

Agent 3 - Git Correlation:
- prompt: "Match git commits to GitHub issues/PRs by issue number in commit messages (e.g., #123, fixes #456). Report which issues have code changes and quantify work per issue."
- agent-type: "Explore"
### Phase 5: Generate Report

Track sections completed with TodoWrite.

## Priority Scoring

When analyzing issues, score them using these factors:

- **Label Priority**: `priority: critical` or `P0` = x10, `priority: high` or `P1` = x7, `priority: medium` or `P2` = x4
- **Milestone Proximity**: Days until milestone due date (lower = higher score)
- **Issue Age**: Stale issues (>7 days no update) get flagged
- **Blocking Status**: Has `blocked` or `blocking` label = +5 points
- **Review Requested**: PRs where your review is pending = +3 points
- **Bug vs Feature**: Issues labeled `bug` with high priority = +4 points
- **Mentions/Comments**: Recent @mentions or comments = +2 points

## Output Formats

For detailed output format templates (default, brief, slack), see [references/output-formats.md](references/output-formats.md).

**Available formats:**
- **Default (Detailed)**: Full report with completed work, in-progress items, PRs, blockers, metrics, and schedule
- **Brief** (`--format brief`): Concise one-line-per-section format for quick standups
- **Slack** (`--format slack`): Formatted for Slack/Teams posting with markdown

## Command Options

### `--repo <owner/repo>` or `-r <owner/repo>`
Specify the GitHub repository explicitly.
```bash
gh-daily --repo myorg/myapp
### `--since <date>`
Override the automatic date calculation.
```bash
gh-daily --since 2025-01-20
### `--format <format>`
Choose output format for different audiences.
```bash
gh-daily --format brief # Concise version for quick standups
gh-daily --format detailed # Full version with technical details (default)
gh-daily --format slack # Formatted for Slack/Teams posting
### `--all-repos`
Scan all repos where you have recent assigned issues, not just the current repo.
```bash
gh-daily --all-repos
### `--include-reviews`
Include PRs where your review was requested (shown separately by default only in detailed format).
```bash
gh-daily --format brief --include-reviews
## Smart Features

### Context Awareness
- Detect Monday condition and report from last Friday
- Identify milestone boundaries and adjust progress tracking
- Recognize critical/blocking issues via labels and highlight urgency
- Correlate git commits with GitHub issue references (`#123`, `fixes #456`)
- Detect cross-repo activity when using `--all-repos`

### Progress Intelligence
- Calculate milestone completion percentage
- Compare current throughput to recent averages
- Identify patterns in blocking issues
- Track code review participation and response times

### Goal Alignment
- Map completed work to milestone objectives
- Highlight work that unblocks teammates
- Identify contributions to team goals
- Suggest proactive communications

## Integration Points

### With gh-todo Skill
- Reference yesterday's planned work vs. actual completion
- Update priority recommendations based on standup outcomes

### With git-commit / git-create-pr Skills
- Parse commit messages for automatic work categorization
- Link git branches to issues for complete picture
- Integrate with PR status for review workflow visibility

### With Development Tools
- Check current git branch for active issue context
- Correlate file changes with issue scope
- Identify stale branches needing cleanup

## Usage Examples

```bash
# Basic usage (auto-detects repo, yesterday's activity)
gh-daily

# Specify repo explicitly
gh-daily --repo myorg/backend

# Quick standup format
gh-daily --format brief

# For Slack posting
gh-daily --format slack

# Custom date range
gh-daily --since 2025-01-15

# All repos you contribute to
gh-daily --all-repos

# Weekly summary
gh-daily --since $(date -v-7d +%Y-%m-%d 2>/dev/null || date -d "7 days ago" +%Y-%m-%d)
## Daily Routine Integration

### Morning Preparation (5 minutes)
```bash
gh-daily --format brief
# Review and adjust for accuracy
# Copy to standup notes
### Standup Meeting (2 minutes per person)
- Read directly from generated report
- Add context or clarifications as needed
- Note any team dependencies or offers to help

### Weekly Summary
```bash
gh-daily --since $(date -v-7d +%Y-%m-%d 2>/dev/null || date -d "7 days ago" +%Y-%m-%d) --format detailed
## Quality Checklist

The report ensures the standup covers:
- [ ] Concrete accomplishments with business impact
- [ ] Clear current work with scope context
- [ ] Specific blockers with escalation plans
- [ ] PR review status and pending reviews
- [ ] Milestone/goal alignment and risk identification
- [ ] Proactive communication about dependencies

## Important Notes

- **Requires gh CLI**: Install from https://cli.github.com/ and authenticate with `gh auth login`
- **Authentication**: Must be logged in (`gh auth status` to verify)
- **Repository context**: Auto-detected from git remote or specify with `--repo`
- **Git integration**: Uses local git repository for commit analysis
- **Real data only**: All metrics based on actual GitHub and git data
- **Rate limits**: GitHub API has rate limits; `gh` CLI handles pagination automatically
