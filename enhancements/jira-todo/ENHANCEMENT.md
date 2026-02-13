---
# Enhancement for: jira-todo
disable-model-invocation: true
argument-hint: "[--project <KEY>] [--urgent-only] [--time-box <hours>]"
allowed-tools: "Bash(jira *), Bash(git *), Bash(cat *), Read, Task, TodoWrite"
context: "fork"
agent: "general-purpose"
---

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
