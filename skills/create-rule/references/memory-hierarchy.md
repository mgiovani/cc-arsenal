# Memory Hierarchy Reference

Every AI coding tool has its own place for standing project instructions. Detect which
one the project uses (see SKILL.md step 2) before writing anything.

## Claude Code

Loads memory from multiple locations, most specific wins:

| Type | Location | Purpose | Shared With |
|------|----------|---------|-------------|
| **Enterprise** | OS-specific, see below | Organization-wide policies | All org users |
| **Project** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project instructions | Team via git |
| **Project Rules** | `./.claude/rules/*.md` | Modular, topic-specific rules | Team via git |
| **User** | `~/.claude/CLAUDE.md` | Personal preferences (all projects) | Just you |
| **User Rules** | `~/.claude/rules/*.md` | Personal modular rules | Just you |
| **Project Local** | `./CLAUDE.local.md` | Personal project preferences | Just you |

Enterprise managed policy path (deployed by IT, not something this skill writes to):

| OS | Path |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux/WSL | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\ProgramData\ClaudeCode\CLAUDE.md` |

These are managed-deployment paths and can vary by organization — verify against
https://code.claude.com/docs/en/memory before relying on one, and never write to them
from this skill.

Priority: more specific overrides general; project rules override user rules;
path-specific rules only apply to matching files; enterprise rules are a baseline that
project rules refine.

### Frontmatter (`.claude/rules/*.md` only — never on `CLAUDE.md`)

```yaml
---
paths: src/**/*.ts
# Supports glob patterns and brace expansion
paths: src/**/*.{ts,tsx}
# Multiple patterns with comma
paths: {src,lib}/**/*.ts, tests/**/*.test.ts
---
```

### Import syntax (CLAUDE.md only)

```markdown
@path/to/file.md
```

Includes the referenced file's content into the memory context.

## AGENTS.md-style tools (Codex, Cursor, Copilot, Gemini CLI, OpenCode, ...)

A single tool-agnostic `AGENTS.md` at the repo root, read natively by these tools —
no frontmatter, no per-topic file split. This repo's own `AGENTS.md` (canonical,
tool-neutral) + `CLAUDE.md` (imports it via `@AGENTS.md` and adds Claude-only content)
is a live worked example of the pairing. When a project has `AGENTS.md` and no
Claude-specific files, add a new `##` section to it rather than creating a separate
file — the format has no concept of splitting rules across files.

## Cursor native rules

Cursor also supports its own format independent of `AGENTS.md`:

| Location | Purpose |
|----------|---------|
| `.cursor/rules/*.mdc` | Modular project rules, one file per topic |
| `.cursorrules` (legacy, repo root) | Older single-file format — don't create new ones, only append if it's the only thing present |

### Frontmatter (`.cursor/rules/*.mdc`)

```yaml
---
description: When this rule applies (used for auto-attachment)
globs: ["src/api/**/*.ts"]
alwaysApply: false
---
```

`alwaysApply: true` includes the rule in every request regardless of `globs`.

## Glob pattern reference (Claude Code `paths` / Cursor `globs`)

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` directory |
| `*.md` | Markdown files in project root only |
| `src/components/*.tsx` | React components in specific directory |
| `**/*.{ts,tsx}` | Both .ts and .tsx files anywhere |
| `{src,lib}/**/*.ts` | TypeScript in src/ or lib/ directories |

## Category organization (Claude Code `.claude/rules/`, Cursor `.cursor/rules/`)

Both tools support nested directories for organizing many rules:

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
