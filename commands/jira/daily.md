---
description: "Smart standup report generator with activity analysis"
argument-hint: "[--project <KEY>] [--since <date>] [--format <format>]"
allowed-tools: ["Bash(jira *)", "Bash(git *)", "Bash(cat *)", "Bash(date *)", "Read", "Task", "TodoWrite"]
---

# Jira Daily - Standup Meeting Preparation

Smart standup report generator that analyzes your work activity and provides structured updates for daily meetings.

## Anti-Hallucination Guidelines

**CRITICAL**: Standup reports must reflect ACTUAL work done:
1. **Only list real tickets** - Every ticket must come from jira CLI output
2. **Verify completion** - Only mark as "Completed" if status is Done/Closed/Released
3. **Real commit counts** - Use actual git log output, don't estimate
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
```

If no project key found, ask user to specify with `--project <KEY>`.

## Your Task

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

## Output Format

### Default (Detailed) Format

```
## Daily Standup - {DATE}

### What I Completed Yesterday
**ABC-1234** - Fix authentication timeout issue
├── Status: Done | Priority: Highest | Type: Bug
├── **Impact**: Fixed critical API issue blocking QA pipeline
├── **Work**: Added session handling with proper timeout logic
└── **PR**: #1234 (merged)

**ABC-1201** - Add input validation for user forms
├── Status: Done | Priority: Medium | Type: Task
├── **Impact**: Enhanced security for user data submission
└── **Work**: Implemented server-side validation middleware

### What I'm Working On Today
**ABC-1156** - Implement user dashboard widget
├── Status: In Progress | Priority: High | Type: Story
├── **Next**: Complete API endpoints for metrics
├── **Estimate**: ~4 hours remaining
└── **Target**: End of day

**ABC-1089** - Refactor data export service
├── Status: Code Review | Priority: Medium | Type: Task
├── **Next**: Address review feedback from @teammate
├── **PR**: #1235 (pending review)
└── **Target**: Tomorrow morning

### Blockers & Help Needed
**ABC-1302** - Database migration performance
├── **Blocked**: Waiting for DBA approval on index changes
├── **Duration**: 2 days blocked
├── **Need**: Infrastructure team input on scaling strategy
└── **Escalation**: Will follow up in #infrastructure channel

### Sprint Progress Update
- **Story Points Completed**: X/Y (Z% of sprint goal)
- **Tickets Closed**: X this week (Y bugs, Z features)
- **On Track**: Yes/No
- **Risk Items**: [List any risks]

### Technical Highlights
- **Code Quality**: [Notable improvements]
- **Performance**: [Optimizations made]
- **Testing**: [Test coverage changes]

### Team Collaboration
- **Code Reviews**: Reviewed X PRs
- **Knowledge Sharing**: [Documentation, mentoring]
- **Planning**: [Design discussions, refinements]

### Metrics Summary
- **Commits**: X commits across Y files
- **Lines Changed**: +X / -Y
- **Test Coverage**: X% (+/-Y% from yesterday)

### Today's Focus Areas
1. **9:00-12:00**: [Primary focus]
2. **1:00-3:00**: [Secondary tasks]
3. **3:00-5:00**: [Reviews, collaboration]
```

### Brief Format (`--format brief`)

```
## Daily Update - {DATE}

**Completed**: ABC-1234 (bug fix), ABC-1201 (validation)
**In Progress**: ABC-1156 (dashboard - 4h remaining)
**Blocked**: ABC-1302 (waiting on DBA - 2 days)
**Today's Focus**: Complete ABC-1156 APIs, review 3 PRs
**Sprint**: X/Y points done (Z%) - on track
```

### Slack Format (`--format slack`)

```
*Daily Standup - {DATE}*

*Completed*
• ABC-1234: Fixed authentication timeout issue
• ABC-1201: Added input validation for forms

*Working On*
• ABC-1156: Dashboard widget implementation (~4h left)
• ABC-1089: Addressing PR review feedback

*Blockers*
• ABC-1302: Waiting 2 days for DBA approval

*Sprint*: X/Y points (Z%) - on track
```

### Manager Format (`--format manager`)

```
## Team Update - {DATE}

**Delivery Highlights**
- Resolved critical production issue (ABC-1234) affecting API stability
- Completed security enhancement (ABC-1201) ahead of schedule
- Sprint progress: Z% complete - on track

**Current Focus**
- Dashboard development (ABC-1156) - on schedule for Friday delivery
- Code review feedback resolution (ABC-1089) - completing today

**Risks & Dependencies**
- Infrastructure dependency (ABC-1302) blocked for 2 days - escalating today

**Team Contributions**
- Reviewed X peer PRs
- Documented best practices for team knowledge sharing
```

## Command Options

### `--project <KEY>` or `-p <KEY>`
Specify the Jira project key explicitly
```bash
/jira:daily --project ABC
```

### `--since <date>`
Override the automatic date calculation
```bash
/jira:daily --since 2025-01-20
# Shows activity since specific date
```

### `--format <format>`
Choose output format for different audiences
```bash
/jira:daily --format brief      # Concise version for quick standups
/jira:daily --format detailed   # Full version with technical details (default)
/jira:daily --format slack      # Formatted for Slack/Teams posting
/jira:daily --format manager    # Executive summary format
```

### `--include-planned`
Include tickets planned for today (not just completed/in-progress)
```bash
/jira:daily --include-planned
# Shows "Today's Plan" section with prioritized work
```

## Smart Features

### Context Awareness
- Detects Monday condition and reports from last Friday
- Identifies sprint boundaries and adjusts progress tracking
- Recognizes critical/blocking tickets and highlights urgency
- Correlates git commits with Jira ticket references

### Progress Intelligence
- Calculates sprint velocity and burndown trends
- Compares current productivity to historical averages
- Identifies patterns in blocking issues
- Tracks code review participation and response times

### Goal Alignment
- Maps completed work to sprint objectives
- Highlights work that unblocks teammates
- Identifies contributions to team goals
- Suggests proactive communications

## Integration Points

### With /jira:todo
- References yesterday's planned work vs. actual completion
- Updates priority recommendations based on standup outcomes

### With Development Tools
- Parses commit messages for automatic work categorization
- Links git branches to Jira tickets for complete picture
- Integrates with PR status for review workflow visibility

## Usage Examples

```bash
# Basic usage (auto-detects project, yesterday's activity)
/jira:daily

# Specify project explicitly
/jira:daily --project ABC

# Quick standup format
/jira:daily --format brief

# For Slack posting
/jira:daily --format slack

# For manager 1:1
/jira:daily --format manager

# Custom date range
/jira:daily --since 2025-01-15

# Weekly summary for manager
/jira:daily --since $(date -v-7d +%Y-%m-%d) --format manager
```

## Daily Routine Integration

### Morning Preparation (5 minutes)
```bash
# Quick morning routine
/jira:daily --format brief
# Review and adjust for accuracy
# Copy to standup notes
```

### Standup Meeting (2 minutes per person)
- Read directly from generated report
- Add context or clarifications as needed
- Note any team dependencies or offers to help

### Manager 1:1s (weekly)
```bash
# Weekly summary for manager meetings
/jira:daily --since $(date -v-7d +%Y-%m-%d) --format manager
```

## Quality Checklist

The command ensures your standup covers:
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

---

**Dependencies**: jira-cli, git
**Config**: `~/.config/.jira/.config.yml`
