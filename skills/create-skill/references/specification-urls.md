# Specification URLs

Canonical URLs for skill specifications, best practices, and examples. These should be fetched fresh in Phase 0 of every skill creation.

## Primary Specifications

### Agent Skills Standard
- **What Are Skills**: https://agentskills.io/what-are-skills.md
  - Extract: Definition of skills, when to use them, anatomy overview

- **Specification**: https://agentskills.io/specification.md
  - Extract: YAML frontmatter fields (required vs optional), allowed-tools syntax, directory structure rules

### Claude Code Best Practices
- **Official Best Practices**: https://platform.claude.com/docs/skills/best-practices.md
  - Extract: Progressive disclosure, writing style, tool selection, anti-hallucination patterns
  - **Fallback**: If URL fails, use bundled `skills/create-skill/references/skill-anatomy.md`

## Example Sources

### Skills Repositories
- **skills.sh Ecosystem**: https://skills.sh
  - Public registry of community skills
  - Search for similar skills to understand patterns

- **Anthropic Official Skills**: https://github.com/anthropics/skills
  - Reference implementations from Anthropic
  - High-quality examples of skill structure

- **Anthropic skill-creator (actively fetched in Phase 2)**: https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
  - Anthropic's own reference implementation for skill creation
  - Extract: workflow phases, frontmatter patterns, anti-hallucination techniques

- **cc-arsenal Skills**: Local `skills/` directory
  - See the current listing for the live count, good source for tool usage and verification patterns

- **mgiovani/skills**: https://github.com/mgiovani/skills
  - Cross-platform skills following Agent Skills standard
  - Examples of model-invoked vs user-invoked patterns

## Fallback References

If WebFetch fails for any URL, use bundled fallback documentation:

- **Frontmatter Fields**: `skills/create-skill/references/frontmatter-fields.md`
  - Complete list of frontmatter fields, argument substitution, and the `context: fork` pattern

- **Skill Anatomy**: `skills/create-skill/references/skill-anatomy.md`
  - Folder conventions and composition patterns

## Fetch Strategy

**Phase 0 of create-skill should:**
1. WebFetch agentskills.io specification directly (no subagent, it's one small fetch)
2. WebFetch platform.claude.com best practices, falling back to bundled references above if it fails
3. Hold results in context for Phases 1-5
4. Never proceed without fresh specifications

**Why fetch every time:**
- Specifications evolve (new frontmatter fields, tool options)
- Best practices update with new patterns
- Cached docs lead to skills using deprecated features
- Fresh docs ensure compatibility with latest Claude Code versions
