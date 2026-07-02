---
# Enhancement for: review-code
description: Runs a comprehensive multi-agent code review of a PR, commit, or the whole
  codebase across six dimensions (correctness, performance, code style, test coverage,
  error handling, and simplicity/over-engineering) and returns a severity-ranked report
  with file:line findings and fix suggestions. Use when the user wants a thorough code
  review, asks to review a PR or diff, or wants over-engineered code flagged for
  simplification. Analysis only, identifying issues without modifying code, committing,
  or running tests. Not for a security-focused audit (use review-security) or a
  visual/UX design critique (use review-design).
---

## Simplicity & Over-Engineering Lens (Claude Code enhancement)

LLM-written code tends to over-engineer: interfaces built for one implementation, factories for one product, wrapper layers that just forward a call. None of that shows up as a bug, so the five specialists in Phase 3 don't catch it — it needs its own lens. This module adds a 6th parallel specialist and a matching report dimension.

### Agent 6: Simplicity & Over-Engineering

Spawn this agent alongside Agents 1-5 in Phase 3, in the same parallel batch:

```
Agent 6 - Simplicity & Over-Engineering (Explore, Haiku):
  prompt: "Review [SCOPE] for unnecessary complexity — code that does more than the
    current, concrete requirement needs.

    1. Grep for interfaces/abstract classes/protocols with exactly one concrete
       implementation, factories that construct exactly one product, wrapper
       functions or classes that only forward calls without adding behavior, and
       configuration flags or parameters that no caller ever varies.
    2. Read each match plus surrounding context to confirm it's genuinely
       unnecessary, not a documented extension point for a real second caller or
       plugin contract.
    3. Before flagging something as speculative, check whether equivalent behavior
       already exists — in this codebase (search first), the standard library, or
       the framework/platform in use.
    4. Classify each confirmed finding with exactly one tag:
       - [delete] — dead/unused code with no live caller
       - [reuse] — equivalent logic already exists elsewhere in this codebase
       - [stdlib] — the standard library already covers it
       - [builtin] — the framework/platform already provides it
       - [unneeded] — speculative code with no current caller (unused flag,
         unexercised branch, extension point nobody extends)
       - [simplify] — a one-implementation interface/factory, or a pure-forwarding
         wrapper, that should be inlined or merged
    5. If a finding is really a correctness bug, a security hole, or a performance
       problem rather than just unnecessary complexity, do NOT tag it here — note
       it separately as out-of-scope-for-OE so it can be routed to the
       Correctness, Performance, or Error Handling reviewer instead. Complexity
       must never be used to mask, or be mistaken for, a real bug.
    6. For each finding report: file:line, the one tag, a one-sentence description
       of what's unnecessary and why, the suggested deletion or replacement, and
       the number of lines that change would remove.
    7. Sum the lines-removed across findings you are confident about, from code you
       actually read — not estimated. Report that sum as a static count only. Do
       not state or imply runtime, token, bundle-size, or percentage savings: the
       simplified version was never built or run, so there is no measured baseline
       to compare against. If a real benchmark already exists in the codebase for
       the code in question, you may cite it — otherwise say nothing about
       performance impact."
  subagent_type: "Explore"
  model: "haiku"
```

**Routing out of scope**: when Agent 6 flags something that Phase 4 consolidation determines is actually a correctness, security, or performance issue, move it into the matching dimension (`CL-`, `PF-`, or `EH-` prefix) instead of reporting it as an OE finding. An over-engineered function that also happens to be buggy is a bug first.

### Report Addendum

Add a sixth dimension to Phase 4/5 output, alongside the existing five:

- **Dimension**: Simplicity & Over-Engineering
- **Finding prefix**: `OE-`
- **Default severity**: Minor or Nit. Escalate to Major only when the complexity itself causes a reliability or maintainability failure (e.g., a forwarding wrapper that silently drops an error the caller needs) — not merely because it exists.
- **Per-finding fields**: severity, `file:line`, the single tag from the list above, description, suggested deletion/replacement, lines-removed.

Report the aggregate as its own line, separate from the per-finding lines-removed counts:

> **Estimated lines removable (static count, not a benchmark): ~N**

`N` is the sum of lines-removed across all `OE-` findings, counted from code actually read during this review. Never state or imply a percentage, runtime, token, or bundle-size saving next to this number — no leaner version was built or measured. If the review surfaces a real, previously-measured benchmark for the flagged code, cite that benchmark by its source instead of inventing a figure.
