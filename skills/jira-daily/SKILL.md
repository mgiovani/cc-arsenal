---
name: jira-daily
description: Generate smart standup reports from Jira activity and git history. This
  skill should be used when users want to prepare for daily standups, generate activity
  reports, or summarize recent work across Jira tickets and git commits.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[--project <KEY>] [--since <date>] [--format <format>]'
allowed-tools: Bash(jira *), Bash(git *), Bash(cat *), Bash(date *), Read, Task, TodoWrite
context: fork
agent: general-purpose
---

# Jira Daily

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Jira Daily - Standup Meeting Preparation

Smart standup report generator that analyzes work activity and provides structured updates for daily meetings. This skill complements the **jira-cli** skill, which provides general Jira CLI knowledge and command reference.

## Anti-Hallucination Guidelines

**CRITICAL**: Standup reports must reflect ACTUAL work done:
1. **Only list real tickets** - Every ticket must come from jira CLI output
2. **Verify completion** - Only mark as "Completed" if status is Done/Closed/Released
3. **Real commit counts** - Use actual git log output, never estimate
4. **Actual blockers** - Only mention blockers explicitly in Jira or discussed
5. **True metrics** - Story points and progress from actual sprint data

## Project Key Detection

### Phase 1: Determine Project Key

Get the project key from (in order of priority):
1. **Command argument**: `--project ABC` or `-p ABC`
2. **Jira CLI config**: Read from `~/.config/.jira/.config.yml`

```bash
# Try to get project key from jira CLI config
PROJECT_KEY=$(cat ~/.config/.jira/.config.yml 2>/dev/null | grep -A1 "^project:" | grep "key:" | awk '{print $2}')
echo "Detected project: $PROJECT_KEY"
If no project key found, ask the user to specify with `--project <KEY>`.

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
# Get tickets updated recently
jira issue list --updated -1d --plain --columns key,summary,status,priority,type

# Get tickets moved to done/completed
jira issue list --jql "status changed to (Done, Released, Closed) after -1d AND assignee was currentUser" --plain

# Get tickets currently in progress
jira issue list --assignee $(jira me) --status "In Progress" "Code Review" "In Review" --plain

# Check for blockers
jira issue list --assignee $(jira me) --jql "labels = 'blocked' OR description ~ 'blocked'" --plain

# Get git activity
git log --author="$(git config user.email)" --since="$SINCE_DATE" --oneline --all --no-merges

# Count commits and files
git rev-list --count --since="$SINCE_DATE" --author="$(git config user.email)" --all 2>/dev/null || echo "0"
### Phase 4: Analyze with SubAgents (For Comprehensive Reports)

For detailed format, use parallel analysis:

```
Agent 1 - Work Classification:
- prompt: "Classify these Jira tickets into: Completed, In Progress, Blocked, Started. Base ONLY on actual status field. Return categorized list."
- agent-type: "general-purpose"

Agent 2 - Impact Analysis:
- prompt: "For completed tickets, summarize the business/technical impact based on ticket description and type. Keep it factual."
- agent-type: "general-purpose"

Agent 3 - Git Correlation:
- prompt: "Match git commits to Jira tickets by ticket ID in commit messages. Report which tickets have code changes."
- agent-type: "Explore"
### Phase 5: Generate Report

Track sections completed with TodoWrite.

## Output Formats

For detailed output format templates (default, brief, slack, manager), see [references/output-formats.md](references/output-formats.md).

**Available formats:**
- **Default (Detailed)**: Full report with completed work, in-progress items, blockers, sprint progress, technical highlights, metrics, and schedule
- **Brief** (`--format brief`): Concise one-line-per-section format for quick standups
- **Slack** (`--format slack`): Formatted for Slack/Teams posting with markdown
- **Manager** (`--format manager`): Executive summary focusing on delivery highlights and risks

## Command Options

### `--project <KEY>` or `-p <KEY>`
Specify the Jira project key explicitly.

### `--since <date>`
Override the automatic date calculation.
```bash
jira-daily --since 2025-01-20
### `--format <format>`
Choose output format for different audiences.
```bash
jira-daily --format brief # Concise version for quick standups
jira-daily --format detailed # Full version with technical details (default)
jira-daily --format slack # Formatted for Slack/Teams posting
jira-daily --format manager # Executive summary format
### `--include-planned`
Include tickets planned for today (not just completed/in-progress).

## Smart Features

### Context Awareness
- Detect Monday condition and report from last Friday
- Identify sprint boundaries and adjust progress tracking
- Recognize critical/blocking tickets and highlight urgency
- Correlate git commits with Jira ticket references

### Progress Intelligence
- Calculate sprint velocity and burndown trends
- Compare current productivity to historical averages
- Identify patterns in blocking issues
- Track code review participation and response times

### Goal Alignment
- Map completed work to sprint objectives
- Highlight work that unblocks teammates
- Identify contributions to team goals
- Suggest proactive communications

## Integration Points

### With jira-todo Skill
- Reference yesterday's planned work vs. actual completion
- Update priority recommendations based on standup outcomes

### With jira-cli Skill
- Use jira-cli for detailed command syntax and flag reference
- Refer to jira-cli workflows for sprint and epic management patterns

### With Development Tools
- Parse commit messages for automatic work categorization
- Link git branches to Jira tickets for complete picture
- Integrate with PR status for review workflow visibility

## Usage Examples

```bash
# Basic usage (auto-detects project, yesterday's activity)
jira-daily

# Specify project explicitly
jira-daily --project ABC

# Quick standup format
jira-daily --format brief

# For Slack posting
jira-daily --format slack

# For manager 1:1
jira-daily --format manager

# Custom date range
jira-daily --since 2025-01-15

# Weekly summary for manager
jira-daily --since $(date -v-7d +%Y-%m-%d) --format manager
## Daily Routine Integration

### Morning Preparation (5 minutes)
```bash
jira-daily --format brief
# Review and adjust for accuracy
# Copy to standup notes
### Standup Meeting (2 minutes per person)
- Read directly from generated report
- Add context or clarifications as needed
- Note any team dependencies or offers to help

### Manager 1:1s (weekly)
```bash
jira-daily --since $(date -v-7d +%Y-%m-%d) --format manager
## Quality Checklist

The report ensures the standup covers:
- [ ] Concrete accomplishments with business impact
- [ ] Clear current work with time estimates
- [ ] Specific blockers with escalation plans
- [ ] Team collaboration and knowledge sharing
- [ ] Sprint/goal alignment and risk identification
- [ ] Proactive communication about dependencies

## Important Notes

- **Requires jira-cli**: Install from https://github.com/ankitpokhrel/jira-cli
- **Config location**: `~/.config/.jira/.config.yml`
- **Project key**: Auto-detected from config or specify with `--project`
- **Git integration**: Uses local git repository for commit analysis
- **Real data only**: All metrics based on actual Jira and git data

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

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
```

### Phase 3: Gather Activity Data

```bash
# Get tickets updated recently
jira issue list --updated -1d --plain --columns key,summary,status,priority,type

# Get tickets moved to done/completed
jira issue list --jql "status changed to (Done, Released, Closed) after -1d AND assignee was currentUser()" --plain

# Get tickets currently in progress
jira issue list --assignee $(jira me) --status "In Progress" "Code Review" "In Review" --plain

# Check for blockers
jira issue list --assignee $(jira me) --jql "labels = 'blocked' OR description ~ 'blocked'" --plain

# Get git activity
git log --author="$(git config user.email)" --since="$SINCE_DATE" --oneline --all --no-merges

# Count commits and files
git rev-list --count --since="$SINCE_DATE" --author="$(git config user.email)" --all 2>/dev/null || echo "0"
```

### Phase 4: Analyze with SubAgents (For Comprehensive Reports)

For detailed format, use parallel analysis:

```
Agent 1 - Work Classification:
- prompt: "Classify these Jira tickets into: Completed, In Progress, Blocked, Started. Base ONLY on actual status field. Return categorized list."
- subagent_type: "general-purpose"

Agent 2 - Impact Analysis:
- prompt: "For completed tickets, summarize the business/technical impact based on ticket description and type. Keep it factual."
- subagent_type: "general-purpose"

Agent 3 - Git Correlation:
- prompt: "Match git commits to Jira tickets by ticket ID in commit messages. Report which tickets have code changes."
- subagent_type: "Explore"
```

### Phase 5: Generate Report

Track sections completed with TodoWrite.
