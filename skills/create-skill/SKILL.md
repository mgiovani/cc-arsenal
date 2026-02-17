---
name: create-skill
description: "Create new agent skills with specification-driven generation, live documentation
  fetching, and multi-source example research. This skill should be used when users
  want to create a new skill, slash command, or agent capability for Claude Code."
metadata:
  author: mgiovani
  version: 1.0.0
argument-hint: "[skill-description]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(mkdir *), Bash(python *), Bash(uv
  run *), Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion,
  EnterPlanMode, ExitPlanMode
---

# Create Skill

Create new agent skills with specification-driven generation, live documentation fetching, and interactive planning.

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks—they transform Claude from a general-purpose agent into a specialized agent equipped with procedural knowledge.

### What This Skill Does Differently

Unlike legacy skill creation tools, this skill:
- **Fetches live specifications** from canonical URLs every run (no stale docs)
- **Researches multi-source examples** (skills.sh, anthropics/skills, mgiovani/skills, cc-arsenal)
- **Uses interactive clarification** to understand your vision
- **Requires user approval** via EnterPlanMode before generating any files
- **Model-invocable** so agents can auto-invoke during larger workflows
- **Task Management System** for transparent progress tracking
- **Validates** generated skills against the official specification

## Skill Creation Workflow

Follow these 6 phases in order. Each phase builds on the previous one.

### Phase 0: Fetch Live Specifications

**CRITICAL**: Always start by fetching the latest official documentation. Never rely on cached or bundled specifications.

Spawn 2 parallel Explore agents (model: haiku) using the Task tool:

```
Agent 1 - Fetch Skill Specifications:
- prompt: "Fetch and summarize the latest skill specifications:
  1. WebFetch https://agentskills.io/what-are-skills.md - Extract: what skills are, when to use them, anatomy overview
  2. WebFetch https://agentskills.io/specification.md - Extract: YAML frontmatter fields (required vs optional), allowed-tools syntax, directory structure rules
  Return: Structured summary with examples"
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - Fetch Best Practices:
- prompt: "Fetch Claude Code skill best practices:
  1. WebFetch https://platform.claude.com/docs/skills/best-practices.md - Extract: progressive disclosure, writing style, tool selection, anti-hallucination patterns
  2. If URL fails, read bundled fallback: skills/create-skill/references/skill-anatomy.md
  Return: Key guidelines and common pitfalls"
- subagent_type: "Explore"
- model: "haiku"
```

**Hold results in context** for all subsequent phases. Do not proceed until both agents return.

### Phase 1: Understand Skill Requirements

Use **AskUserQuestion** for interactive clarification. Conduct 2 rounds of questions:

**Round 1 - Core Identity:**
```
Questions:
1. What does this skill do? (Focus on the outcome, not implementation)
   Options: "Automates a workflow", "Provides domain expertise", "Integrates with a tool/API", "Generates code/files"

2. Provide 2-3 concrete usage examples (what would a user say to trigger this skill?)
   Free-text field

3. Should this skill be user-invoked (explicit /command) or model-invoked (auto-activates)?
   Options: "User-invoked (/slash command only)", "Model-invoked (auto-detect and activate)"
```

**Round 2 - Technical Details:**
```
Questions:
1. Will this skill create or modify files?
   Options: "Yes - creates new files", "Yes - edits existing files", "Yes - both", "No - read-only"

2. Does this skill need external tools? (Select all that apply)
   Options: "Git operations", "Package managers (npm/pip/uv)", "Web fetching", "Subagents/Task tool", "None"

3. What tech stack or domain does this skill target? (e.g., "Python testing", "Next.js", "Documentation")
   Free-text field

4. Where should this skill be installed?
   Options: "Project skill (.claude/skills/) - shared with team", "User skill (~/.claude/skills/) - personal only"
```

**Synthesize** responses into a structured requirements document:
- Purpose statement (2-3 sentences)
- Usage scenarios (list of 3-5 examples)
- Technical requirements (tools, file operations, target domain)
- Invocation mode (user vs model)
- Installation location

### Phase 2: Research Existing Patterns & Composition

Spawn 2 parallel Explore agents (model: haiku) using the Task tool:

```
Agent 1 - Internal Pattern Analysis & Composition Discovery:
- prompt: "Search skills/ directory for skills similar to [SKILL_PURPOSE].

  Extract:
  1. Similar skill patterns: frontmatter structure, phase organization, tool usage
  2. **Composable skills**: Identify existing skills this new skill could reference or invoke
     Example: A deploy skill could invoke git-commit; a testing skill could invoke fix-bug
  3. Bundled resource patterns: When skills use scripts/, references/, assets/

  Return:
  - Patterns summary with file paths
  - List of composable skills with descriptions of how they could be used"
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - External Example Research:
- prompt: "Research external skill examples:
  1. WebFetch https://skills.sh - Search for skills similar to [SKILL_PURPOSE]
  2. Grep skills/skill-creator/references/ for relevant patterns
  3. Look for anti-hallucination and verification patterns

  Return: Best practices and common patterns with sources"
- subagent_type: "Explore"
- model: "haiku"
```

**Consolidate results** into:
- Pattern summary (frontmatter conventions, tool usage, verification checks)
- **Composable skills list** (which existing skills to reference/invoke and why)
- Decision rationale (which patterns apply to this skill)

### Phase 3: Plan Skill Structure (User Approval Required)

**CRITICAL**: Use EnterPlanMode to request explicit user approval before generating any files.

Present a complete blueprint:

**1. Frontmatter Design:**
```yaml
name: skill-name
description: "Clear, specific description following spec"
metadata:
  author: [USER_OR_ORG]
  version: 1.0.0
[argument-hint: if applicable]
[disable-model-invocation: true if user-invoked]
allowed-tools: [List with rationale]
```

**2. Directory Structure:**
```
skill-name/
├── SKILL.md (required)
├── scripts/ (include if: [RATIONALE])
├── references/ (include if: [RATIONALE])
└── assets/ (include if: [RATIONALE])
```

Explain **why** each directory is or isn't needed:
- **scripts/**: For executable code that would be repeatedly rewritten
- **references/**: For documentation that keeps SKILL.md lean and loads on-demand
- **assets/**: For output files (templates, images, boilerplate)

**3. SKILL.md Outline:**
- Introduction (what the skill does)
- Workflow phases (2-6 phases typical)
- Anti-hallucination guidelines
- Verification steps
- Examples

**4. Skill Composition Plan:**
If relevant, list existing skills this skill will reference or invoke:
- Skill name and purpose
- How it will be used (direct invocation, reference in instructions, etc.)
- Benefits of composition vs reimplementation

**5. Design Decisions:**
- Tool selection rationale
- Model-invoked vs user-invoked choice
- Verification strategy
- Trade-offs considered

**Exit Plan Mode**: Use ExitPlanMode to submit the plan for user approval. Do NOT proceed to Phase 4 until the user explicitly approves the plan.

### Phase 4: Generate Skill Files

**ONLY execute after user approval in Phase 3.**

Create the skill following the approved blueprint:

**Step 1: Create Directory Structure**
```bash
mkdir -p [SKILL_PATH]
mkdir -p [SKILL_PATH]/scripts  # if needed
mkdir -p [SKILL_PATH]/references  # if needed
mkdir -p [SKILL_PATH]/assets  # if needed
```

**Step 2: Write SKILL.md**

Follow this template structure:

```markdown
---
[Approved frontmatter from Phase 3]
---

# [Skill Name]

[Clear description of what the skill does]

## Your Task

[Main workflow organized into phases]

### Phase 1: [Phase Name]

[Clear instructions for this phase]

### Phase 2: [Phase Name]

[Clear instructions for this phase]

[Continue for all phases...]

## Anti-Hallucination Guidelines

- Never reference files or functions that don't exist
- Verify all file paths before creating/editing
- Use Glob/Grep to confirm assumptions
- Read existing code before suggesting modifications

## Verification Steps

[Specific checks to ensure the skill completed successfully]

## Examples

[2-3 concrete usage examples]
```

**Step 3: Generate Supporting Files**

If the plan includes scripts/, references/, or assets/:
- Create placeholder or template files
- Add comments explaining what each file should contain
- Reference them in SKILL.md with clear usage instructions

**Step 4: Self-Check**

Before marking complete, verify:
- [ ] All referenced files exist (no broken paths)
- [ ] SKILL.md < 500 lines (move details to references/ if needed)
- [ ] Frontmatter has required fields (name, description)
- [ ] No TODO or placeholder text in final skill
- [ ] All tools used in workflow are listed in allowed-tools

### Phase 5: Validate and Report

Run validation checks using the bundled validator:

```bash
uv run python skills/create-skill/scripts/quick_validate.py [SKILL_PATH]
```

**Validation checks**:
- YAML frontmatter structure and required fields
- Skill naming conventions (kebab-case)
- Description completeness (>50 chars)
- Directory structure compliance
- No broken internal references

**Report results**:
- ✅ All checks passed
- ❌ Issues found (with specific error messages)

**Next steps**:
1. Test the skill on a real use case
2. Iterate based on usage (see references/skill-anatomy.md)
3. Share with team or publish to skills.sh
4. Consider creating a plugin variant in .claude-plugin/marketplace.json

## Anti-Hallucination Guidelines

- **Never guess URLs**: Fetch from the canonical sources listed in references/specification-urls.md
- **Verify examples exist**: Use Grep to confirm patterns before recommending them
- **Read before referencing**: Don't reference bundled files (references/, scripts/) without reading them first
- **Validate file paths**: Use Glob to confirm directories before mkdir or Write operations
- **Check tool availability**: Don't add tools to allowed-tools that don't exist in the spec

## Common Pitfalls to Avoid

1. **Skipping Phase 0**: Always fetch live specs, even if you "know" the format
2. **No user approval**: Never generate files before ExitPlanMode approval
3. **Monolithic SKILL.md**: Use references/ to keep core instructions under 500 lines
4. **Missing verification**: Always include specific checks users can run to validate success
5. **Vague descriptions**: Be specific about what triggers the skill (bad: "helps with tasks", good: "generates ADRs following the Michael Nygard template")
6. **Over-tooling**: Only request tools actually used in the workflow
7. **Ignoring composition**: Don't reimplement functionality that existing skills already provide well

## Reference Documentation

For detailed information, see bundled references:
- **specification-urls.md**: Canonical URLs for specs, best practices, and examples
- **skill-anatomy.md**: Deep dive into folder conventions, progressive disclosure, and composition patterns

## Examples

**Example 1: User wants a code review skill**
```
User: "Create a skill that reviews Python code for PEP 8 compliance"

Phase 1 clarification reveals:
- Purpose: Lint Python files and suggest fixes
- User-invoked (/code-review)
- Uses Bash (ruff, flake8), Read, Edit

Phase 2 research finds:
- Similar: fix-bug (verification patterns), review-security (multi-file scanning)
- Can compose with fix-bug for auto-fixing violations

Phase 3 plan:
- scripts/run_ruff.py for deterministic linting
- No references/ needed (PEP 8 is well-known)
- allowed-tools: Bash(ruff *), Bash(flake8 *), Read, Edit, Grep, Glob
```

**Example 2: Agent wants to create a deployment skill during implementation**
```
Agent context: "While implementing the feature, I need a skill to deploy to production"

Phase 1 (auto-inferred):
- Purpose: Deploy application to production environment
- Model-invoked (auto-activates when agent says "deploy")
- Uses Bash (git), Task (subagents for testing), WebFetch (deployment APIs)

Phase 2 research finds:
- Similar: git-create-pr (git workflow patterns), implement-feature (Task tool usage)
- Can compose with git-commit for creating deployment commits

Phase 3 plan:
- references/deployment-checklist.md (pre-deploy verification steps)
- scripts/deploy.sh (deterministic deployment script)
- Model-invoked (no disable-model-invocation)
- allowed-tools: Bash(git *), Bash(./scripts/deploy.sh), Task, WebFetch, Read
```

**Example 3: Team needs a documentation skill**
```
User: "We need a skill to generate API documentation from OpenAPI specs"

Phase 1 clarification reveals:
- Purpose: Parse OpenAPI YAML and generate markdown docs
- User-invoked (/docs-api)
- Uses Read, Write, Bash (swagger-cli)

Phase 2 research finds:
- Similar: docs-diagram (Mermaid generation), docs-init (doc structure)
- Can compose with docs-diagram for adding visualizations to API docs

Phase 3 plan:
- scripts/parse_openapi.py (deterministic parsing logic)
- assets/api-template.md (documentation template)
- references/openapi-spec.md (schema reference for on-demand loading)
- allowed-tools: Read, Write, Bash(swagger-cli *), Bash(python scripts/parse_openapi.py)
```
