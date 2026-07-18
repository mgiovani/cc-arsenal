# Authoring Rubric

The frozen rewrite rubric this repo's skills are held to. Apply it to every skill this workflow touches — read it in full before rewriting a `SKILL.md`.

## Description (frontmatter)

- Third person. State WHAT the skill does and WHEN to use it.
- Lead with the key use case, then natural trigger phrases a real user would actually type — not idealized machine queries.
- ≤1024 chars (the repo's validator cap; `quick_validate.py` enforces it).
- One `"Not for X (use <sibling>)"` clause per real overlap with an existing skill — read the sibling's actual description before writing the clause, never guess at what it covers. A single accurate disambiguation clause prevents more wrong triggers than three extra trigger phrases.

## Body

- **Under 500 lines.** Heavy detail — tables, long templates, option lists, full schema dumps — moves to `references/<topic>.md` with an inline link from the body and a one-line "load when..." condition, so the body stays skimmable and the detail loads only when actually needed.
- **Lean imperative.** "Run the validator." beats "You should run the validator, because..." Explain WHY only at a hard boundary — a point where an agent would otherwise plausibly do the wrong thing without the reasoning (e.g. "fetch live specs — cached docs go stale within weeks"). Everywhere else, a justification clause is noise, not guidance.
- **CAPS (MUST/NEVER/ALWAYS) reserved for true invariants** — the handful of things that are genuinely non-negotiable. A word repeated everywhere protects nothing; it just trains the reader to skim past it.
- **3-5 diverse worked examples**, and only where output format actually matters (a table shape, a report template, a specific command). Don't pad with an example that just restates the prose.
- **Anti-hallucination floor**: never instruct the skill to fabricate metrics, paths, or API names. Any number the skill reports in its own output must come from a command it actually ran this session — a validator's stdout, a grep count, an eval script's summary. This applies recursively: a skill that generates other skills or reports must carry this same floor into what it produces.
- **Portability**: the body itself must be tool-neutral — usable by any agent that can read files and run shell commands. Claude-Code-only mechanics (subagent/Task orchestration, parallel workflows, `AskUserQuestion`, plan-mode gates) are enhancements layered on top, each with an explicit sequential/inline fallback described in the body itself, not assumed. A reader on a tool with no subagent primitive should be able to follow the same workflow one step at a time and reach the same result, just slower.
- **Destructive/irreversible steps stop and ask first**, for any skill that mutates user state — installs, file edits beyond the skill's own declared scope, history rewrites, deploys, deletions. The user's original request is not itself the confirmation for the specific destructive action; a generic "improve this" or "clean this up" does not authorize a force-push or an unreviewed delete.

## Frontmatter keys

Only `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`, `disable-model-invocation`, `argument-hint`, `context`, `agent`, `hooks` are valid — anything else fails validation. List only tools the body actually uses in `allowed-tools`; an unused tool in the list is a stale claim about what the skill does.

## Generalize, don't overfit

A fix that only resolves the exact failing case you saw isn't a real fix — design for the pattern behind the failure, not the specific prompt. Ask: "would this instruction still hold if the user's request looked slightly different?" If a rewritten instruction only works because it happens to match one eval prompt's wording, it will misfire the next time the phrasing shifts. This applies as much to fixing a skill from eval feedback as it does to writing it the first time.
