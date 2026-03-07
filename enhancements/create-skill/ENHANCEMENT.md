---
# Enhancement for: create-skill
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

## Claude Code Enhanced Features

This enhancement adds Claude Code-specific capabilities: parallel subagent research, plan mode approval gates, eval system with blind comparison, and description optimization.

### Phase 0 Enhancement: Parallel Spec Fetching

Instead of sequential WebFetch calls, spawn 2 parallel Explore agents (use model: haiku to minimize cost):

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

### Phase 2 Enhancement: Parallel Pattern Research

Instead of sequential search, spawn 2 parallel Explore agents:

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

### Phase 3 Enhancement: Plan Mode Approval Gate

Use EnterPlanMode / ExitPlanMode to require explicit user approval before generating any files.

```
EnterPlanMode → Present complete blueprint → ExitPlanMode
```

Do NOT generate any files before ExitPlanMode returns. The plan mode gate is the last checkpoint before irreversible file creation.

### Phase 6: Run Evals (Optional — Recommended for Model-Invoked Skills)

Run this phase when:
- User answered "yes" to eval-worthiness in Phase 1 Q4
- `evals/evals.json` was created in Phase 4
- The skill is model-invoked (auto-triggers matter — bad descriptions cause wrong triggers)

**Why this matters**: Model-invoked skills fire automatically based on their description. A bad description means the skill either fires when it shouldn't (annoying false positives) or misses when it should (silent failures). Evals measure this objectively.

For each eval in `evals/evals.json`, spawn parallel agents then a grader:

```
For each eval_id in evals/evals.json:

  Agent A - With-Skill Run:
  - subagent_type: "general-purpose"
  - model: "haiku"
  - prompt: "Run this exact prompt: '[EVAL_PROMPT]'
    The create-skill skill should be active.
    Document the complete output.
    Check each assertion: [ASSERTIONS]
    Return: full output + assertion verdicts (pass/fail)"

  Agent B - Baseline Run:
  - subagent_type: "general-purpose"
  - model: "haiku"
  - prompt: "Run this exact prompt WITHOUT any skill active: '[EVAL_PROMPT]'
    Document the complete output.
    Return: full output"

  Then Grader (after A and B complete):
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

## Reference Files

- `references/eval-system.md` — How the eval system works, when to use it, platform-specific notes
- `references/agent-prompts.md` — Exact prompts for grader and comparator agents
