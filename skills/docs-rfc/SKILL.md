---
name: docs-rfc
description: Create numbered RFC (Request For Comments) documents for proposing and
  discussing changes. This skill should be used when users want to write a proposal,
  create an RFC, or formally document a proposed change.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: <title> [variant]
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task
context: fork
agent: general-purpose
---

# Docs Rfc

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Create Request For Comments

Create a new RFC (Request For Comments) document for proposing and discussing changes.

## Anti-Hallucination Guidelines

**CRITICAL**: RFCs propose changes to REAL systems. Before writing:
1. **Verify current state** - Explore the codebase to understand what exists today
2. **Reference actual code** - Do not invent APIs or patterns; find real examples
3. **Check dependencies** - Verify libraries/tools mentioned actually exist in project
4. **Validate assumptions** - Each claim about current state must be verified

## Workflow

### Phase 1: Explore Current State (Explore Codebase)

Before writing an RFC, thoroughly explore the codebase to understand current state:

### Phase 2: Parse Arguments

1. Extract proposal title from `command arguments`
2. Check for variant keyword: `minimal`, `standard`, or `detailed`
3. If variant found, remove it from title
4. Default variant: `standard`

### Phase 3: Determine RFC Number

- Scan `docs/rfc/` directory
- Find highest existing RFC number (format: `RFC-XXXX-*`)
- Increment by 1
- If no RFCs exist, start with `0001`
- Format as 4-digit padded number (e.g., `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

- Convert title to kebab-case
- Remove special characters
- Lowercase all letters
- Example: "Add GraphQL API Support" -> `add-graphql-api-support`

### Phase 5: Gather Context

- Analyze codebase to understand current state
- Identify relevant files and patterns
- Find similar implementations or related features
- Understand technical constraints

### Phase 6: Get Author Information

```bash
# Try to get git author
!`git config user.name 2>/dev/null || echo "Development Team"`
### Phase 7: Load and Populate Template

- Template location: `assets/templates/`
- Select based on variant:
 - `minimal` -> `minimal.md`
 - `standard` -> `standard.md` (default)
 - `detailed` -> `detailed.md`

Replace placeholders:
- `{{RFC_NUMBER}}` - 4-digit number
- `{{RFC_TITLE}}` - Original title (Title Case)
- `{{DATE}}` - Current date (YYYY-MM-DD)
- `{{AUTHOR}}` - Git user name or "Development Team"
- `{{CONTEXT}}` - Gathered context from codebase
- `{{PROJECT_NAME}}` - Git repo or directory name

### Phase 8: Create RFC File

- Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
- Ensure `docs/rfc/` directory exists
- Write populated content
- Set initial status to "Draft"

### Phase 9: Report Creation

- Show RFC number and title
- Display file path
- Provide workflow guidance

## Template Variants

### Minimal Template
Quick proposal format for small changes.

**Sections:** Summary, Motivation, Proposal, Open Questions

**Use when:** Small features, minor changes

### Standard Template (Default)
Balanced RFC for most changes.

**Sections:** Summary, Motivation, Proposal, Rationale and Alternatives, Implementation Plan, Testing Plan, Migration Strategy, Open Questions, Timeline

**Use when:** Most feature proposals

### Detailed Template
Comprehensive RFC for major changes.

**Sections:** Summary, Background and Motivation, Goals and Non-Goals, Proposal, Detailed Design, Rationale and Alternatives, Implementation Plan, Testing and Quality Assurance, Migration and Rollout Strategy, Monitoring and Metrics, Security Considerations, Performance Implications, Open Questions and Risks, Timeline and Milestones, Appendices

**Use when:** Major features, architectural changes

## Usage Examples

Basic RFC creation (uses Standard template):
```
docs-rfc "Add GraphQL API Support"
docs-rfc "Implement Rate Limiting"
docs-rfc "Add Multi-Tenancy Support"
With template variant override:
```
docs-rfc minimal "Update Logging Format"
docs-rfc detailed "Migration to Microservices Architecture"
docs-rfc detailed "Adopt Event Sourcing Pattern"
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
docs-rfc "Proposal Title"
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
## Important Notes

- **Write Before Implementing**: Create RFCs before starting work
- **Concrete Examples**: Include real code examples when possible
- **Address Concerns**: Proactively address potential objections
- **Update Actively**: RFC is a living document during review
- **Link Related Work**: Reference ADRs, issues, or other RFCs
- **Clear Language**: Keep accessible to all stakeholders
- **Define Success**: Include measurable success criteria

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

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Explore Current State (Use Explore Agent)

Before writing an RFC, thoroughly explore the codebase to understand current state:

```
Use Task tool with Explore agent:
- prompt: "Analyze the codebase to understand [RFC_TOPIC]. Find: 1) Current implementation patterns, 2) Related components and their interactions, 3) Existing similar features, 4) Technical constraints. Return verified findings with file paths."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract proposal title from `$ARGUMENTS`
2. Check for variant keyword: `minimal`, `standard`, or `detailed`
3. If variant found, remove it from title
4. Default variant: `standard`

### Phase 3: Determine RFC Number

- Scan `docs/rfc/` directory
- Find highest existing RFC number (format: `RFC-XXXX-*`)
- Increment by 1
- If no RFCs exist, start with `0001`
- Format as 4-digit padded number (e.g., `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

- Convert title to kebab-case
- Remove special characters
- Lowercase all letters
- Example: "Add GraphQL API Support" -> `add-graphql-api-support`

### Phase 5: Gather Context

- Analyze codebase to understand current state
- Identify relevant files and patterns
- Find similar implementations or related features
- Understand technical constraints

### Phase 6: Get Author Information

```bash
# Try to get git author
!`git config user.name 2>/dev/null || echo "Development Team"`
```

### Phase 7: Load and Populate Template

- Template location: `assets/templates/`
- Select based on variant:
  - `minimal` -> `minimal.md`
  - `standard` -> `standard.md` (default)
  - `detailed` -> `detailed.md`

Replace placeholders:
- `{{RFC_NUMBER}}` - 4-digit number
- `{{RFC_TITLE}}` - Original title (Title Case)
- `{{DATE}}` - Current date (YYYY-MM-DD)
- `{{AUTHOR}}` - Git user name or "Development Team"
- `{{CONTEXT}}` - Gathered context from codebase
- `{{PROJECT_NAME}}` - Git repo or directory name

### Phase 8: Create RFC File

- Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
- Ensure `docs/rfc/` directory exists
- Write populated content
- Set initial status to "Draft"

### Phase 9: Report Creation

- Show RFC number and title
- Display file path
- Provide workflow guidance
