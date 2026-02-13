---
name: jira-todo
description: Generate smart daily work plans with intelligent prioritization from
  Jira tickets. This skill should be used when users want to plan their workday, prioritize
  assigned tickets, or determine what to work on next based on Jira data.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[--project <KEY>] [--urgent-only] [--time-box <hours>]'
allowed-tools: Bash(jira *), Bash(git *), Bash(cat *), Read, Task, TodoWrite
context: fork
agent: general-purpose
---

# Jira Todo

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Jira Todo - Daily Work Prioritization

Smart daily work planner that analyzes assigned tickets and provides actionable recommendations on what to work on next. This skill complements the **jira-cli** skill, which provides general Jira CLI knowledge and command reference.

## Anti-Hallucination Guidelines

**CRITICAL**: Recommendations must be based on ACTUAL Jira data:
1. **Only reference real tickets** - Every ticket ID must come from jira CLI output
2. **Verify statuses** - Never assume status; read it from the API response
3. **Check actual priorities** - Use the priority field from Jira, never infer
4. **Real story points** - Only show story points if they exist in the ticket
5. **No invented blockers** - Only mention blockers explicitly marked in Jira

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

### Phase 2: Gather Current Workload

```bash
# Get all assigned tickets in active statuses
jira issue list --assignee $(jira me) --status "To Do" "In Progress" "Code Review" "In Review" --plain --columns key,summary,status,priority,updated

# Check for blockers and dependencies
jira issue list --assignee $(jira me) --jql "status IN ('To Do', 'In Progress') AND (labels = 'blocked' OR description ~ 'blocked')" --plain

# Get recently updated tickets needing attention
jira issue list --assignee $(jira me) --updated -2d --status "Code Review" "In Review" "Waiting for Feedback" --plain
### Phase 3: Analyze with SubAgents (For Complex Workloads)

If more than 5 active tickets, use parallel analysis:

```
Agent 1 - Priority Analysis:
- prompt: "Analyze these Jira tickets and score by priority. Consider: Priority field weight, due dates, recent activity, blocking status. Return sorted list with scores."
- agent-type: "general-purpose"

Agent 2 - Dependency Analysis:
- prompt: "For these tickets, identify which ones are blocking others or being blocked. Map the dependency chain and impact."
- agent-type: "general-purpose"

Agent 3 - Context Analysis:
- prompt: "Check git branches and recent commits. Which tickets have active development? Which need context switch?"
- agent-type: "Explore"
### Phase 4: Apply Prioritization Algorithm

**Priority Scoring:**
- **Critical/Urgent Priority**: Weight x 10
- **Due Soon**: Days until due date (lower = higher score)
- **Recent Activity**: Updated in last 24h = +5 points
- **Blocking Others**: Has dependents = +3 points
- **Needs Response**: Recent comments = +2 points
- **Production Bug**: Bug type with High+ priority = +4 points

**Smart Recommendations:**
```python
if ticket.priority == "Highest" and ticket.type == "Bug":
 recommendation = "DROP EVERYTHING - Critical bug"
elif ticket.has_recent_comments and ticket.status == "Code Review":
 recommendation = "Address review feedback ASAP"
elif ticket.is_blocking_others:
 recommendation = "Unblock others - high team impact"
elif ticket.status == "In Progress" and days_since_update > 2:
 recommendation = "Continue momentum - you were making progress"
else:
 recommendation = "Good candidate for focused work time"
### Phase 5: Generate Output

Use TodoWrite to track the work items identified.

## Output Format

For the detailed output template, see [references/output-formats.md](references/output-formats.md).

**Report sections:**
- **Immediate Actions (Do First)**: Critical/urgent tickets requiring immediate attention
- **High Impact Work (Do Today)**: High-priority items that fit into today's schedule
- **This Week (Schedule Time)**: Medium-priority items to plan for the week
- **On Hold (Monitor)**: Tickets waiting on others or blocked
- **Work Summary**: Active ticket count, estimated hours, sprint progress
- **Smart Suggestions**: Time-blocking and energy management recommendations
- **Recommended Schedule**: Hour-by-hour daily plan

## Command Options

### `--project <KEY>` or `-p <KEY>`
Specify the Jira project key explicitly.
```bash
jira-todo --project ABC
jira-todo -p PROJ
### `--urgent-only`
Show only critical/urgent tickets requiring immediate attention.
```bash
jira-todo --urgent-only
# Only shows Priority: Highest, production bugs, blocking issues
### `--include-blocked`
Include tickets that are blocked (usually filtered out).
```bash
jira-todo --include-blocked
# Shows blocked tickets with suggestions for unblocking
### `--time-box <hours>`
Optimize recommendations for specific time availability.
```bash
jira-todo --time-box 3
# Recommends work that fits in ~3 hours
## Smart Features

### Context Awareness
- Detect if work is already in progress (recent commits, branch names)
- Suggest continuing vs. context switching based on cognitive load
- Consider typical work patterns (morning debugging vs. afternoon planning)

### Dependency Analysis
- Identify tickets blocking teammates
- Show impact chain (what gets unblocked when a ticket is finished)
- Highlight cross-team dependencies requiring coordination

### Energy Optimization
- Suggest complex debugging for high-energy periods
- Recommend routine tasks for low-energy times
- Balance creative work with maintenance tasks

### Progress Tracking
- Show sprint/milestone progress
- Identify tickets falling behind schedule
- Celebrate completed work momentum

## Integration Points

### With jira-daily Skill
- Previous day's work influences today's recommendations
- Completed items inform progress tracking

### With jira-cli Skill
- Use jira-cli for detailed command syntax and flag reference
- Refer to jira-cli workflows for sprint and epic management patterns

### With Development Tools
- Check current git branch for context
- Look for recent commits related to tickets
- Suggest based on recent file activity

## Usage Examples

```bash
# Basic usage (auto-detects project from config)
jira-todo

# Specify project explicitly
jira-todo --project ABC

# Only show urgent items
jira-todo --urgent-only

# Plan for limited time
jira-todo --time-box 4

# Include blocked tickets in analysis
jira-todo --include-blocked
## Important Notes

- **Requires jira-cli**: Install from https://github.com/ankitpokhrel/jira-cli
- **Config location**: `~/.config/.jira/.config.yml`
- **Project key**: Auto-detected from config or specify with `--project`
- **Real data only**: All recommendations based on actual Jira ticket data

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 2: Gather Current Workload

```bash
# Get all assigned tickets in active statuses
jira issue list --assignee $(jira me) --status "To Do" "In Progress" "Code Review" "In Review" --plain --columns key,summary,status,priority,updated

# Check for blockers and dependencies
jira issue list --assignee $(jira me) --jql "status IN ('To Do', 'In Progress') AND (labels = 'blocked' OR description ~ 'blocked')" --plain

# Get recently updated tickets needing attention
jira issue list --assignee $(jira me) --updated -2d --status "Code Review" "In Review" "Waiting for Feedback" --plain
```

### Phase 3: Analyze with SubAgents (For Complex Workloads)

If more than 5 active tickets, use parallel analysis:

```
Agent 1 - Priority Analysis:
- prompt: "Analyze these Jira tickets and score by priority. Consider: Priority field weight, due dates, recent activity, blocking status. Return sorted list with scores."
- subagent_type: "general-purpose"

Agent 2 - Dependency Analysis:
- prompt: "For these tickets, identify which ones are blocking others or being blocked. Map the dependency chain and impact."
- subagent_type: "general-purpose"

Agent 3 - Context Analysis:
- prompt: "Check git branches and recent commits. Which tickets have active development? Which need context switch?"
- subagent_type: "Explore"
```

### Phase 4: Apply Prioritization Algorithm

**Priority Scoring:**
- **Critical/Urgent Priority**: Weight x 10
- **Due Soon**: Days until due date (lower = higher score)
- **Recent Activity**: Updated in last 24h = +5 points
- **Blocking Others**: Has dependents = +3 points
- **Needs Response**: Recent comments = +2 points
- **Production Bug**: Bug type with High+ priority = +4 points

**Smart Recommendations:**
```python
if ticket.priority == "Highest" and ticket.type == "Bug":
    recommendation = "DROP EVERYTHING - Critical bug"
elif ticket.has_recent_comments and ticket.status == "Code Review":
    recommendation = "Address review feedback ASAP"
elif ticket.is_blocking_others:
    recommendation = "Unblock others - high team impact"
elif ticket.status == "In Progress" and days_since_update > 2:
    recommendation = "Continue momentum - you were making progress"
else:
    recommendation = "Good candidate for focused work time"
```

### Phase 5: Generate Output

Use TodoWrite to track the work items identified.
