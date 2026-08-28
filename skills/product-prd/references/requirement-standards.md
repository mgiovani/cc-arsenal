# Requirement Standards: IDs, quality, the decision log

The rules every requirement in a `product-prd` output must satisfy. For the
authoring rulebook (RFC-2119, the eight-term vague blocklist, INVEST, EARS,
compound-split, `[NEEDS CLARIFICATION]`) see the shared `requirement-hygiene.md`.
`scripts/validate.py` enforces the mechanical subset; `scripts/hygiene.py` adds
advisory INVEST/EARS lints.

## ID scheme: six categories

Every requirement has a **unique, stable** ID: `PRD-<CAT>-NNN` (zero-padded, e.g.
`PRD-FR-001`). IDs are never reused or renumbered: deprecate, don't delete.

| CAT | Domain | Owned by |
|---|---|---|
| FR | Functional | product-prd |
| NFR | Non-functional (performance, reliability, operations) | product-prd |
| UX | User experience | product-prd |
| SEC | Security & privacy | product-prd |
| DATA | Data & domain | product-prd |
| DES | Design (screens, tokens) | product-design-spec / product-design-tokens |

This is the whole set: no per-concern proliferation (performance, a11y, i18n,
analytics, etc. fold into NFR/UX rather than spawning their own prefix).

## Requirement quality: every requirement is

1. **Unambiguous**: one interpretation.
2. **Testable**: has Given/When/Then acceptance criteria (or an EARS clause for
   non-UI requirements) a test can check.
3. **Traceable**: links back to an approved decision, a research finding, or a user
   need. Record the link in the requirement's evidence block; a big/execution PRD may
   also keep a requirement ↔ release table.
4. **Single-behaviour**: one obligation per requirement (split compounds).
5. **Evidence-tagged**: a finding, an evidence path, and a confidence level.

Acceptance criteria format (numbered, one scenario each):

```
Given <precondition>
When <action>
Then <observable outcome>
```

Optional prioritization (MoSCoW/RICE) and metrics (NSM/HEART/AARRR) fields are
opt-in: see `frameworks.md`. Don't force them through every requirement.

## Status & the decision log

A requirement's **Status** is `Approved` (from an approved decision), `Assumption`
(pending validation), or `Open` (undecided). Nothing reaches `Approved` without a
corresponding `decision` row in the log: a recommendation you made is not an
approved requirement until the user decides.

All reasoning behind the requirements lives in **one append-only** log
(`assets/templates/decision-log.md`). Its `type` column separates the four kinds
of entry: `decision | assumption | question | finding`, each with its own status
vocabulary and, for findings and
assumptions, a confidence level (**HIGH** multiple sources · **MEDIUM** single
source/inference · **LOW** unconfirmed). Rows are never edited; supersede instead.
Triangulate any legal/security/compliance finding to HIGH before it drives a MUST.
