---
name: create-skill
description: "Create a new agent skill (or Claude Code slash command) from a plain-language description, using live spec fetching, pattern research, and an approval-gated blueprint before any files are written. Use whenever the user wants to build, scaffold, or author a new skill, subagent capability, or slash command, including phrasings like 'make a command for X', 'create a slash command', 'turn this into a reusable skill', or 'package this workflow as a skill'. Not for editing CLAUDE.md/AGENTS.md memory rules (use create-rule) or discovering/installing existing third-party skills (use find-skills)."
metadata:
  author: mgiovani
  version: 3.0.0
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
  - WebFetch
  - AskUserQuestion
  - EnterPlanMode
  - ExitPlanMode
---

# Create Skill

Create new agent skills with specification-driven generation, live documentation fetching, and interactive planning.

## Writing Philosophy

Apply these when drafting the generated skill's description and body in Phase 4: they make the difference between a skill that works once vs. one that works reliably across varied inputs:

**Descriptions lead with use case.** Open with the concrete use case, then the trigger phrases a user would actually type: third person, WHAT the skill does + WHEN to use it. If a sibling skill covers adjacent territory, add one "Not for X (use <sibling>)" clause per real overlap: that single clause prevents more wrong triggers than three extra trigger phrases. Cap at 1024 chars (the bundled validator enforces it).

**Explain WHY only at hard boundaries.** Add reasoning only where an agent would otherwise plausibly do the wrong thing (e.g. "fetch live specs: cached docs go stale within weeks"). Everywhere else, a plain imperative ("Run the validator.") is faster to read and no less correct. Justifying every line is noise, not guidance.

**Keep it lean; reserve ALL-CAPS for true invariants.** Remove instructions that aren't pulling their weight: a 100-line skill often beats a 500-line skill diluted with edge cases that never occur. CRITICAL/MUST/ALWAYS/NEVER should mark the handful of things that really are non-negotiable; a word repeated ten times protects nothing.

**Generalize, don't overfit**: Skills designed only around their own test examples fail in practice. Design for the pattern, not the specific instance. Ask: "Would this instruction still apply if the user's request looked different?"

**Mine conversations first**: Users rarely articulate needs perfectly upfront. Extract information they've already provided before asking more questions.

**Refusal and precondition paths end at the question.** When the generated skill needs the user to resolve an ambiguity or confirm before a destructive step, its instruction should stop at asking: never "ask, then proceed anyway if there's no reply." A non-interactive eval run can't pause mid-task; a skill written to assume it can either hangs or silently guesses.

## Workflow

### Phase 0: Fetch Live Specifications

Fetch latest specs before every creation: never rely on memory or bundled docs, because specifications evolve. This is two small fetches, not a research task, call WebFetch directly rather than spawning agents for it:

1. WebFetch `https://agentskills.io/specification.md`: frontmatter fields, `allowed-tools` syntax, directory rules
2. WebFetch `https://platform.claude.com/docs/skills/best-practices.md`: progressive disclosure, writing style, anti-hallucination patterns. If the fetch fails, fall back to bundled `references/skill-anatomy.md` and `references/frontmatter-fields.md`

Hold both results in context. Do not proceed until both are fetched.

### Phase 1: Understand Requirements

**Step 1: Mine the conversation.** Read what the user already said and extract:
- What skill/command/workflow they want
- Examples of triggers they mentioned
- Tools, files, or outputs they described
- Who will use it (personal, team, organization)

Extract answers from conversation history before asking questions: don't ask what's already there.

**Step 2: Four key questions** (ask only what the conversation didn't already answer) using AskUserQuestion:

1. **What does this skill do?** Focus on the outcome. "Generates ADRs in the Nygard format from a decision description" beats "helps with documentation." The more specific, the better the description will be.

2. **When should it trigger?** Give 2-3 examples of exactly what a user would type to activate it. These become the description. Think about different phrasings the same intent might take.

3. **What does success look like?** Describe the output or end state specifically. "Creates a numbered file in docs/adr/ with YAML frontmatter and four required sections" is useful; "produces documentation" isn't.

4. **Is this worth measuring?** Would you want to compare this skill's output against a no-skill baseline to know it's actually helping? This matters most for model-invoked skills that trigger automatically on vague prompts.

Adapt communication style to the user. Technical users: use precise terms (frontmatter, YAML, subprocess). Non-technical users: explain concepts ("the skill's metadata tells agents when to activate it").

**Step 3: Interview for edge cases.** Before planning, clarify:
- What are 2-3 common ways this could go wrong?
- Are there input variations that need different handling?
- What should the skill explicitly NOT do (to set scope boundaries)?

### Phase 2: Research Existing Patterns & Composition

No `Task` tool here? Do this research yourself, sequentially: read the same targets each agent below would, one after the other. The two research tracks are what matters, not the parallel dispatch.

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
  2. WebFetch https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md — extract: workflow phases, frontmatter patterns, anti-hallucination techniques used in Anthropic's own skill-creator reference implementation
  3. Look for anti-hallucination and verification patterns
  Return: Best practices and common patterns with sources"
```

Consolidate into: pattern summary, composable skills list, decision rationale.

### Phase 3: Plan Skill Structure (User Approval Required)

Use EnterPlanMode to require explicit user approval before generating any files. If EnterPlanMode isn't available, present the same blueprint as plain text and wait for an explicit go-ahead: do not generate files on silence or an ambiguous reply.

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

Allowed frontmatter keys: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`, `disable-model-invocation`, `argument-hint`, `context`, `agent`, `hooks`. Reject anything else: unknown keys cause validation failures. Add `context: fork` + `agent: <type>` only when the skill should run isolated from conversation history (the SKILL.md content becomes the subagent's entire prompt). See `references/frontmatter-fields.md` for the full field reference and `$ARGUMENTS`/`$0`/`$1` substitution syntax.

If the new skill builds on an existing one, follow the **Skill composition** convention in `AGENTS.md`: name the sibling skill in prose and state its tool-neutral fallback in the same sentence (via the `Skill` tool where available, otherwise apply its documented steps), don't invent `uses:`/`composes:` frontmatter for it.

**2. Directory Structure**: explain why each directory is or isn't included:
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

Lead with what the skill does (outcome), not what it is. Structure instructions as imperative phases: "Fetch...", "Create...", "Validate...", not "You should fetch..." or "Claude will create..." Explain WHY only at hard boundaries (see Writing Philosophy above): not every step needs a justification clause.

Include verification checkpoints: what does success look like mid-workflow?

Anti-hallucination section: what should the skill explicitly verify before assuming?

**Writing `evals/evals.json`** (create if Q4 was "yes"), see `references/schemas.md` for the full schema:
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

Write prompts first: they're easy. Draft assertions while reasoning about what good output looks like for each prompt. Cover at minimum: a happy-path scenario, a judgment-call scenario (ambiguous input, no single correct output), and an edge case or refusal.

Eval-design rules that keep evals scoreable in a non-interactive run:
- A correct refusal must be able to score 100%: don't bundle a refusal assertion in the same eval as assertions that only make sense if the skill proceeded; a scenario that stops early can't satisfy both. Split guard behavior into its own scenario.
- Refusal/precondition scenarios must assert that **no mutating command ran** (no file writes, no `git commit`, no destructive Bash), otherwise a broken "helpful" auto-fix that ignores the guard passes anyway.
- Never assert on interactive mid-run input (a sandboxed eval runner can't pause). Instead assert the run's final message asks the right question and stops there.
- Bake any fixtures the prompt needs (sample file contents, a repo state) directly into the eval prompt text, so the scenario is self-contained and deterministic.

**Writing `evals/trigger-eval.json`** (create alongside evals.json for any model-invoked skill): a top-level JSON array (no wrapper object) of `{"query": "...", "should_trigger": true|false}` entries, roughly half realistic near-miss negatives pulled from sibling skills' territory (the cases a bad description would falsely trigger on):
```json
[
  {"query": "create a skill that generates changelog entries from commits", "should_trigger": true},
  {"query": "add a rule to CLAUDE.md about commit message style", "should_trigger": false}
]
```

**Self-check before finalizing:**
- [ ] No broken internal file references (every referenced file exists)
- [ ] SKILL.md under 500 lines (move details to `references/` if needed)
- [ ] Description is assertive, covers multiple trigger phrasings, 50-1024 chars, has a sibling disambiguation clause if one applies
- [ ] All tools in `allowed-tools` are actually used in the workflow
- [ ] No allowed-tools with unknown keys
- [ ] No TODO or placeholder text remains in generated files
- [ ] If the skill is model-invoked, `evals/evals.json` and `evals/trigger-eval.json` were authored, not skipped

### Phase 5: Validate and Package

Run the bundled validator to catch common errors: it catches frontmatter key typos that silently break skill loading, descriptions that are too short or too long, and broken internal references:

```bash
uv run skills/create-skill/scripts/quick_validate.py [SKILL_PATH]
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
uv run skills/create-skill/scripts/package_skill.py [SKILL_PATH]
```

**Next steps:**
1. Test on a real use case: creation is just the beginning
2. Improve based on real usage (see improvement philosophy below)
3. Publish to skills.sh or share with team

## Improvement Philosophy

When iterating on an existing skill after seeing it in use:

**Read transcripts, not just outputs.** Find where the skill caused unproductive patterns. Did it ask for information the user already gave? Did it produce outputs that needed heavy editing? Did it trigger when it shouldn't have?

**Generalize solutions.** If a fix only works for the specific failure case you saw, it's not a real fix. Generalize to the class of problem. If the skill failed because it asked "what language?" when the repo obviously uses Python, the fix is "mine context before asking questions", not just adding a Python-specific check.

**Stay lean.** Resist adding instructions for every edge case. More instructions can make skills worse by diluting the important parts. Ask: "If I removed this instruction, would the skill get meaningfully worse?"

**Bundle repeated code.** If the skill has Claude rewriting the same logic from scratch each invocation, put it in `scripts/`. Scripts are token-efficient and deterministic.

**Iterate until:** user is satisfied, feedback is empty, or there's no more measurable improvement.

## Anti-Hallucination Guidelines

- Never reference files or functions that don't exist: verify with Glob/Grep first
- Never guess at URL structure: only fetch from canonical sources in `references/specification-urls.md`
- Read existing code before suggesting modifications
- Confirm all internal skill references resolve before writing them
- Only include tools in `allowed-tools` that you've verified exist in the platform spec
- Never write a percentage, count, or score into a generated skill or report unless it came from a command actually run this session (validator stdout, eval script output, a grep count): a fabricated number in a generated skill teaches the same fabrication pattern forward into every skill it produces

## Reference Documentation

- **`references/skill-anatomy.md`**: Deep dive: folder conventions, progressive disclosure, composition patterns
- **`references/frontmatter-fields.md`**: Full frontmatter field reference, `$ARGUMENTS` substitution syntax, the `context: fork` isolated-subagent pattern
- **`references/specification-urls.md`**: Canonical URLs for specs, best practices, examples
- **`references/schemas.md`**: JSON schemas for evals.json, trigger-eval.json, grading.json, metrics.json

---

## Claude Code Enhanced Features

This section extends the base skill with Claude Code-specific capabilities: parallel subagent research, plan mode approval gates, eval system with blind comparison, and description optimization.

### Phase 6: Run Evals (Optional, Recommended for Model-Invoked Skills)

Run this phase when:
- User answered "yes" to eval-worthiness in Phase 1 Q4
- `evals/evals.json` was created in Phase 4
- The skill is model-invoked (auto-triggers matter, bad descriptions cause wrong triggers)

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
uv run skills/create-skill/scripts/run_eval.py [SKILL_PATH]
uv run skills/create-skill/scripts/generate_report.py [SKILL_PATH]
```

**Improvement loop**: if score < 4/5 or assertions fail:
1. Read the full transcripts (not just outputs): find where the skill caused unproductive patterns
2. Identify the specific failure mode
3. Generalize the fix (don't just patch the failing test case, fix the class of problem)
4. Update SKILL.md or the skill description
5. Re-run evals: repeat until score improves or no further progress

### Phase 7: Optimize Description & Package (Optional)

For model-invoked skills, the description is the trigger mechanism. Optimizing it improves precision.

Use the description optimizer: it generates should/should-not-trigger queries, iterates the description against a train split via `claude -p`, then validates on a held-out test split to avoid overfitting (see the script's own docstring for the full algorithm):
```bash
uv run skills/create-skill/scripts/improve_description.py [SKILL_PATH]
```

Then package for distribution:
```bash
uv run skills/create-skill/scripts/package_skill.py [SKILL_PATH]
```

## Eval Reference Files

- `references/eval-system.md`: How the eval system works, when to use it, platform-specific notes
- `references/agent-prompts.md`: Exact prompts for grader and comparator agents
