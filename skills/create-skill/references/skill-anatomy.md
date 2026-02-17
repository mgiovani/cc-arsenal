# Skill Anatomy

Deep dive into skill structure, folder conventions, progressive disclosure, and composition patterns.

## Directory Structure

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

## SKILL.md (Required)

### Frontmatter

The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it.

**Required fields:**
- `name`: Kebab-case identifier (e.g., `create-skill`, `docs-adr`)
- `description`: Clear, specific description (>50 chars, third-person)

**Common optional fields:**
- `metadata`: Author, version, source
- `argument-hint`: Placeholder for skill arguments (e.g., `[skill-description]`)
- `disable-model-invocation`: Set to `true` for user-invoked-only skills
- `allowed-tools`: List of tools the skill can use

**Writing style:** Use third-person in description (e.g., "This skill should be used when..." instead of "Use this skill when...").

### Instructions

Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X").

**Keep SKILL.md lean:** Target <500 lines. Move detailed information to `references/` files.

## Bundled Resources (Optional)

### scripts/ - Executable Code

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

**When to include:**
- The same code is being rewritten repeatedly
- Deterministic reliability is needed
- Code is complex enough to be error-prone when written by hand

**Examples:**
- `scripts/rotate_pdf.py` - PDF rotation logic
- `scripts/parse_openapi.py` - OpenAPI spec parsing
- `scripts/quick_validate.py` - Skill validation checks

**Benefits:**
- Token efficient (may be executed without loading into context)
- Deterministic (same input → same output every time)
- Reusable across multiple invocations

**Note:** Scripts may still need to be read by Claude for patching or environment-specific adjustments.

### references/ - Documentation

Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

**When to include:**
- Documentation that Claude should reference while working
- Information needed occasionally, not every invocation
- Detailed information that would bloat SKILL.md

**Examples:**
- `references/finance.md` - Financial schemas and business rules
- `references/mnda.md` - Company NDA template for reference
- `references/policies.md` - Company-specific policies
- `references/api_docs.md` - API endpoint specifications
- `references/database_schema.md` - Database table structures

**Use cases:**
- Database schemas
- API documentation
- Domain knowledge
- Company policies
- Detailed workflow guides

**Benefits:**
- Keeps SKILL.md lean and focused
- Loaded only when Claude determines it's needed (progressive disclosure)
- Easy to update without changing core skill logic

**Best practices:**
- If files are large (>10k words), include grep search patterns in SKILL.md
- Avoid duplication between SKILL.md and references/
- Prefer references/ for detailed information; keep only essential instructions in SKILL.md

### assets/ - Output Files

Files not intended to be loaded into context, but rather used within the output Claude produces.

**When to include:**
- Files that will be used in the final output
- Templates that get copied or modified
- Boilerplate code that gets customized

**Examples:**
- `assets/logo.png` - Brand assets for generated documents
- `assets/slides.pptx` - PowerPoint templates
- `assets/frontend-template/` - HTML/React boilerplate
- `assets/font.ttf` - Typography files
- `assets/api-template.md` - Documentation template

**Use cases:**
- Templates
- Images and icons
- Boilerplate code
- Fonts
- Sample documents

**Benefits:**
- Separates output resources from documentation
- Enables Claude to use files without loading them into context
- Provides consistent starting points for generated content

## Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
   - Determines when the skill activates
   - Minimal context overhead for skills not in use

2. **SKILL.md body** - When skill triggers (<5k words)
   - Core workflow and instructions
   - Loaded only when skill is invoked

3. **Bundled resources** - As needed by Claude (Unlimited*)
   - scripts/ may be executed without reading
   - references/ loaded when Claude determines it's useful
   - assets/ used for output without context loading

*Unlimited because scripts can be executed without reading into context window.

## Skill Composition

Skills can reference and invoke other existing skills as reusable components. This follows the "don't repeat yourself" principle and creates a more maintainable ecosystem.

### When to Compose with Existing Skills

**Consider composition when:**
- An existing skill already does part of what you need
- The composed skill is stable and well-maintained
- Composition is clearer than reimplementation
- Multiple skills could benefit from the same component

**Examples:**
- A deploy skill invoking `git-commit` for creating deployment commits
- A feature implementation skill invoking `fix-bug` for handling issues during development
- A testing skill invoking `review-security` for security checks
- An API docs skill invoking `docs-diagram` for adding visualizations

### How to Compose Skills

**Reference in instructions:**
```markdown
After implementing the feature, use the existing `/git-commit` skill to create a conventional commit message.
```

**Direct invocation:**
```markdown
Invoke the `/docs-diagram` skill to generate architecture diagrams for the documentation.
```

**Conditional composition:**
```markdown
If security concerns are identified, recommend running `/review-security` on the affected files.
```

### Benefits of Composition

- **Maintainability**: Updates to composed skills benefit all consumers
- **Consistency**: Ensures uniform behavior across workflows (e.g., all skills use the same commit format)
- **Token efficiency**: Reference established patterns instead of repeating instructions
- **Expertise reuse**: Leverage specialized skills without duplicating domain knowledge

### Composition Discovery (Phase 2)

When creating a new skill, the Explore agent in Phase 2 should identify potential composition opportunities:
- Search cc-arsenal `skills/` for relevant existing skills
- List composable skills with descriptions of how they could be used
- Consider whether composition is better than reimplementation

## Anti-Hallucination Patterns

Skills should include verification steps to prevent Claude from assuming things that aren't true:

**File verification:**
```markdown
- Use Glob to verify directory exists before mkdir
- Use Grep to confirm patterns before recommending them
- Read existing code before suggesting modifications
```

**Path validation:**
```markdown
- Never reference files without checking they exist
- Use Read tool to verify file contents before editing
- Confirm all internal links resolve before generating
```

**Tool verification:**
```markdown
- Only include tools in allowed-tools that are actually used
- Verify tool availability before including in workflow
- Don't guess at tool syntax - reference documentation
```

## Writing Style Guidelines

**Imperative/infinitive form:**
- ✅ "To accomplish X, do Y"
- ✅ "Create the file structure"
- ✅ "Fetch the latest specification"
- ❌ "You should create the file structure"
- ❌ "If you need to fetch..."

**Third-person descriptions:**
- ✅ "This skill should be used when users want to..."
- ✅ "The skill generates documentation..."
- ❌ "Use this skill when you want to..."
- ❌ "You can generate documentation..."

**Objective tone:**
- Focus on what to do, not how Claude might feel about it
- Avoid anthropomorphizing ("Claude understands", "Claude knows")
- Use clear, direct instructions

## Common Pitfalls

1. **Monolithic SKILL.md**: Move detailed docs to references/ to keep core instructions lean
2. **Unused bundled resources**: Don't create scripts/ or references/ unless they're actually needed
3. **Vague descriptions**: Be specific about what triggers the skill
4. **Missing verification**: Always include checks to validate success
5. **Ignoring composition**: Don't reimplement what existing skills do well
6. **Over-tooling**: Only request tools actually used in the workflow
7. **Duplication**: Information should live in either SKILL.md or references/, not both
