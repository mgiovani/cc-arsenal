---
# Enhancement for: docs-diagram
disable-model-invocation: true
argument-hint: "<type> [context]"
allowed-tools: "Read, Write, Grep, Glob, Task"
context: "fork"
agent: "general-purpose"
---

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
