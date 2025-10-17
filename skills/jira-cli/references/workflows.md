# Jira CLI - Common Workflows

This file contains practical workflow examples for common Jira use cases and team collaboration scenarios.

## Daily Standup Preparation

Get quick answers for your daily standup:

```bash
# What did I work on yesterday?
jira issue list -a$(jira me) --updated -1d

# What am I working on today?
jira issue list -a$(jira me) -s"In Progress"

# What tickets did I close this week?
jira issue list -a$(jira me) -sDone --updated week

# Any blockers? (high priority issues assigned to me)
jira issue list -a$(jira me) -yHigh -s~Done
```

## Sprint Planning

Prepare for and manage sprint planning:

```bash
# High priority unassigned tickets (need assignment)
jira issue list -ax -yHigh

# Backlog items ready for sprint (ordered by rank like UI)
jira issue list -s"Ready for Dev" --order-by rank --reverse

# Current sprint progress
jira sprint list --current

# Current sprint with my tasks only
jira sprint list --current -a$(jira me)

# See what's planned for next sprint
jira sprint list --next

# Check sprint capacity (how many issues)
jira sprint list SPRINT_ID --plain --no-headers | wc -l
```

## Code Review Workflow

Integrate Jira with your code review process:

```bash
# 1. Create ticket for review
jira issue create -tTask -s"Code review: Feature X"

# 2. Link to related PR
jira issue link remote ISSUE-1 https://github.com/org/repo/pull/123 "PR #123"

# 3. Move to review status
jira issue move ISSUE-1 "In Review"

# 4. Add review comments
jira issue comment add ISSUE-1 "LGTM! Approved changes."

# 5. Close the ticket
jira issue move ISSUE-1 Done -RFixed
```

## Bug Triage

Efficient bug triage workflow:

```bash
# List new bugs from last week
jira issue list -tBug -sOpen --created -7d

# List critical/high priority bugs
jira issue list -tBug -yHighest,High -s~Done

# Assign high priority bug to team lead
jira issue assign BUG-123 "Team Lead"

# Add triage notes
jira issue comment add BUG-123 "Investigating root cause. Checking logs."

# Update priority and labels
jira issue edit BUG-123 -yHigh -lproduction -lurgent

# Link to related issues
jira issue link BUG-123 BUG-100 "is caused by"
```

## Epic Management Workflow

Working with epics effectively:

```bash
# Create a new epic for quarterly goals
jira epic create -n"Q1 2025 Goals" -s"Q1 Goals" -yHigh

# List open epics to see what's in progress
jira epic list -sOpen

# View all tasks in a specific epic
jira epic list EPIC-42

# Add new stories to the epic
jira issue create -tStory -s"User authentication" -PEPIC-42
jira epic add EPIC-42 STORY-100 STORY-101

# Check epic progress (how many done vs total)
jira epic list EPIC-42 -sDone --plain --no-headers | wc -l
jira epic list EPIC-42 --plain --no-headers | wc -l

# Remove completed stories from epic
jira epic remove STORY-98 STORY-99
```

## Release Management

Managing releases and versions:

```bash
# List all releases
jira release list

# List releases for specific project
jira release list --project MYPROJECT

# Create issues for a release
jira issue create -tBug -s"Release blocker" --fix-version v2.0

# Find all issues in a release
jira issue list --fix-version v2.0

# Find unresolved issues blocking release
jira issue list --fix-version v2.0 -s~Done
```

## Team Collaboration

Collaborate effectively with your team:

```bash
# See what your teammate is working on
jira issue list -a"John Doe" -s"In Progress"

# Find issues reported by PM for review
jira issue list -r"Jane PM" -s"To Do" --order-by priority

# Check team's completed work this week
jira issue list -a~x --updated week -sDone

# Find unassigned high priority work
jira issue list -ax -yHigh -s"To Do"

# Check who's working on what in current sprint
jira sprint list --current --plain --columns assignee,key,summary
```

## Incident Response

Handle production incidents:

```bash
# Create critical incident ticket
jira issue create -tBug -s"Production outage: API down" -yHighest -lincident -lproduction --no-input

# Link related issues
jira issue link INC-1 BUG-789 "is caused by"

# Add status updates
jira issue comment add INC-1 "Root cause identified. Rolling back deployment."

# Track time spent
jira issue worklog add INC-1 "2h" --comment "Incident response" --no-input

# Close incident
jira issue move INC-1 Done -RFixed --comment "Service restored. Post-mortem scheduled."
```

## Backlog Grooming

Keep your backlog organized:

```bash
# Find old unassigned tickets (potential cleanup candidates)
jira issue list -ax --created-before -12w -s"To Do"

# Find tickets with no recent activity
jira issue list --updated-before -8w -s~Done

# Find tickets missing labels or components
jira issue list -l~x -C~x

# Update stale tickets in bulk (interactive or scripted)
for issue in $(jira issue list -ax --created-before -12w --plain --columns key --no-headers); do
  jira issue edit $issue -s"To Do" --label stale
done
```

## Cross-Team Coordination

Working across teams:

```bash
# Find issues blocked by other teams
jira issue list -a$(jira me) -lblocked --plain --columns key,summary,status

# Check dependencies in a project
jira issue list -pOTHERPROJ -a"Dependency Owner"

# See what other teams need from you
jira issue list -r~$(jira me) -a$(jira me) --plain --columns key,reporter,summary

# Create handoff ticket
jira issue create -tTask -s"Handoff: Database migration" -CInfra -a"Infrastructure Lead"
```

## Personal Productivity

Personal task management:

```bash
# My daily dashboard
alias jira-today='jira issue list -a$(jira me) -s"In Progress"'

# What I should focus on
alias jira-priorities='jira issue list -a$(jira me) -yHigh -s~Done --order-by priority'

# What I reported that needs attention
alias jira-reported='jira issue list -r$(jira me) -s"To Do"'

# Quick add task
alias jira-task='jira issue create -tTask -a$(jira me)'

# My work this week
alias jira-week='jira issue list -a$(jira me) --updated week'
```

## Best Practices

### Efficient Filtering

```bash
# Combine multiple filters for precision
jira issue list -a$(jira me) -yHigh -s"In Progress" --created week -lurgent

# Use NOT operator (~) to exclude
jira issue list -s~Done -s~"In Progress"  # Not done and not in progress

# Time-based queries for recent activity
jira issue list --updated -2h  # Last 2 hours
jira issue list --created today  # Created today
```

### Bulk Operations

```bash
# Add multiple issues to sprint
jira sprint add SPRINT_ID $(jira issue list -s"Ready" --plain --columns key --no-headers | head -10 | tr '\n' ' ')

# Batch assign to team members
for issue in ISSUE-1 ISSUE-2 ISSUE-3; do
  jira issue assign $issue "Team Member"
done
```

### Keyboard Shortcuts in Interactive Mode

Master the interactive UI for speed:
- Use **j/k** instead of arrows for Vim-like navigation
- Press **v** to quickly view details without leaving the list
- Press **m** to transition without navigating to browser
- Use **c** and **CTRL+k** to quickly copy links/keys for sharing

### Output Formatting for Different Needs

```bash
# For spreadsheets
jira issue list --csv > issues.csv

# For scripts
jira issue list --plain --no-headers --columns key

# For reports
jira issue list --plain --columns key,status,assignee,summary

# For JSON processing
jira issue list --raw | jq '.issues[] | {key, summary}'
```
