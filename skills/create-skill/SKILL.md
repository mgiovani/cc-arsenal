---
name: create-skill
description: "Create new agent skills with specification-driven generation, live documentation fetching, and interactive planning. Use this skill whenever the user wants to create a new skill, slash command, or agent capability — even if they say 'make a command' or 'turn this into a reusable workflow'."
metadata:
  author: mgiovani
  version: 2.0.0
argument-hint: "[skill-description]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(mkdir *)
  - Bash(python *)
  - Bash(uv run *)
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - WebFetch
  - AskUserQuestion
  - EnterPlanMode
  - ExitPlanMode
---

# Create Skill

Create new agent skills with specification-driven generation, live documentation fetching, and interactive planning.

## Writing Philosophy

Before starting, internalize these principles — they make the difference between a skill that works once vs. one that works reliably across varied inputs:

**Explain the why**: Replace heavy-handed "MUSTs" with reasoning. LLMs respond better to understanding why a constraint exists than to being commanded. "Fetch live specs because specifications evolve weekly" beats "ALWAYS fetch live specs."

**Pushy descriptions**: Combat undertriggering by making descriptions assertive. "Use this whenever someone says 'create a workflow', 'make a command', or 'turn this into a skill'" beats "Use for skill creation." Model-invoked skills that don't trigger aren't useful.

**Keep it lean**: Remove instructions that aren't pulling their weight. Every line competes for attention in the context window. A 100-line skill often beats a 500-line skill if the extra 400 lines are noise, redundancy, or edge cases that never occur.

**Generalize, don't overfit**: Skills designed only around their own test examples fail in practice. Design for the pattern, not the specific instance. Ask: "Would this instruction still apply if the user's request looked different?"

**Mine conversations first**: Users rarely articulate needs perfectly upfront. Extract information they've already provided before asking more questions.

## Workflow

### Phase 0: Fetch Live Specifications

Fetch latest specs before every creation — never rely on memory or bundled docs, because specifications evolve.

Spawn 2 parallel Explore agents (model: haiku to minimize cost):

```
Agent 1 - Fetch Skill Specifications:
- subagent_type: "Explore"
- model: "haiku"
- prompt: "Fetch and summarize the latest skill specifications:
  1. WebFetch https://agentskills.io/what-are-skills.md — extract: what skills are, anatomy, when to use
  2. WebFetch https://agentskills.io/specification.md — extract: frontmatter fields, allowed-tools syntax, directory rules
  Return: Structured summary with examples"

Agent 2 - Fetch Best Practices:
- subagent_type: "Explore"
- model: "haiku"
- prompt: "Fetch Claude Code skill best practices:
  1. WebFetch https://platform.claude.com/docs/skills/best-practices.md — extract: progressive disclosure, writing style, anti-hallucination patterns
  2. If URL fails, read bundled: skills/create-skill/references/skill-anatomy.md
  Return: Key guidelines and common pitfalls"
```

Hold results in context. Do not proceed until both agents return.

### Phase 1: Understand Requirements

**Step 1: Mine the conversation.** Read what the user already said and extract:
- What skill/command/workflow they want
- Examples of triggers they mentioned
- Tools, files, or outputs they described
- Who will use it (personal, team, organization)

Extract answers from conversation history before asking questions — don't ask what's already there.

**Step 2: Four key questions** (ask only what the conversation didn't already answer) using AskUserQuestion:

1. **What does this skill do?** — Focus on the outcome. "Generates ADRs in the Nygard format from a decision description" beats "helps with documentation." The more specific, the better the description will be.

2. **When should it trigger?** — Give 2-3 examples of exactly what a user would type to activate it. These become the description. Think about different phrasings the same intent might take.

3. **What does success look like?** — Describe the output or end state specifically. "Creates a numbered file in docs/adr/ with YAML frontmatter and four required sections" is useful; "produces documentation" isn't.

4. **Is this worth measuring?** — Would you want to compare this skill's output against a no-skill baseline to know it's actually helping? This matters most for model-invoked skills that trigger automatically on vague prompts.

Adapt communication style to the user. Technical users: use precise terms (frontmatter, YAML, subprocess). Non-technical users: explain concepts ("the skill's metadata tells agents when to activate it").

**Step 3: Interview for edge cases.** Before planning, clarify:
- What are 2-3 common ways this could go wrong?
- Are there input variations that need different handling?
- What should the skill explicitly NOT do (to set scope boundaries)?

### Phase 2: Research Existing Patterns & Composition

Spawn 2 parallel Explore agents (model: haiku) using the Task tool:

```
Agent 1 - Internal Pattern Analysis:
- subagent_type: "Explore"
- model: "haiku"
- prompt: "Search skills/ directory for skills similar to [SKILL_PURPOSE].
  Extract:
  1. Similar skill patterns: frontmatter structure, phase organization, tool usage
  2. Composable skills: existing skills this new skill could reference or invoke
     Example: A deploy skill could invoke git-commit; a testing skill could invoke fix-bug
  3. scripts/ usage patterns: when scripts are included vs not
  Return: Patterns summary with file paths + composable skills list"

Agent 2 - External Example Research:
- subagent_type: "Explore"
- model: "haiku"
- prompt: "Research external skill examples:
  1. WebFetch https://skills.sh — search for skills similar to [SKILL_PURPOSE]
  2. Look for anti-hallucination and verification patterns
  Return: Best practices and common patterns with sources"
```

Consolidate into: pattern summary, composable skills list, decision rationale.

### Phase 3: Plan Skill Structure (User Approval Required)

Use EnterPlanMode to require explicit user approval before generating any files.

Present a complete blueprint:

**1. Frontmatter Design:**
```yaml
name: skill-name          # kebab-case, ≤64 chars, no leading/trailing/consecutive hyphens
description: "..."        # assertive, covers multiple trigger phrasings, 50-1024 chars
[disable-model-invocation: true]   # add only for explicit /slash-command-only skills
[argument-hint: "[hint]"]          # add if skill accepts a positional argument
allowed-tools:            # only list tools actually used — each has a cost
  - Read                  # explain why each is here
  - Write
```

Allowed frontmatter keys: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`, `disable-model-invocation`, `argument-hint`. Reject anything else — unknown keys cause validation failures.

**2. Directory Structure** — explain why each directory is or isn't included:
```
skill-name/
├── SKILL.md (required)
├── scripts/      ← include if: code would be rewritten identically on every invocation
├── references/   ← include if: reference docs would push SKILL.md past 500 lines
└── assets/       ← include if: output templates or static files are needed
```

**3. Workflow Outline**: 2-6 phases covering the full task from start to verified completion.

**4. Test Case Plan** (if user said "yes" to Q4):
- 2-3 trigger prompts that should activate the skill
- Expected output for each prompt
- These will become `evals/evals.json` entries

**5. Composition Plan**: List existing skills to invoke and why, vs. reimplementing.

Use ExitPlanMode to submit for user approval. Do NOT generate any files before ExitPlanMode returns.

### Phase 4: Generate Skill Files

Create files only after approval from Phase 3.

**Writing SKILL.md:**

Lead with what the skill does (outcome), not what it is. Structure instructions as imperative phases: "Fetch...", "Create...", "Validate..." — not "You should fetch..." or "Claude will create..."

Each phase should explain WHY the step matters:
- BAD: "Run the validator."
- GOOD: "Run the validator — it catches frontmatter key typos that silently break skill loading."

Include verification checkpoints: what does success look like mid-workflow?

Anti-hallucination section — what should the skill explicitly verify before assuming?

**Writing evals/evals.json** (create if Q4 was "yes"):
```json
{
  "skill": "skill-name",
  "description": "What this skill does in one sentence",
  "evals": [
    {
      "id": "eval-1",
      "prompt": "Exact trigger phrase a user would type",
      "assertions": [
        "Output contains expected content or structure",
        "Files created at expected paths",
        "No placeholder text in output"
      ]
    }
  ]
}
```

Write prompts first — they're easy. Draft assertions while reasoning about what good output looks like for each prompt.

**Self-check before finalizing:**
- [ ] No broken internal file references (every referenced file exists)
- [ ] SKILL.md under 500 lines (move details to `references/` if needed)
- [ ] Description is assertive, covers multiple trigger phrasings, 50-1024 chars
- [ ] All tools in `allowed-tools` are actually used in the workflow
- [ ] No allowed-tools with unknown keys
- [ ] No TODO or placeholder text remains in generated files

### Phase 5: Validate and Package

Run the bundled validator to catch common errors — it catches frontmatter key typos that silently break skill loading, descriptions that are too short or too long, and broken internal references:

```bash
uv run python skills/create-skill/scripts/quick_validate.py [SKILL_PATH]
```

The validator checks:
- Name format (kebab-case, ≤64 chars, no invalid hyphens)
- Description length (50-1024 chars, no angle brackets)
- Allowed frontmatter keys only (no unknown fields)
- SKILL.md line count (warns if >500)
- Directory structure (only `scripts/`, `references/`, `assets/` subdirs)
- Internal reference integrity (referenced files exist)
- `evals/evals.json` schema (if present)

Fix all issues before proceeding.

Optionally, package for distribution:
```bash
uv run python skills/create-skill/scripts/package_skill.py [SKILL_PATH]
```

**Next steps:**
1. Test on a real use case — creation is just the beginning
2. Improve based on real usage (see improvement philosophy below)
3. Publish to skills.sh or share with team

## Improvement Philosophy

When iterating on an existing skill after seeing it in use:

**Read transcripts, not just outputs.** Find where the skill caused unproductive patterns. Did it ask for information the user already gave? Did it produce outputs that needed heavy editing? Did it trigger when it shouldn't have?

**Generalize solutions.** If a fix only works for the specific failure case you saw, it's not a real fix. Generalize to the class of problem. If the skill failed because it asked "what language?" when the repo obviously uses Python, the fix is "mine context before asking questions" — not just adding a Python-specific check.

**Stay lean.** Resist adding instructions for every edge case. More instructions can make skills worse by diluting the important parts. Ask: "If I removed this instruction, would the skill get meaningfully worse?"

**Bundle repeated code.** If the skill has Claude rewriting the same logic from scratch each invocation, put it in `scripts/`. Scripts are token-efficient and deterministic.

**Iterate until:** user is satisfied, feedback is empty, or there's no more measurable improvement.

## Anti-Hallucination Guidelines

- Never reference files or functions that don't exist — verify with Glob/Grep first
- Never guess at URL structure — only fetch from canonical sources in `references/specification-urls.md`
- Read existing code before suggesting modifications
- Confirm all internal skill references resolve before writing them
- Only include tools in `allowed-tools` that you've verified exist in the platform spec

## Reference Documentation

- **`references/skill-anatomy.md`** — Deep dive: folder conventions, progressive disclosure, composition patterns
- **`references/specification-urls.md`** — Canonical URLs for specs, best practices, examples
- **`references/schemas.md`** — JSON schemas for evals.json, grading.json, metrics.json

---

## Claude Code Enhanced Features

This section extends the base skill with Claude Code-specific capabilities: parallel subagent research, plan mode approval gates, eval system with blind comparison, and description optimization.

### Phase 6: Run Evals (Optional — Recommended for Model-Invoked Skills)

Run this phase when:
- User answered "yes" to eval-worthiness in Phase 1 Q4
- `evals/evals.json` was created in Phase 4
- The skill is model-invoked (auto-triggers matter — bad descriptions cause wrong triggers)

**Why this matters**: Model-invoked skills fire automatically based on their description. A bad description means the skill either fires when it shouldn't (annoying false positives) or misses when it should (silent failures). Evals measure this objectively.

For each eval in `evals/evals.json`, spawn parallel agents then a grader:

```
For each eval_id in evals/evals.json:

  Agent A - With-Skill Run (model: haiku):
  - subagent_type: "general-purpose"
  - model: "haiku"
  - prompt: "Run this exact prompt with the skill active: '[EVAL_PROMPT]'
    Document the complete output.
    Check each assertion: [ASSERTIONS]
    Return: full output + assertion verdicts (pass/fail)"

  Agent B - Baseline Run (model: haiku):
  - subagent_type: "general-purpose"
  - model: "haiku"
  - prompt: "Run this exact prompt WITHOUT any skill active: '[EVAL_PROMPT]'
    Document the complete output.
    Return: full output"

  Grader (after A and B complete, model: sonnet):
  - subagent_type: "general-purpose"
  - model: "sonnet"
  - prompt: [See references/agent-prompts.md for exact grader prompt]
```

Alternatively, use the bundled eval runner scripts:
```bash
uv run python skills/create-skill/scripts/run_eval.py [SKILL_PATH]
uv run python skills/create-skill/scripts/generate_report.py [SKILL_PATH]
```

**Improvement loop** — if score < 4/5 or assertions fail:
1. Read the full transcripts (not just outputs) — find where the skill caused unproductive patterns
2. Identify the specific failure mode
3. Generalize the fix (don't just patch the failing test case — fix the class of problem)
4. Update SKILL.md or the skill description
5. Re-run evals — repeat until score improves or no further progress

### Phase 7: Optimize Description & Package (Optional)

For model-invoked skills, the description is the trigger mechanism. Optimizing it improves precision.

Use the description optimizer:
```bash
uv run python skills/create-skill/scripts/improve_description.py [SKILL_PATH]
```

This script:
1. Generates 20 trigger queries (10 should-trigger, 10 should-not-trigger)
2. Splits 60/40 into train/test sets (stratified by trigger intent)
3. Tests the current description against train set via `claude -p`
4. Iterates up to 5 times, improving based on failures
5. Validates best iteration on test set to prevent overfitting
6. Auto-shortens if description exceeds 1024 chars (then re-validates)

Then package for distribution:
```bash
uv run python skills/create-skill/scripts/package_skill.py [SKILL_PATH]
```

## Eval Reference Files

- `references/eval-system.md` — How the eval system works, when to use it, platform-specific notes
- `references/agent-prompts.md` — Exact prompts for grader and comparator agents
