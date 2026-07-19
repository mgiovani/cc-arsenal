# Jira Daily - Output Format Templates

Reference templates for all supported output formats. Select the appropriate
format based on the audience and context.

Every section below is conditional: include it only when Phase 3/4 actually
produced matching data. A report with nothing blocked has no Blockers section; a
ticket with no commits matched to it has no Commits line. Never fabricate a
number (story points, lines changed, test coverage, PR counts) or leave a
placeholder bracket in the final output — jira-daily has no source for those
fields, so they don't appear in any template below.

## Default (Detailed) Format

The full standup report with all sections. Used when no `--format` flag is
specified or with `--format detailed`.

```
## Daily Standup - {DATE}

### What I Completed Yesterday
**ABC-1234** - Fix authentication timeout issue
├── Status: Done | Priority: Highest | Type: Bug
├── **Impact**: Fixed critical API issue blocking QA pipeline
└── **Commits**: 3 (matched via ABC-1234 in commit messages)

**ABC-1201** - Add input validation for user forms
├── Status: Done | Priority: Medium | Type: Task
└── **Impact**: Enhanced security for user data submission

### What I'm Working On Today
**ABC-1156** - Implement user dashboard widget
├── Status: In Progress | Priority: High | Type: Story
└── **Commits**: 2 (matched via ABC-1156 in commit messages)

**ABC-1089** - Refactor data export service
├── Status: Code Review | Priority: Medium | Type: Task
└── **Due**: 2025-01-22 (from ticket due date)

### Blockers & Help Needed
**ABC-1302** - Database migration performance
├── **Blocked**: Waiting for DBA approval on index changes
├── **Duration**: 2 days blocked
└── **Need**: Infrastructure team input on scaling strategy

### Ticket Summary
- **Completed**: X (Y bugs, Z stories/tasks — from the completed-tickets Type column)
- **In Progress**: X | **Blocked**: X
- **Commits**: X (from `git rev-list --count`)
```

Include a `**Commits**` line under a ticket only when at least one commit
matched its ID; include `**Due**` only when the ticket's `duedate` field is set.
Neither is a guess — both come straight out of Phase 3 output.

## Brief Format (`--format brief`)

Concise version for quick standups. Each section is a single line.

```
## Daily Update - {DATE}

**Completed**: ABC-1234 (bug fix, 3 commits), ABC-1201 (validation)
**In Progress**: ABC-1156 (dashboard, 2 commits)
**Blocked**: ABC-1302 (waiting on DBA - 2 days)
**Ticket Summary**: 2 completed, 1 in progress, 1 blocked
```

## Slack Format (`--format slack`)

Formatted for Slack/Teams posting with appropriate markdown.

```
*Daily Standup - {DATE}*

*Completed*
• ABC-1234: Fixed authentication timeout issue (3 commits)
• ABC-1201: Added input validation for forms

*Working On*
• ABC-1156: Dashboard widget implementation (2 commits)
• ABC-1089: Addressing PR review feedback, due 2025-01-22

*Blockers*
• ABC-1302: Waiting 2 days for DBA approval

*Ticket Summary*: 2 completed, 1 in progress, 1 blocked
```

## Manager Format (`--format manager`)

Executive summary focusing on delivery and risks — no team-collaboration or
peer-review metrics, since jira-daily gathers neither.

```
## Team Update - {DATE}

**Delivery Highlights**
- Resolved critical production issue (ABC-1234) affecting API stability
- Completed security enhancement (ABC-1201)

**Current Focus**
- Dashboard development (ABC-1156) - 2 commits so far
- Data export refactor (ABC-1089) - due 2025-01-22

**Risks & Dependencies**
- Infrastructure dependency (ABC-1302) blocked for 2 days - escalating today
```
