---
# Enhancement for: jira-daily
disable-model-invocation: true
argument-hint: "[--project <KEY>] [--since <date>] [--format <format>]"
allowed-tools: "Bash(jira *), Bash(git *), Bash(cat *), Bash(date *), Read, Task, TodoWrite"
context: "fork"
agent: "general-purpose"
---

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
