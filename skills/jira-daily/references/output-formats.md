# Jira Daily - Output Format Templates

Reference templates for all supported output formats. Select the appropriate format based on the audience and context.

## Default (Detailed) Format

The full standup report with all sections. Used when no `--format` flag is specified or with `--format detailed`.

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

## Brief Format (`--format brief`)

Concise version for quick standups. Each section is a single line.

```
## Daily Update - {DATE}

**Completed**: ABC-1234 (bug fix), ABC-1201 (validation)
**In Progress**: ABC-1156 (dashboard - 4h remaining)
**Blocked**: ABC-1302 (waiting on DBA - 2 days)
**Today's Focus**: Complete ABC-1156 APIs, review 3 PRs
**Sprint**: X/Y points done (Z%) - on track
```

## Slack Format (`--format slack`)

Formatted for Slack/Teams posting with appropriate markdown.

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

## Manager Format (`--format manager`)

Executive summary focusing on delivery, risks, and team contributions.

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
