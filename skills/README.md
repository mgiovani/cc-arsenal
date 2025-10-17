# Skills

Model-invoked capabilities that Claude automatically loads when relevant to the current task.

## What are Skills?

Skills are modular, self-contained packages that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. Unlike agents (explicitly invoked) or commands (user-invoked), **Skills are automatically activated by Claude** when the task matches the skill's description.

### Key Characteristics

- **Model-invoked**: Claude autonomously decides when to use them based on context
- **Composable**: Multiple skills can work together seamlessly
- **Efficient**: Progressive disclosure loads only what's needed to save context
- **Portable**: Same format works across Claude apps, Claude Code, and API

## Available Skills

### skill-creator

Comprehensive guide for creating effective skills with specialized knowledge, workflows, or tool integrations. This skill activates when you want to create or update a skill.

**Includes:**
- Complete skill creation process documentation
- Template generation script (`init_skill.py`)
- Validation script (`quick_validate.py`)
- Packaging script (`package_skill.py`)

### jira-cli

Interactive command-line tool for Atlassian Jira. This skill activates when working with Jira issues, epics, sprints, or when users mention Jira workflows and issue management.

**Provides:**
- Setup instructions for Cloud and on-premise installations
- Comprehensive command reference for issues, epics, and sprints
- Common workflow examples (daily standup, sprint planning, code review, bug triage)
- Scripting examples for automation
- Best practices and troubleshooting guidance

## Creating a New Skill

### 1. Initialize

```bash
python skills/skill-creator/scripts/init_skill.py my-skill-name --path skills
```

This creates a new skill directory with:
- `SKILL.md` template with YAML frontmatter and TODO placeholders
- `scripts/` directory with example executable script
- `references/` directory with example documentation
- `assets/` directory with example asset files

### 2. Edit

Update the generated `SKILL.md` file:

```yaml
---
name: my-skill-name
description: Complete explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.
---
```

**Important:**
- Use third-person description (e.g., "This skill should be used when..." not "Use this skill when...")
- Be specific about activation triggers
- Use imperative/infinitive form in instructions (e.g., "To accomplish X, do Y" not "You should do X")

### 3. Add Resources (Optional)

#### scripts/
Executable code (Python/Bash/etc.) for deterministic operations:
- When the same code is repeatedly rewritten
- When deterministic reliability is needed
- Can be executed without loading into context

#### references/
Documentation loaded into context as needed:
- API documentation, database schemas
- Domain knowledge, company policies
- Detailed workflow guides
- For large files (>10k words), include grep patterns in SKILL.md

#### assets/
Files used in output (NOT loaded into context):
- Templates (.pptx, .docx, boilerplate directories)
- Images, icons, fonts
- Sample data files
- Boilerplate code

### 4. Validate

```bash
python skills/skill-creator/scripts/quick_validate.py skills/my-skill-name
```

Checks:
- YAML frontmatter format and required fields
- Naming conventions (hyphen-case: lowercase with hyphens)
- Description completeness
- File organization

### 5. Package

```bash
python skills/skill-creator/scripts/package_skill.py skills/my-skill-name
```

Creates a distributable zip file after validation passes.

## Skill Architecture

Every skill follows this structure:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/      - Executable code
    ├── references/   - Documentation
    └── assets/       - Output files
```

## Progressive Disclosure

Skills use a three-level loading system to manage context efficiently:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - Loaded when skill triggers (<5k words)
3. **Bundled resources** - Loaded only when Claude needs them (unlimited)

## Best Practices

### Writing SKILL.md

- **Be specific**: Include exact scenarios that should trigger the skill
- **Use imperative form**: "To accomplish X, do Y" (not "You should do X")
- **Keep it lean**: Move detailed content to references/ files
- **Reference bundled resources**: Tell Claude how to use scripts/references/assets

### Organizing Resources

- **Avoid duplication**: Information should live in either SKILL.md or references/, not both
- **Delete unused examples**: The init script creates example files you may not need
- **Use appropriate resource types**:
  - Scripts for code that would be repeatedly rewritten
  - References for documentation Claude should load
  - Assets for files used in final output

### Testing

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify improvements to SKILL.md or bundled resources
4. Iterate and test again

## Skill vs Agent vs Command vs Hook

| Feature | Skills | Agents | Commands | Hooks |
|---------|--------|--------|----------|-------|
| **Invocation** | Automatic (model-invoked) | Explicit (Task tool) | Explicit (slash command) | Event-driven |
| **Use Case** | Domain expertise, tool integrations | Complex multi-step tasks | User-controlled operations | Safety validation |
| **Context** | Progressive disclosure | Stateless, single-shot | Direct execution | Background checks |
| **Example** | skill-creator activates automatically | `/task "Use bmad-dev agent"` | `/commit`, `/test` | Pre-commit hooks |

## Resources

- **Anthropic Skills Documentation**: https://docs.claude.com/docs/claude-code/skills
- **Skills Repository**: https://github.com/anthropics/skills
- **Announcement**: https://www.anthropic.com/news/skills

## License

Skills are based on the Anthropic skills framework. See individual skill LICENSE files for details.
