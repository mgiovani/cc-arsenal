---
name: docs-adr
description: Create a numbered Architecture Decision Record (ADR) documenting a technical
  decision with context, alternatives, and consequences. Trigger on "create an ADR",
  "document this architectural decision", "record why we chose X", or "write an ADR
  for [decision]". Use docs-rfc instead when the decision is still open for discussion;
  use docs-adr once a choice has actually been made and needs a permanent record.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: <title> [variant]
allowed-tools: Read, Write, Grep, Glob, Task
context: fork
agent: general-purpose
---

# Create Architecture Decision Record

Create a new Architecture Decision Record (ADR) documenting an architectural decision.

## Anti-Hallucination Guidelines

ADRs document REAL decisions about REAL code. Before writing:
1. **Verify the technology exists** - If ADR mentions "Redis", confirm Redis is actually used
2. **Reference actual files** - Do not invent file paths; grep/glob to find real ones
3. **Quote real code** - If mentioning a pattern, find an actual example
4. **Check current state** - The "Context" section must reflect verified reality

## Workflow

### Phase 1: Explore Context

Before writing an ADR, use the Explore agent to understand the relevant codebase context:

```
Use Task tool with Explore agent:
- prompt: "Search for code related to [DECISION_TOPIC]. Find: 1) Current implementation if any, 2) Related configuration files, 3) Dependencies involved, 4) Any existing documentation. Return verified file paths and relevant code snippets."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract decision title from the command arguments
2. Check for variant keyword: `lightweight`, `full`, or `nygard`
3. If variant found, remove it from title
4. Default variant: `nygard` (Nygard style)

### Phase 3: Determine ADR Number

- Scan `docs/adr/` directory
- Find highest existing ADR number (format: `XXXX-*`)
- Increment by 1
- If no ADRs exist, start with `0001`
- Format as 4-digit padded number (e.g., `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

- Convert title to kebab-case
- Remove special characters
- Lowercase all letters
- Example: "Use Redis for Caching" -> `use-redis-for-caching`

### Phase 5: Gather Context

- Search codebase for relevant information about the decision topic
- Look for related code, configs, or documentation
- Understand current state and alternatives
- Keep context concise but informative

### Phase 6: Load and Populate Template

- Template location: `assets/templates/`
- Select based on variant:
  - `nygard` -> `nygard.md` (default)
  - `lightweight` -> `lightweight.md`
  - `full` -> `full.md`

Replace placeholders:
- `{{ADR_NUMBER}}` - 4-digit number
- `{{ADR_TITLE}}` - Original title (Title Case)
- `{{DATE}}` - Current date (YYYY-MM-DD)
- `{{CONTEXT}}` - Gathered context from codebase
- `{{PROJECT_NAME}}` - Git repo or directory name

### Phase 7: Create ADR File

- Filename: `docs/adr/XXXX-kebab-case-title.md`
- Ensure `docs/adr/` directory exists
- Write populated content
- Set initial status to "Proposed"

### Phase 8: Report Creation

- Show ADR number and title
- Display file path
- Provide next steps

## Template Variants

### Nygard Style (Default)
Michael Nygard's ADR format - concise and focused.

**Sections:** Title with number, Status, Context, Decision, Consequences

**Use when:** Most decisions, balanced detail

### Lightweight
Minimal ADR for quick decisions.

**Sections:** Title with number, Status, Decision, Rationale

**Use when:** Simple, straightforward decisions

### Full
Comprehensive ADR with detailed sections.

**Sections:** Title with number, Status, Context, Decision Drivers, Considered Options, Decision, Consequences (Positive, Negative, Neutral), Pros and Cons, Related Decisions, References

**Use when:** Complex, high-impact decisions

## Usage Examples

Basic ADR creation (uses Nygard template):
```
docs-adr "Database Migration Strategy"
docs-adr "API Authentication Approach"
docs-adr "Microservices Communication Pattern"
```

With template variant override:
```
docs-adr lightweight "Use Redis for Session Storage"
docs-adr full "Adopt Event-Driven Architecture"
```

## ADR Numbering

- **First ADR**: `0001-record-architecture-decisions.md` (meta-ADR)
- **Subsequent ADRs**: Auto-incremented (0002, 0003, etc.)
- **Format**: `XXXX-kebab-case-title.md`

## ADR Status Lifecycle

Update status in the ADR as the decision progresses:

1. **Proposed** - Initial proposal (default)
2. **Accepted** - Decision approved
3. **Deprecated** - No longer recommended
4. **Superseded** - Replaced by another ADR

## Context Gathering Examples

```bash
# For database decisions
find . -name "*.sql" -o -name "*models.py" -o -name "*schema.prisma" | head -10

# For API decisions
grep -r "router\|endpoint\|api" --include="*.py" --include="*.ts" --include="*.js" . | head -20

# For architecture decisions
find . -name "docker-compose.yml" -o -name "*.config.js" -o -name "*.config.ts" | head -10
```

## Important Notes

- **One Decision per ADR**: Keep focused on a single decision
- **Context Matters**: Include "why" even if it seems obvious
- **Link Related ADRs**: Reference superseded or related decisions
- **Early Documentation**: Create ADRs early in decision process
- **Imperative Language**: Use "we will" not "we should"
- **Status Updates**: Update status as decision progresses

## When to Create ADRs

Create an ADR when making:
- Technology stack decisions
- Architecture pattern choices
- Database or storage decisions
- API design choices
- Security architecture decisions
- Deployment strategy decisions
- Major library/framework selections
- Cross-cutting concerns (logging, caching, etc.)

## Best Practices

- **Create early**: Document decisions before implementation
- **Be honest**: Document the real reasons, not ideal reasons
- **Include alternatives**: Show what was considered
- **Accept trade-offs**: Acknowledge negative consequences
- **Link to code**: Reference implementation in the ADR
- **Review regularly**: Revisit ADRs during retrospectives
- **Update status**: Keep status current as decisions evolve
