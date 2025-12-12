---
description: "Smart daily work planner with intelligent prioritization"
argument-hint: "[--project <KEY>] [--urgent-only] [--time-box <hours>]"
allowed-tools: ["Bash(jira *)", "Bash(git *)", "Bash(cat *)", "Read", "Task", "TodoWrite"]
---

# Jira Todo - Daily Work Prioritization

Smart daily work planner that analyzes your assigned tickets and provides actionable recommendations on what to work on next.

## Anti-Hallucination Guidelines

**CRITICAL**: Recommendations must be based on ACTUAL Jira data:
1. **Only reference real tickets** - Every ticket ID must come from jira CLI output
2. **Verify statuses** - Don't assume status, read it from the API response
3. **Check actual priorities** - Use the priority field from Jira, don't infer
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
```

If no project key found, ask user to specify with `--project <KEY>`.

## Your Task

### Phase 2: Gather Current Workload

```bash
# Get all your assigned tickets in active statuses
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
- **Critical/Urgent Priority**: Weight × 10
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

## Output Format

```
## Your Todo List - {DATE}

### Immediate Actions (Do First)
**ABC-1234** - Fix authentication timeout issue
├── Priority: Highest | Type: Bug | Status: In Progress
├── **Recommendation**: Continue this - you were debugging yesterday
├── **Effort**: ~2 hours | **Context**: Familiar codebase
├── **Impact**: Blocking QA testing
└── **Next Step**: Complete the session handling fix you started

### High Impact Work (Do Today)
**ABC-1156** - Implement user dashboard widget
├── Priority: High | Type: Story | Status: To Do
├── **Recommendation**: Start after ABC-1234 - clear requirements
├── **Effort**: ~1 day | **Context**: New feature area
├── **Impact**: Sprint goal dependency
└── **Next Step**: Review designs and create technical plan

### This Week (Schedule Time)
**ABC-1089** - Refactor data export service
├── Priority: Medium | Type: Task | Status: To Do
├── **Recommendation**: Good for Friday afternoon - refactoring work
├── **Effort**: ~4 hours | **Context**: Technical debt
└── **Next Step**: Analyze current implementation patterns

### On Hold (Monitor)
**ABC-1201** - Database schema optimization
├── Status: Waiting for Feedback | Updated: 3 days ago
├── **Issue**: Waiting for DBA review
└── **Action**: Follow up if no response by tomorrow

### Work Summary
- **Total Active**: X tickets
- **Estimated Today**: ~X hours of focused work
- **Sprint Progress**: X/Y story points completed
- **Blocking Others**: X ticket(s)
- **Waiting on Others**: X ticket(s)

### Smart Suggestions
1. **Block Focus Time**: 9-11 AM for deep work on ABC-1234
2. **Collaboration Window**: 2-4 PM for ABC-1156 (may need clarification)
3. **Energy Management**: Save refactoring for low-energy periods

### Recommended Schedule
**9:00-11:00** | ABC-1234 (Debug authentication issue)
**11:00-12:00** | ABC-1234 (Testing & documentation)
**1:00-4:00** | ABC-1156 (Start dashboard widget)
**4:00-5:00** | Address any code review feedback
```

## Command Options

### `--project <KEY>` or `-p <KEY>`
Specify the Jira project key explicitly
```bash
/jira:todo --project ABC
/jira:todo -p PROJ
```

### `--urgent-only`
Show only critical/urgent tickets requiring immediate attention
```bash
/jira:todo --urgent-only
# Only shows Priority: Highest, production bugs, blocking issues
```

### `--include-blocked`
Include tickets that are blocked (usually filtered out)
```bash
/jira:todo --include-blocked
# Shows blocked tickets with suggestions for unblocking
```

### `--time-box <hours>`
Optimize recommendations for specific time availability
```bash
/jira:todo --time-box 3
# Recommends work that fits in ~3 hours
```

## Smart Features

### Context Awareness
- Detects if you're in the middle of work (recent commits, branch names)
- Suggests continuing vs. context switching based on cognitive load
- Considers typical work patterns (morning debugging vs. afternoon planning)

### Dependency Analysis
- Identifies tickets blocking teammates
- Shows impact chain (what gets unblocked when you finish)
- Highlights cross-team dependencies requiring coordination

### Energy Optimization
- Suggests complex debugging for high-energy periods
- Recommends routine tasks for low-energy times
- Balances creative work with maintenance tasks

### Progress Tracking
- Shows sprint/milestone progress
- Identifies tickets falling behind schedule
- Celebrates completed work momentum

## Integration Points

### With /jira:daily
- Previous day's work influences today's recommendations
- Completed items inform progress tracking

### With Development Tools
- Checks current git branch for context
- Looks for recent commits related to tickets
- Suggests based on recent file activity

## Usage Examples

```bash
# Basic usage (auto-detects project from config)
/jira:todo

# Specify project explicitly
/jira:todo --project ABC

# Only show urgent items
/jira:todo --urgent-only

# Plan for limited time
/jira:todo --time-box 4

# Include blocked tickets in analysis
/jira:todo --include-blocked
```

## Important Notes

- **Requires jira-cli**: Install from https://github.com/ankitpokhrel/jira-cli
- **Config location**: `~/.config/.jira/.config.yml`
- **Project key**: Auto-detected from config or specify with `--project`
- **Real data only**: All recommendations based on actual Jira ticket data

---

**Dependencies**: jira-cli, git
**Config**: `~/.config/.jira/.config.yml`
