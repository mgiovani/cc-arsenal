---
name: jira-todo
description: Generates a prioritized daily work plan from a user's assigned Jira
  tickets — scoring by priority, due date, blockers, and recent activity, then
  recommending what to work on next. Use when the user asks "what should I work
  on today", wants to plan their workday, prioritize assigned tickets, or triage
  their Jira backlog. Complements jira-daily (yesterday's standup recap) and
  jira-cli (general command reference) — use this one specifically for
  forward-looking prioritization, not status reporting.
metadata:
  author: mgiovani
  version: 1.0.1
disable-model-invocation: true
argument-hint: '[--project <KEY>] [--urgent-only] [--include-blocked] [--time-box <hours>]'
allowed-tools: Bash(jira *), Bash(git *), Bash(cat *), Read, Task, TodoWrite
context: fork
agent: general-purpose
---

# Jira Todo - Daily Work Prioritization

Analyzes assigned tickets and recommends what to work on next, based on actual Jira data. Complements the **jira-cli** skill (general command reference) and **jira-daily** (yesterday's standup recap) — this skill is for forward-looking prioritization.

## Anti-Hallucination Guidelines

Recommendations must be based on actual Jira data, not inference:
1. **Only reference real tickets** - every ticket ID must come from jira CLI output
2. **Verify statuses** - read status from the API response, never assume
3. **Check actual priorities** - use the priority field from Jira, never infer
4. **Real story points** - only show story points if they exist in the ticket
5. **No invented blockers** - only mention blockers explicitly marked in Jira

## Phase 1: Determine Project Key

Get the project key from (in order of priority):
1. **Command argument**: `--project ABC` or `-p ABC`
2. **Jira CLI config**: read from `~/.config/.jira/.config.yml`

```bash
PROJECT_KEY=$(cat ~/.config/.jira/.config.yml 2>/dev/null | grep -A1 "^project:" | grep "key:" | awk '{print $2}')
echo "Detected project: $PROJECT_KEY"
```

If no project key is found, ask the user to specify with `--project <KEY>`.

## Phase 2: Gather Current Workload

```bash
# Get all assigned tickets in active statuses
jira issue list --assignee $(jira me) --status "To Do" "In Progress" "Code Review" "In Review" --plain --columns key,summary,status,priority,updated

# Check for blockers and dependencies
jira issue list --assignee $(jira me) --jql "status IN ('To Do', 'In Progress') AND (labels = 'blocked' OR description ~ 'blocked')" --plain

# Get recently updated tickets needing attention
jira issue list --assignee $(jira me) --updated -2d --status "Code Review" "In Review" "Waiting for Feedback" --plain
```

## Phase 3: Apply Prioritization Algorithm

Apply this directly in the main agent — it's a short scoring pass over a daily ticket list, not worth fanning out to subagents. Only spawn parallel Explore subagents if the workload is unusually large (>30 active tickets).

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

Also check git context inline (current branch, recent commits) to see which tickets already have active work in progress, so the plan can favor continuing momentum over context-switching.

## Phase 4: Generate Output

Use TodoWrite to track the work items identified. For the detailed output template, see [references/output-formats.md](references/output-formats.md).

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
```

### `--urgent-only`
Show only critical/urgent tickets requiring immediate attention (Priority: Highest, production bugs, blocking issues).
```bash
jira-todo --urgent-only
```

### `--include-blocked`
Include tickets that are blocked (filtered out by default), with suggestions for unblocking.
```bash
jira-todo --include-blocked
```

### `--time-box <hours>`
Optimize recommendations for specific time availability.
```bash
jira-todo --time-box 3
```

## Integration Points

- **jira-daily**: previous day's work influences today's recommendations
- **jira-cli**: use for detailed command syntax and sprint/epic management patterns
- **git**: check current branch and recent commits for context on active work

## Usage Examples

```bash
jira-todo                        # auto-detects project from config
jira-todo --project ABC          # specify project explicitly
jira-todo --urgent-only          # only show urgent items
jira-todo --time-box 4           # plan for limited time
jira-todo --include-blocked      # include blocked tickets in analysis
```

## Important Notes

- **Requires jira-cli**: install from https://github.com/ankitpokhrel/jira-cli
- **Config location**: `~/.config/.jira/.config.yml`
- **Real data only**: all recommendations are based on actual Jira ticket data
