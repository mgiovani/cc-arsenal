# GitHub Daily - Output Format Templates

Reference templates for all supported output formats. Select the appropriate format based on the audience and context.

Every section below is conditional: include it only when Phase 3/4 actually produced matching data. A repo with no blocked items has no Blockers section; a report where `--include-reviews` wasn't set has no Reviews Requested section. Never fabricate numbers or leave placeholder brackets in the final output.

## Default (Detailed) Format

The full standup report with all sections. Used when no `--format` flag is specified or with `--format detailed`.

```
## Daily Standup - {DATE}

### What I Completed Yesterday
**#1234** - Fix authentication timeout issue
├── State: Closed | Labels: bug, priority: high
├── **Impact**: Fixed critical API issue blocking QA pipeline
├── **Work**: Added session handling with proper timeout logic
└── **PR**: #1240 (merged)

**#1201** - Add input validation for user forms
├── State: Closed | Labels: enhancement
├── **Impact**: Enhanced security for user data submission
└── **Work**: Implemented server-side validation middleware

### Pull Requests Merged
**PR #1240** - Fix session timeout handling
├── **Linked**: Closes #1234
└── **Merged**: {YESTERDAY}

### What I'm Working On Today
**#1156** - Implement user dashboard widget
├── State: Open | Labels: feature, priority: high | Milestone: v2.1
├── **Next**: Complete API endpoints for metrics
├── **Estimate**: ~4 hours remaining
└── **Branch**: feature/dashboard-widget (12 commits)

**PR #1245** - Refactor data export service
├── State: Open | Reviews: Changes requested
├── **Next**: Address review feedback from @teammate
└── **Target**: Tomorrow morning

### Reviews Requested
**PR #1250** by @teammate - Add caching layer for API responses
├── Labels: performance
├── **Requested**: 2 hours ago
└── **Action**: Review during collaboration window

### Blockers & Help Needed
**#1302** - Database migration performance
├── **Blocked**: Label `blocked` - Waiting for infra team approval
├── **Duration**: 2 days blocked
├── **Need**: Infrastructure team input on scaling strategy
└── **Escalation**: Will follow up in #infrastructure channel

### Metrics Summary
- **Commits**: X (from `git rev-list --count`)
- **Issues Closed**: X | **PRs Merged**: Y
```

Omit the Metrics Summary line for any metric that Phase 3 didn't gather (e.g. no lines-changed or reviews-given command runs by default, leave those out rather than guessing).

## Brief Format (`--format brief`)

Concise version for quick standups. Each section is a single line.

```
## Daily Update - {DATE}

**Completed**: #1234 (bug fix), #1201 (validation) | PR #1240 merged
**In Progress**: #1156 (dashboard - 4h remaining), PR #1245 (review feedback)
**Reviews Pending**: PR #1250 from @teammate (caching)  [only with `--include-reviews`]
**Blocked**: #1302 (waiting on infra - 2 days)
```

## Slack Format (`--format slack`)

Formatted for Slack/Teams posting with appropriate markdown.

```
*Daily Standup - {DATE}*

*Completed*
• #1234: Fixed authentication timeout issue
• #1201: Added input validation for forms
• PR #1240: Merged (session timeout fix)

*Working On*
• #1156: Dashboard widget implementation (~4h left)
• PR #1245: Addressing review feedback

*Reviews Requested*
• PR #1250 by @teammate: API caching layer

*Blockers*
• #1302: Waiting 2 days for infra team approval
```

`*Reviews Requested*` only appears with `--include-reviews` (detailed format includes it by default).
