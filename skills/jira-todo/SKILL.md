---
name: jira-todo
description: Generates a prioritized daily work plan from a user's assigned Jira
  tickets, scoring by priority, due date, blockers, and recent activity, then
  recommending what to work on next. Use when the user asks "what should I work
  on today", wants to plan their workday, prioritize assigned tickets, or triage
  their Jira backlog. Not for yesterday's standup recap (use jira-daily) or raw
  command reference (use jira-cli), this skill is specifically for
  forward-looking prioritization, not status reporting.
metadata:
  author: mgiovani
  version: 1.2.0
disable-model-invocation: true
argument-hint: '[--project <KEY>] [--urgent-only] [--include-blocked] [--time-box <hours>]'
allowed-tools: Bash(jira *), Bash(git *), Read, Task, TodoWrite
---

# Jira todo - daily work prioritization

Analyzes assigned tickets and recommends what to work on next, based on actual Jira data. Complements the **jira-cli** skill (general command reference) and **jira-daily** (yesterday's standup recap): this skill is for forward-looking prioritization.

## Phase 1: verify Jira CLI works

Before anything else, confirm the CLI is installed and authenticated:

```bash
jira me
```

If that fails (command not found, not authenticated, any error), STOP here. Do not proceed to Phase 2 or any later phase, and do not simulate, infer, or fabricate ticket data to produce a plan anyway. Tell the user:

> The `jira` CLI isn't available or isn't authenticated in this environment. Install and configure it from https://github.com/ankitpokhrel/jira-cli, then re-run this skill.

This gate exists because an agent that can't reach real Jira data will otherwise write a plausible-looking report from imagined tickets and present it as a real daily plan. Every ticket ID, priority, status, and story point anywhere in this skill's output must come from a `jira` command actually run this session. Never use a hardcoded fixture, a "simulated" placeholder, or a helper script that was written but not executed, and never mention a blocker that wasn't explicitly marked (label or blocking-link field) in that output. If a command returns no results, say so plainly rather than inventing tickets to fill out the report sections.

## Phase 2: determine project key

Get the project key from (in order of priority):
1. **Command argument**: `--project ABC` or `-p ABC`
2. **Jira CLI config**: Read `~/.config/.jira/.config.yml` and extract the `project.key` value.

If no project key is found, ask the user to specify with `--project <KEY>`.

## Phase 3: gather current workload

Run these directly via Bash before recommending anything: every ticket in the output must trace back to one of these commands' actual stdout, not to a script that reproduces expected output without executing them:

```bash
# Get all assigned tickets in active statuses
jira issue list --assignee $(jira me) --status "To Do" "In Progress" "Code Review" "In Review" --plain --columns key,summary,status,priority,updated

# Check for blockers and dependencies
jira issue list --assignee $(jira me) --jql "status IN ('To Do', 'In Progress') AND (labels = 'blocked' OR description ~ 'blocked')" --plain

# Get recently updated tickets needing attention
jira issue list --assignee $(jira me) --updated -2d --status "Code Review" "In Review" "Waiting for Feedback" --plain
```

If `--include-blocked` is not set, drop blocked tickets from the main sections (still surface them under On Hold).

## Phase 4: apply prioritization algorithm

Apply this directly in the main agent: it's a short scoring pass over a daily ticket list, not worth fanning out to subagents. Only spawn parallel Explore subagents if the workload is unusually large (>30 active tickets), and only where a `Task`/subagent tool is available; otherwise do the same scoring pass sequentially inline regardless of ticket count.

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

If `--urgent-only` is set, skip straight to just the Immediate Actions section (Priority: Highest, production bugs, blocking issues) and drop the rest of Phase 5's sections.

If `--time-box <hours>` is set, cap the Recommended Schedule at that many hours and drop lower-priority items that wouldn't fit rather than padding the schedule to fill it.

## Phase 5: generate output

Track the identified items in a todo list (use TodoWrite if available; otherwise just list them in the report). For the detailed output template, see [references/output-formats.md](references/output-formats.md).

**Report sections:**
- **Immediate Actions (Do First)**: Critical/urgent tickets requiring immediate attention
- **High Impact Work (Do Today)**: High-priority items that fit into today's schedule
- **This Week (Schedule Time)**: Medium-priority items to plan for the week
- **On Hold (Monitor)**: Tickets waiting on others or blocked
- **Work Summary**: Active ticket count, estimated hours, sprint progress
- **Smart Suggestions**: Time-blocking and energy management recommendations
- **Recommended Schedule**: Hour-by-hour daily plan

## Command options

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

## Integration points

- **jira-daily**: previous day's work influences today's recommendations
- **jira-cli**: use for detailed command syntax and sprint/epic management patterns
- **git**: check current branch and recent commits for context on active work

## Usage examples

```bash
jira-todo                        # auto-detects project from config
jira-todo --project ABC          # specify project explicitly
jira-todo --urgent-only          # only show urgent items
jira-todo --time-box 4           # plan for limited time
jira-todo --include-blocked      # include blocked tickets in analysis
```

## Important notes

- **Requires jira-cli**: install from https://github.com/ankitpokhrel/jira-cli
- **Config location**: `~/.config/.jira/.config.yml`
- **Real data only**: all recommendations are based on actual Jira ticket data
