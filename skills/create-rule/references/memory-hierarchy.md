# Memory Hierarchy Reference

Claude Code loads memory from multiple locations in priority order:

| Type | Location | Purpose | Shared With |
|------|----------|---------|-------------|
| **Enterprise** | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Organization-wide policies | All org users |
| **Project** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project instructions | Team via git |
| **Project Rules** | `./.claude/rules/*.md` | Modular, topic-specific rules | Team via git |
| **User** | `~/.claude/CLAUDE.md` | Personal preferences (all projects) | Just you |
| **User Rules** | `~/.claude/rules/*.md` | Personal modular rules | Just you |
| **Project Local** | `./CLAUDE.local.md` | Personal project preferences | Just you |

## Priority Rules

- More specific locations override general ones
- Project rules override user rules
- Path-specific rules only apply to matching files
- Enterprise rules serve as baseline; project rules refine

## Frontmatter Syntax

Only used for `.claude/rules/*.md` files that need path-specific activation:

```yaml
---
# Only for path-specific rules
paths: src/**/*.ts
# Supports glob patterns and brace expansion
paths: src/**/*.{ts,tsx}
# Multiple patterns with comma
paths: {src,lib}/**/*.ts, tests/**/*.test.ts
---
```

## Glob Pattern Reference

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` directory |
| `*.md` | Markdown files in project root only |
| `src/components/*.tsx` | React components in specific directory |
| `**/*.{ts,tsx}` | Both .ts and .tsx files anywhere |
| `{src,lib}/**/*.ts` | TypeScript in src/ or lib/ directories |

## Category Organization

Recommended structure for `.claude/rules/`:

```
.claude/rules/
├── code-style/
│   ├── formatting.md      # Indentation, line length, etc.
│   ├── naming.md          # Variable/function naming conventions
│   └── imports.md         # Import organization
├── testing/
│   ├── unit-tests.md      # Unit testing conventions
│   ├── integration.md     # Integration testing
│   └── mocking.md         # Mock patterns
├── security/
│   ├── authentication.md  # Auth patterns
│   ├── validation.md      # Input validation
│   └── secrets.md         # Secret handling
├── workflow/
│   ├── git.md             # Git conventions
│   ├── pr-reviews.md      # PR review process
│   └── deployment.md      # Deployment procedures
└── api-design.md          # API design guidelines
```

## Import Syntax

In CLAUDE.md files, you can import other files:

```markdown
@path/to/file.md
```

This includes the referenced file's content into the memory context.
