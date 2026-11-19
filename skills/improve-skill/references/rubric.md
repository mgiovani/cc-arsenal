# Authoring Rubric

The frozen rewrite rubric this repo's skills are held to. Apply it to every skill this workflow touches: read it in full before rewriting a `SKILL.md`.

## Description (frontmatter)

- Third person. State WHAT the skill does and WHEN to use it.
- Lead with the key use case, then natural trigger phrases a real user would actually type, not idealized machine queries.
- ≤1024 chars (the repo's validator cap; `quick_validate.py` enforces it). `name` equals the directory name.
- One `"Not for X (use <sibling>)"` clause per real overlap with an existing skill: read the sibling's actual description before writing the clause, never guess at what it covers. A single accurate disambiguation clause prevents more wrong triggers than three extra trigger phrases.

## Body

- **Under 500 lines.** Heavy detail (tables, long templates, option lists, full schema dumps) moves to `references/<topic>.md` with an inline link from the body and a one-line "load when..." condition, so the body stays skimmable and the detail loads only when actually needed.
- **Lean imperative.** "Run the validator." beats "You should run the validator, because..." Explain WHY only at a hard boundary: a point where an agent would otherwise plausibly do the wrong thing without the reasoning (e.g. "fetch live specs, cached docs go stale within weeks"). Everywhere else, a justification clause is noise, not guidance.
- **No all-caps emphasis.** Where a rule matters, state the reason instead of writing it in capitals or bold `CRITICAL`/`IMPORTANT`: newer models over-trigger on emphasis, and a reason also tells the agent what to do in the case the rule did not foresee. `quick_validate.py` warns on it. To quote a keyword that is the skill's subject matter, put it in inline code or a fence: the validator skips both.
- **Cut what the model already knows.** For each line ask: would the agent get this wrong without it? Generic advice, definitions of common tools and restated best practice cost context and teach nothing.
- **Every workflow says how to verify its result**, with the real test, build or validator commands discovered from the repo. "Make sure it works" is not a check.
- **One default, not a menu.** Where several tools or approaches fit a step, name the one to use and give the escape hatch for the case it does not cover.
- **No time-sensitive facts** (model IDs, version numbers, prices, dates) unless the skill exists for them. A correction of a mistake agents keep making goes in a Gotchas section.
- **No contradictions** between `SKILL.md` and its references, templates or scripts: a reference command that breaks a body rule is a bug in the skill.
- **3-5 diverse worked examples**, and only where output format actually matters (a table shape, a report template, a specific command). Don't pad with an example that just restates the prose.
- **Anti-hallucination floor**: never instruct the skill to fabricate metrics, paths, or API names. Any number the skill reports in its own output must come from a command it actually ran this session: a validator's stdout, a grep count, an eval script's summary. This applies recursively: a skill that generates other skills or reports must carry this same floor into what it produces.
- **Portability**: the body itself must be tool-neutral: usable by any agent that can read files and run shell commands. Claude-Code-only mechanics (subagent/Task orchestration, parallel workflows, `AskUserQuestion`, plan-mode gates) are enhancements layered on top, each with an explicit sequential/inline fallback described in the body itself, not assumed. A reader on a tool with no subagent primitive should be able to follow the same workflow one step at a time and reach the same result, just slower.
- **Destructive/irreversible steps stop and ask first**, for any skill that mutates user state: installs, file edits beyond the skill's own declared scope, history rewrites, deploys, deletions. The user's original request is not itself the confirmation for the specific destructive action; a generic "improve this" or "clean this up" does not authorize a force-push or an unreviewed delete.

## Structure and flow

Mark one of these deficient only when the skill shows the problem: a step that fails or drifts when run, an ordering mistake, a long reference agents skim past. A working prose step that could have been a script is compliant; leave it alone.

- Reference contents and depth: a reference over 100 lines starts with a `## Contents` section of anchor links to its H2s. References sit one level deep from SKILL.md: link each directly, never reference-to-reference chains.
- Degrees of freedom: fragile, exact operations (byte-exact diffs, history rewrites, contrast math) become a script the skill runs; flexible judgment (what a Dockerfile or pipeline should achieve) is stated as goals and criteria, not a snippet to paste.
- Checklists and gates: an order-dependent flow gets a copyable fenced checklist of `- [ ]` steps with explicit gates ("if X fails, return to step N", "stop and report"). Replace the equivalent prose ordering rather than duplicating it.
- Validation loops: validate, fix, re-validate, with the exact command and a cap (e.g. 3 rounds, then report what still fails).
- Install lines: put the install command next to the first use of each external tool.
- Multi-model testing: run the skill on several models (e.g. a fast, a balanced and a strongest-reasoning tier: `haiku`, `sonnet`, `opus` in Claude Code); guidance that is enough for one may not be for another.

## Frontmatter keys

Only `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`, `disable-model-invocation`, `argument-hint`, `context`, `agent`, `hooks` are valid: anything else fails validation. Remove `allowed-tools`: in Claude Code it only pre-approves tools for the invoking turn, restricts nothing, and goes stale as the body changes.

## Generalize, don't overfit

A fix that only resolves the exact failing case you saw isn't a real fix: design for the pattern behind the failure, not the specific prompt. Ask: "would this instruction still hold if the user's request looked slightly different?" If a rewritten instruction only works because it happens to match one eval prompt's wording, it will misfire the next time the phrasing shifts. This applies as much to fixing a skill from eval feedback as it does to writing it the first time.
