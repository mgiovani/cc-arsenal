---
name: docs-diagram
description: Generate Mermaid diagrams from codebase analysis including architecture,
  database schema, deployment, and security diagrams. This skill should be used when
  users want to create system diagrams, ER diagrams, architecture visualizations,
  or deployment diagrams.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: <type> [context]
allowed-tools: Read, Write, Grep, Glob, Task
context: fork
agent: general-purpose
---

# Docs Diagram

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Generate System Diagrams

Generate Mermaid diagrams including architecture, database schema, deployment, and security architecture.

## Anti-Hallucination Guidelines

**CRITICAL**: Diagrams must represent REAL components. Before adding ANY element:
1. **Verify component exists** - Read the actual file before adding it to diagram
2. **Confirm relationships** - Check imports/references to verify connections
3. **Count entities accurately** - Use find/glob to get exact counts
4. **No placeholder components** - Only include verified, existing elements
5. **Empty directories != components** - Check directories have actual content

## Supported Diagram Types

| Type | Output File | Description |
|------|------------|-------------|
| `er` | `docs/data-model.md` | Entity-Relationship diagram from database models |
| `arch` | `docs/architecture.md` | System architecture and component relationships |
| `deployment` | `docs/deployment.md` | Deployment infrastructure and CI/CD |
| `security` | `docs/security.md` | Security architecture and data flow |

## Workflow

### Phase 1: Deep Analysis (Explore Codebase)

Use the Explore agent to thoroughly analyze the codebase before generating diagrams:

### Phase 2: Parse Arguments

1. Extract diagram type from `command arguments`
2. Supported types: `er`, `arch`, `deployment`, `security`
3. Extract optional context (remaining arguments)
4. If type not provided or invalid, show available types and exit with helpful message

### Phase 3: Parallel Verification (Use Parallel Analysis)

Before generating, spawn parallel agents to verify different aspects. See [references/detection-patterns.md](references/detection-patterns.md) for specific detection commands per diagram type.

```
Example: Generating an architecture diagram

Agent 1 - Verify Services:
- prompt: "Find all actual service files/classes in the codebase. Return a list of verified service names with their file paths. Do NOT assume - only return what you can find."
- agent-type: "Explore"

Agent 2 - Verify Databases:
- prompt: "Find all database configurations and connections. Look for DB URLs, ORM configs, connection pools. Return verified database technologies with evidence."
- agent-type: "Explore"

Agent 3 - Verify External Integrations:
- prompt: "Find all external API calls, third-party service integrations. Look for HTTP clients, SDK imports, webhook handlers. Return verified external dependencies."
- agent-type: "Explore"

Agent 4 - Verify Data Flow:
- prompt: "Trace how data flows between components. Look at imports, function calls, event handlers. Return verified connections between components."
- agent-type: "Explore"

Merge results -> Only include verified entities in diagram
**Verification checklist before adding to diagram**:
1. Read the actual source file to confirm it exists
2. For relationships, verify the import/reference exists in code
3. For counts (e.g., "5 services"), run: `find . -name "*service*" | wc -l`
4. Remove any component that cannot be verified with actual code

### Phase 4: Generate Mermaid Diagram

- Create appropriate Mermaid syntax based on type
- **ONLY include verified components** - no assumptions
- Include meaningful labels and relationships
- Add comments for clarity
- Keep diagram readable (not too complex)

For Mermaid syntax patterns per diagram type, see [references/mermaid-patterns.md](references/mermaid-patterns.md).

### Phase 5: Load and Populate Template

- Template location: `assets/templates/`
- Select based on diagram type:
 - `er` -> `data-model.md`
 - `arch` -> `architecture.md`
 - `deployment` -> `deployment.md`
 - `security` -> `security.md`

Replace placeholders:
- `{{PROJECT_NAME}}` - Git repo or directory name
- `{{DATE}}` - Current date
- `{{ER_DIAGRAM}}` or `{{DIAGRAM_CONTENT}}` - Generated Mermaid code
- `{{ENTITIES}}` or `{{COMPONENTS}}` - Entity/component descriptions

### Phase 6: Create or Update Documentation

- Output to appropriate file in `docs/`
- If file exists, ask before overwriting
- Preserve custom content if possible

### Phase 7: Report Results

- Show diagram type and output file
- Display summary of what was detected
- Provide next steps

## Usage Examples

Generate specific diagram type:
```
docs-diagram er
docs-diagram arch
docs-diagram deployment
docs-diagram security
With additional context:
```
docs-diagram er for user and order tables
docs-diagram arch for microservices architecture
docs-diagram deployment with Docker and Kubernetes
Show available types:
```
docs-diagram
## Important Notes

- **Auto-detection**: Diagrams generated from actual code
- **Mermaid format**: Uses GitHub-compatible Mermaid syntax
- **Readable diagrams**: Limits complexity for clarity
- **Incremental**: Can regenerate as code evolves
- **Template-based**: Uses templates for consistent formatting
- **Context-aware**: Uses optional context to guide generation

## When to Run

- Database schema has been modified (`er`)
- Architecture has evolved (`arch`)
- Deployment configuration changed (`deployment`)
- Security architecture modified (`security`)
- Onboarding new team members (all diagrams)
- Documentation review (all diagrams)

## Best Practices

- **Keep current**: Regenerate after significant changes
- **Review generated**: Always review auto-generated content
- **Add context**: Supplement with manual descriptions
- **Link diagrams**: Reference diagrams in related docs
- **Version control**: Commit diagram updates with code changes
- **Simplify**: Break complex diagrams into multiple views

## Additional Resources

- For Mermaid syntax per diagram type, see [references/mermaid-patterns.md](references/mermaid-patterns.md)
- For codebase detection commands, see [references/detection-patterns.md](references/detection-patterns.md)

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Deep Analysis (Use Explore Agent)

Use the Explore agent to thoroughly analyze the codebase before generating diagrams:

```
Use Task tool with Explore agent:
- prompt: "For [DIAGRAM_TYPE] diagram, find all relevant components. For ER: find model/entity files and their relationships. For arch: find services, APIs, databases. For deployment: find Docker/K8s configs. Return ONLY verified files with their actual content structure."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract diagram type from `$ARGUMENTS`
2. Supported types: `er`, `arch`, `deployment`, `security`
3. Extract optional context (remaining arguments)
4. If type not provided or invalid, show available types and exit with helpful message

### Phase 3: Parallel Verification (Use SubAgents)

Before generating, spawn parallel agents to verify different aspects. See [references/detection-patterns.md](references/detection-patterns.md) for specific detection commands per diagram type.

```
Example: Generating an architecture diagram

Agent 1 - Verify Services:
- prompt: "Find all actual service files/classes in the codebase. Return a list of verified service names with their file paths. Do NOT assume - only return what you can find."
- subagent_type: "Explore"

Agent 2 - Verify Databases:
- prompt: "Find all database configurations and connections. Look for DB URLs, ORM configs, connection pools. Return verified database technologies with evidence."
- subagent_type: "Explore"

Agent 3 - Verify External Integrations:
- prompt: "Find all external API calls, third-party service integrations. Look for HTTP clients, SDK imports, webhook handlers. Return verified external dependencies."
- subagent_type: "Explore"

Agent 4 - Verify Data Flow:
- prompt: "Trace how data flows between components. Look at imports, function calls, event handlers. Return verified connections between components."
- subagent_type: "Explore"

Merge results -> Only include verified entities in diagram
```

**Verification checklist before adding to diagram**:
1. Read the actual source file to confirm it exists
2. For relationships, verify the import/reference exists in code
3. For counts (e.g., "5 services"), run: `find . -name "*service*" | wc -l`
4. Remove any component that cannot be verified with actual code

### Phase 4: Generate Mermaid Diagram

- Create appropriate Mermaid syntax based on type
- **ONLY include verified components** - no assumptions
- Include meaningful labels and relationships
- Add comments for clarity
- Keep diagram readable (not too complex)

For Mermaid syntax patterns per diagram type, see [references/mermaid-patterns.md](references/mermaid-patterns.md).

### Phase 5: Load and Populate Template

- Template location: `assets/templates/`
- Select based on diagram type:
  - `er` -> `data-model.md`
  - `arch` -> `architecture.md`
  - `deployment` -> `deployment.md`
  - `security` -> `security.md`

Replace placeholders:
- `{{PROJECT_NAME}}` - Git repo or directory name
- `{{DATE}}` - Current date
- `{{ER_DIAGRAM}}` or `{{DIAGRAM_CONTENT}}` - Generated Mermaid code
- `{{ENTITIES}}` or `{{COMPONENTS}}` - Entity/component descriptions

### Phase 6: Create or Update Documentation

- Output to appropriate file in `docs/`
- If file exists, ask before overwriting
- Preserve custom content if possible

### Phase 7: Report Results

- Show diagram type and output file
- Display summary of what was detected
- Provide next steps
