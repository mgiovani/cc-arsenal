# Skill Design Patterns

Common patterns for building effective skills with SubAgents, TodoWrite, and anti-hallucination techniques.

## SubAgent Usage Patterns

### When to Use Each Agent Type

```
Explore agent:
- Understanding codebase structure
- Finding relevant files/patterns
- Initial context gathering
- Read-only analysis tasks
- Use model: "haiku" for simple exploration tasks

Plan agent:
- Complex planning and reasoning
- Architecture decisions
- Multi-step strategy development

general-purpose agent:
- Semantic analysis of content
- Complex reasoning tasks
- Multi-step operations with file modifications
```

### Parallel SubAgent Pattern

Spawn multiple agents when tasks are independent:

```markdown
Spawn parallel Explore agents with model: haiku:

Agent 1 - [Aspect 1]:
- prompt: "[Specific exploration task]"
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - [Aspect 2]:
- prompt: "[Different aspect to explore]"
- subagent_type: "Explore"
- model: "haiku"

Agent 3 - [Aspect 3]:
- prompt: "[Another independent task]"
- subagent_type: "Explore"
- model: "haiku"
```

### context: fork Pattern

For skills that should run in isolation:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**Important**: `context: fork` skills do NOT have access to conversation history. The SKILL.md content becomes the complete prompt for the subagent.

## TodoWrite Progress Tracking

### When to Use TodoWrite

- Multi-step operations where tracking progress matters
- Skills that may take a long time to complete
- Operations where partial progress should be visible
- Complex workflows with multiple phases

### TodoWrite Pattern

```markdown
Use TodoWrite to track progress:

\`\`\`
TodoWrite:
- [ ] Phase 1: Explore codebase context
- [ ] Phase 2: Gather requirements
- [ ] Phase 3: Generate structure
- [ ] Phase 4: Write files
- [ ] Phase 5: Validate output
- [ ] Phase 6: Report results
\`\`\`

Update task status as completing each step.
```

## Anti-Hallucination Patterns

### For Documentation Skills

```markdown
## Anti-Hallucination Guidelines

**CRITICAL**: Before writing documentation:
1. **Verify files exist** before describing them
2. **Count entities** with actual commands, not estimates
3. **Reference real code** - do not invent file paths
4. **Quote actual implementations** - grep/read before citing
```

### For Code Generation Skills

```markdown
## Anti-Hallucination Guidelines

**CRITICAL**: Before generating code:
1. **Explore existing patterns first** - match the codebase style
2. **Verify imports/dependencies exist** - check package.json or pyproject.toml
3. **Check naming conventions** - use grep to find existing patterns
4. **Never guess test commands** - find the actual test runner
```

### For Analysis Skills

```markdown
## Anti-Hallucination Guidelines

**CRITICAL**: When analyzing code:
1. **Cross-reference claims with actual files** - read before asserting
2. **Provide evidence** - include file paths and line numbers
3. **Remove unverifiable claims** - if it cannot be proven, do not state it
4. **Check current state** - code may have changed since last analysis
```

### For File Creation Skills

```markdown
## Anti-Hallucination Guidelines

**CRITICAL**: Before creating files:
1. **Check if file already exists** - do not overwrite without confirmation
2. **Verify the target directory exists** - create it if needed
3. **Match existing conventions** - check similar files for patterns
4. **Validate generated content** - ensure syntax is correct
```

## Skill Template Patterns

### Simple Utility Skill

Best for focused, single-purpose operations:

```yaml
---
name: skill-name
description: "Clear description of what and when"
disable-model-invocation: true
argument-hint: "[argument]"
allowed-tools: Read, Edit, Grep, Glob
---

# Skill Title

Brief description.

## Workflow

### Phase 1: Explore
[Gather context]

### Phase 2: Execute
[Main logic]

### Phase 3: Verify
[Validation steps]
```

### Complex Analysis Skill

Best for multi-step operations needing exploration and reporting:

```yaml
---
name: skill-name
description: "Clear description of what and when"
disable-model-invocation: true
argument-hint: "[argument]"
allowed-tools: Read, Write, Edit, Grep, Glob, Task, TodoWrite
---

# Skill Title

Brief description.

## Anti-Hallucination Guidelines
[Domain-specific verification rules]

## Workflow

### Phase 1: Explore (Use Explore Agent)
[Parallel subagents for context]

### Phase 2: Analyze
[Core analysis logic]

### Phase 3: Track Progress (TodoWrite)
[Multi-step tracking]

### Phase 4: Generate Output
[Create deliverables]

### Phase 5: Verify
[Comprehensive validation]
```

### Skill with Supporting Files

For skills with extensive reference material:

```
skill-name/
├── SKILL.md                      # Core workflow (under 500 lines)
└── references/
    ├── detailed-guide.md          # Loaded when Claude needs specifics
    └── examples.md                # Example patterns and outputs
```

Reference from SKILL.md:
```markdown
## Additional Resources

- For complete API details, see [references/detailed-guide.md](references/detailed-guide.md)
- For usage examples, see [references/examples.md](references/examples.md)
```

## Tool Selection Guide

| Use Case | Recommended Tools |
|----------|-------------------|
| File operations | `Read`, `Write`, `Edit`, `Glob`, `Grep` |
| Git operations | `Bash(git *)` |
| GitHub operations | `Bash(gh *)` |
| Complex analysis | `Task` (with Explore or general-purpose agents) |
| Progress tracking | `TodoWrite` |
| Web research | `WebFetch`, `WebSearch` |
| User interaction | `AskUserQuestion` |
| Planning | `EnterPlanMode` |

## Progressive Disclosure Best Practices

1. **SKILL.md**: Keep under 500 lines. Include only essential workflow and instructions.
2. **references/**: Move detailed documentation, API specs, and examples here. Claude loads these only when needed.
3. **scripts/**: Include executable code that would otherwise be rewritten each time. Token-efficient since scripts can be executed without reading into context.
4. **assets/**: Templates, images, and boilerplate that get copied or modified in output.

### When to Split Content

Move content to references/ when:
- Detailed reference tables exceed 50 lines
- Multiple examples with full code snippets
- API documentation or schema definitions
- Domain-specific knowledge that is not always needed
- Historical context or background information
