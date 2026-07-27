---
name: create-rule
description: Create a new memory/instruction rule for whatever AI coding tool a project
  actually uses, a CLAUDE.md entry or .claude/rules/*.md file for Claude Code, an
  AGENTS.md entry for Codex/Cursor/Copilot/Gemini-CLI-style tools, or a .cursor/rules/*.mdc
  file for Cursor. Use when the user runs /create-rule or asks to add a project rule,
  user/personal rule, coding standard, style guide entry, or workflow instruction to
  memory, AGENTS.md, or CLAUDE.md. Not for creating skills or slash commands (use
  create-skill). Not for discovering or installing existing third-party skills (use
  find-skills).
metadata:
  author: mgiovani
  version: 2.0.0
disable-model-invocation: false
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

Generate a new memory rule (a project instruction, coding standard, or workflow
guideline) in whatever format the project's AI tooling actually reads.

This creates **memory rules**, not skills or commands (use `create-skill`) and not a
search for existing skills to install (use `find-skills`).

- Tool conventions, OS-specific paths, and frontmatter formats: [references/memory-hierarchy.md](references/memory-hierarchy.md)
- Worked templates per tool and scope: [references/rule-examples.md](references/rule-examples.md)
- Claude Code memory docs: https://code.claude.com/docs/en/memory

## Anti-hallucination guidelines

- Verify existing patterns first: check the actual codebase, don't assume conventions.
- Base rules on real code found in the project, not invented standards.
- If no convention exists, ask the user rather than making one up.
- Check existing CLAUDE.md / AGENTS.md / `.claude/rules/*.md` / `.cursor/rules/*.mdc` for conflicts before adding a new rule.
- Only use `paths` frontmatter on `.claude/rules/*.md` (Claude Code) or `globs` on `.cursor/rules/*.mdc` (Cursor), never on CLAUDE.md or AGENTS.md, which have no frontmatter.

## Steps

1. **Parse arguments**: rule name from `$1` (or the first word of the arguments),
   description from the rest: ask the user if either is missing.
2. **Detect the tool convention** by checking what's already in the repo:
   - `CLAUDE.md` or `.claude/rules/*.md` present → Claude Code.
   - `AGENTS.md` present (with no Claude-specific files) → Codex/Cursor/Copilot/Gemini-CLI-style tool. This repo's own `AGENTS.md` + `CLAUDE.md` pair is a live example of the pattern.
   - `.cursor/rules/*.mdc` present → Cursor's native format.
   - More than one convention present → ask which the user wants updated (or write to more than one, if the user says so).
   - None present → ask the user which tool/format they use before writing anything.
3. **Decide type and scope** for the detected tool (details and templates in the reference):
   - Claude Code: modular `.claude/rules/<name>.md` for a focused single topic vs. a `CLAUDE.md` entry for a short cross-cutting instruction; project (`.claude/rules/`, git-shared) vs. user (`~/.claude/rules/`, personal): ask if unclear from context; path-specific rules need `paths` frontmatter.
   - AGENTS.md-style tools: append a new section to the single root `AGENTS.md`, this format has no per-topic file split or frontmatter.
   - Cursor: `.cursor/rules/<name>.mdc` with `description`/`globs`/`alwaysApply` frontmatter; scope by directory nesting for path-specific rules.
4. **Write the rule**, following the matching template in [references/rule-examples.md](references/rule-examples.md): imperative language, specific expectations, one topic per file, code examples where useful.

## Examples

- `/create-rule api-errors "Standard error handling for API routes"` in a Claude Code repo → writes `.claude/rules/api-errors.md` with `paths: src/api/**/*.ts` frontmatter and concrete guidelines.
- `/create-rule formatting "2-space indentation, single quotes"` in a Claude Code repo, no path scope needed → writes `.claude/rules/formatting.md` with no frontmatter.
- `/create-rule --user preferences "Prefer functional patterns, async/await over raw promises"` → writes `~/.claude/rules/preferences.md` (personal, not git-shared).
- `/create-rule testing "Use table-driven tests and no test interdependence"` in a repo with only `AGENTS.md` → appends a `## Testing` section to `AGENTS.md` instead of creating a new file.
- `/create-rule react-components "Function components only, props typed with interfaces"` in a Cursor repo → writes `.cursor/rules/react-components.mdc` with `globs: ["**/*.tsx"]` frontmatter.
