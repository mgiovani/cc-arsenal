---
name: docs-diagram
description: Generate a Mermaid diagram (er, arch, deployment, or security) by reading
  the actual codebase and writing it to docs/. Use for requests like "draw an ER
  diagram of these tables", "show me the architecture", "diagram the deployment
  setup", or "visualize the security data flow". Not for scaffolding a new docs
  structure (use docs-init) or syncing existing prose docs with code (use docs-update)
  — this skill only produces diagrams.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: <type> [context]
allowed-tools: Read, Write, Grep, Glob, Task
context: fork
agent: general-purpose
---

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

### Phase 1: Parse Arguments

1. Extract diagram type from `$ARGUMENTS`
2. Supported types: `er`, `arch`, `deployment`, `security`
3. Extract optional context (remaining arguments)
4. If type not provided or invalid, show available types and exit with helpful message

### Phase 2: Analyze the Codebase

Scale the analysis to the request — a small, scoped ask doesn't need the same fan-out as "diagram the whole system":

- **Scoped request** (e.g. "er diagram for the user and order tables"): Read/Grep the named files directly. No subagent needed.
- **Broad or ambiguous request** (e.g. "show me the architecture" on an unfamiliar codebase): spawn one Explore subagent (`subagent_type: "Explore"`) per aspect that matters for the diagram type — e.g. for `arch`, one agent for services, one for databases, one for external integrations, one for data flow. Only spawn the agents relevant to what's being diagrammed; skip aspects the request doesn't touch.

See [references/detection-patterns.md](references/detection-patterns.md) for detection commands per diagram type.

**Verification checklist before adding anything to the diagram**:
1. Read the actual source file to confirm it exists
2. For relationships, verify the import/reference exists in code
3. For counts (e.g., "5 services"), run: `find . -name "*service*" | wc -l`
4. Drop any component that cannot be verified with actual code

### Phase 3: Generate Mermaid Diagram

- Create appropriate Mermaid syntax based on type
- **ONLY include verified components** - no assumptions
- Include meaningful labels and relationships
- Add comments for clarity
- Keep diagram readable (not too complex)

For Mermaid syntax patterns per diagram type, see [references/mermaid-patterns.md](references/mermaid-patterns.md).

### Phase 4: Load and Populate Template

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

### Phase 5: Create or Update Documentation

- Output to appropriate file in `docs/`
- If file exists, ask before overwriting
- Preserve custom content if possible

### Phase 6: Report Results

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
```

With additional context:
```
docs-diagram er for user and order tables
docs-diagram arch for microservices architecture
docs-diagram deployment with Docker and Kubernetes
```

Show available types:
```
docs-diagram
```

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
