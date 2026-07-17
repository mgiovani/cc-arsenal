---
name: create-rule
description: Create a new memory rule (CLAUDE.md entry or .claude/rules/*.md file)
  following Claude Code's memory-hierarchy conventions. Use when the user runs
  /create-rule or asks to add a project/user rule, coding standard, or workflow
  instruction to memory. Not for creating skills or slash commands — use
  create-skill for those.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: <rule-name> [description]
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(git *)
- Bash(mkdir *)
- AskUserQuestion
---

# Create Rule

Generate a new memory rule following Claude Code best practices for project instructions, coding standards, and workflow guidelines.

This creates **memory rules** (CLAUDE.md entries and `.claude/rules/` files), not skills or commands (use `create-skill` for those).

- Memory hierarchy and rule file spec: [references/memory-hierarchy.md](references/memory-hierarchy.md)
- Glob patterns and worked examples: [references/rule-examples.md](references/rule-examples.md)
- Official docs: https://code.claude.com/docs/en/memory

## Anti-hallucination guidelines

- Verify existing patterns first — check the actual codebase, don't assume conventions.
- Base rules on real code found in the project, not invented standards.
- If no convention exists, ask the user rather than making one up.
- Check existing CLAUDE.md / `.claude/rules/*.md` for conflicts before adding a new rule.
- Only use `paths` frontmatter on `.claude/rules/*.md` files — never on CLAUDE.md.

## Steps

1. **Parse arguments**: rule name from `$1` (or first word of the arguments), description from the rest — ask the user if either is missing.
2. **Check existing memory**: grep for `CLAUDE.md` and `.claude/rules/*.md` in the project. Skim what's there to match structure/tone and catch conflicts or duplicates with the new rule.
3. **Decide type and scope**:
   - Modular rule (`.claude/rules/<name>.md`) is preferred for a focused, single topic; a CLAUDE.md entry suits a short cross-cutting instruction.
   - Project scope (`.claude/rules/`, shared via git) vs. user scope (`~/.claude/rules/`, personal only) — ask if unclear from context.
   - Path-specific rules need `paths` frontmatter (see reference); general rules don't.
4. **Write the rule**, following the templates in [references/rule-examples.md](references/rule-examples.md): imperative language, specific expectations, one topic per file, code examples where useful.

## Example

`/create-rule api-errors "Standard error handling for API routes"` → writes `.claude/rules/api-errors.md` with `paths: src/api/**/*.ts` frontmatter and concrete guidelines (see reference for the full template).
