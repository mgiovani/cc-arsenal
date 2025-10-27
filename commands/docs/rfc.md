---
description: "Create numbered RFC for proposing and discussing changes"
argument-hint: "<title> [variant]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash(git *)"]
---

# Create Request For Comments

Create a new RFC (Request For Comments) document for proposing and discussing changes.

## Your Task

1. **Parse Arguments**:
   - Extract proposal title from `$ARGUMENTS`
   - Check for variant keyword: `minimal`, `standard`, or `detailed`
   - If variant found, remove it from title
   - Default variant: `standard`

2. **Determine RFC Number**:
   - Scan `docs/rfc/` directory
   - Find highest existing RFC number (format: `RFC-XXXX-*`)
   - Increment by 1
   - If no RFCs exist, start with `0001`
   - Format as 4-digit padded number (e.g., `0001`, `0023`)

3. **Sanitize Title for Filename**:
   - Convert title to kebab-case
   - Remove special characters
   - Lowercase all letters
   - Example: "Add GraphQL API Support" → `add-graphql-api-support`

4. **Gather Context**:
   - Analyze codebase to understand current state
   - Identify relevant files and patterns
   - Find similar implementations or related features
   - Understand technical constraints

5. **Get Author Information**:
   ```bash
   # Try to get git author
   !`git config user.name 2>/dev/null || echo "Development Team"`
   ```

6. **Load Template**:
   - Template location: `commands/docs/templates/rfc/`
   - Select based on variant:
     - `minimal` → `minimal.md`
     - `standard` → `standard.md` (default)
     - `detailed` → `detailed.md`

7. **Populate Template**:
   Replace placeholders:
   - `{{RFC_NUMBER}}` - 4-digit number
   - `{{RFC_TITLE}}` - Original title (Title Case)
   - `{{DATE}}` - Current date (YYYY-MM-DD)
   - `{{AUTHOR}}` - Git user name or "Development Team"
   - `{{CONTEXT}}` - Gathered context from codebase
   - `{{PROJECT_NAME}}` - Git repo or directory name

8. **Create RFC File**:
   - Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
   - Ensure `docs/rfc/` directory exists
   - Write populated content
   - Set initial status to "Draft"

9. **Report Creation**:
   - Show RFC number and title
   - Display file path
   - Provide workflow guidance

## Template Variants

### Minimal Template
Quick proposal format for small changes.

**Sections:**
- Summary
- Motivation
- Proposal
- Open Questions

**Use when:** Small features, minor changes

### Standard Template (Default)
Balanced RFC for most changes.

**Sections:**
- Summary
- Motivation
- Proposal
- Rationale and Alternatives
- Implementation Plan
- Testing Plan
- Migration Strategy
- Open Questions
- Timeline

**Use when:** Most feature proposals

### Detailed Template
Comprehensive RFC for major changes.

**Sections:**
- Summary
- Background and Motivation
- Goals and Non-Goals
- Proposal
- Detailed Design
- Rationale and Alternatives
- Implementation Plan
- Testing and Quality Assurance
- Migration and Rollout Strategy
- Monitoring and Metrics
- Security Considerations
- Performance Implications
- Open Questions and Risks
- Timeline and Milestones
- Appendices

**Use when:** Major features, architectural changes

## Usage

Basic RFC creation (uses Standard template):
```
/docs:rfc "Add GraphQL API Support"
/docs:rfc "Implement Rate Limiting"
/docs:rfc "Add Multi-Tenancy Support"
```

With template variant override:
```
/docs:rfc minimal "Update Logging Format"
/docs:rfc detailed "Migration to Microservices Architecture"
/docs:rfc detailed "Adopt Event Sourcing Pattern"
```

## RFC Status Lifecycle

Update status in the RFC as it progresses:

1. **Draft** - Initial proposal, gathering feedback
2. **In Review** - Under discussion, modifications being made
3. **Accepted** - Approved for implementation
4. **Implemented** - Changes have been deployed
5. **Rejected** - Not moving forward with proposal
6. **Withdrawn** - Author withdrew the proposal

## RFC Workflow

### 1. Create RFC
```
/docs:rfc "Proposal Title"
```

### 2. Initial Draft
- Write comprehensive proposal
- Include motivation and context
- Document alternatives considered
- Add implementation plan

### 3. Share for Feedback
- Share RFC with team
- Update status to "In Review"
- Collect feedback in comments or discussions

### 4. Iterate
- Incorporate feedback
- Update proposal as needed
- Address concerns and questions
- Refine implementation details

### 5. Final Decision
- Stakeholders review final version
- Update status to "Accepted" or "Rejected"
- Document decision rationale

### 6. Implementation
- Reference RFC in PRs
- Update RFC with implementation notes
- Mark status as "Implemented" when complete

## Context Gathering Examples

```bash
# For API changes
!`find . -name "*router*" -o -name "*controller*" -o -name "*api*" | head -10`

# For feature additions
!`grep -r "export.*function\|export.*class" --include="*.ts" --include="*.js" . | head -20`

# For infrastructure changes
!`find . -name "*.yml" -o -name "*.yaml" -o -name "Dockerfile" | head -10`

# For performance changes
!`grep -r "cache\|redis\|memcache\|performance" --include="*.py" --include="*.ts" . | head -15`
```

## Important Notes

- **Write Before Implementing**: Create RFCs before starting work
- **Concrete Examples**: Include real code examples when possible
- **Address Concerns**: Proactively address potential objections
- **Update Actively**: RFC is a living document during review
- **Link Related Work**: Reference ADRs, issues, or other RFCs
- **Clear Language**: Keep accessible to all stakeholders
- **Define Success**: Include measurable success criteria

## Example Output

```
Request For Comments Created ✓

RFC-0003: Add GraphQL API Support
File: docs/rfc/RFC-0003-add-graphql-api-support.md
Status: Draft
Template: Standard
Author: Jane Developer

Next Steps:
  1. Complete the proposal sections
  2. Add implementation timeline
  3. Document testing strategy
  4. Share with team for feedback
  5. Update status to "In Review"
  6. Address feedback and iterate
  7. Get stakeholder approval
```

## When to Create RFCs

Create an RFC when proposing:
- Major feature additions
- Significant refactorings
- Architecture changes
- Breaking API changes
- New technology adoptions
- Process changes
- Performance optimizations with trade-offs
- Security enhancements
- Developer experience improvements

## Best Practices

- **Early Documentation**: Write RFC before implementation
- **Be Specific**: Include concrete examples and details
- **Show Your Work**: Document research and investigation
- **Consider Alternatives**: Show what else was considered and why
- **Realistic Timeline**: Include reasonable milestones
- **Risk Assessment**: Document known risks and mitigation
- **Stakeholder Input**: Identify who should review
- **Clear Outcomes**: Define what success looks like
- **Keep Updated**: Reflect changes made during review

---

**Template Location**: `commands/docs/templates/rfc/`
**Output Directory**: `docs/rfc/`
