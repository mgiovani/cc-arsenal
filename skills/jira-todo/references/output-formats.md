# Jira Todo - Output Format Template

Reference template for the todo list output. Adapt sections based on actual Jira data returned.

## Default Output Format

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
