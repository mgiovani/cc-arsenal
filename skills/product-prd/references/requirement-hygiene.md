# Requirement Hygiene: INVEST, EARS, RFC-2119, compound-split, vague blocklist

The shared, tool-neutral rulebook for writing a single testable requirement.
`product-prd` owns this file; `product-design-spec` references it inline for
screen-level acceptance criteria (via the `Skill` tool where available, else by
reading this file directly). `scripts/validate.py` and `scripts/hygiene.py`
enforce the mechanical subset.

## RFC-2119 normative language

Use these keywords, and only these, for obligations:

- **MUST / MUST NOT**: an absolute requirement / prohibition.
- **SHOULD / SHOULD NOT**: recommended; a deviation needs a documented reason.
- **MAY**: genuinely optional.

One requirement states **one** obligation. If you need two, write two requirements.

## The eight-term vague-word blocklist (verbatim)

These words are not testable and are **forbidden** in a requirement statement:

> **fast, scalable, intuitive, robust, secure, seamless, user-friendly, performant**

Replace each with a measurable target: "responds within 200 ms at p95", not
"fast"; "supports 10k concurrent sessions", not "scalable"; "meets WCAG 2.2 AA",
not "user-friendly".

## Compound-requirement split

A requirement is **compound** (and must be split) when it:

- contains two or more obligation keywords in one statement ("the system MUST log
  the user in and MUST send an email"), or
- joins two distinct behaviours with "and" / "or" (", and ...", ", or ..."), or
- describes more than one observable outcome.

Split it into one requirement per behaviour, each with its own ID and acceptance
criteria. `validate.py` flags multi-obligation statements (MAJOR) and comma-joined
clauses (MINOR); `hygiene.py` proposes the split count.

## INVEST self-check

Every requirement should be:

- **I**ndependent: minimal coupling to other requirements.
- **N**egotiable: a statement of intent, not a bolted-down implementation.
- **V**aluable: traceable to a user need, a goal, or an approved decision.
- **E**stimable: small and clear enough that effort is knowable.
- **S**mall: one behaviour. If Small/Estimable fails, split (see above).
- **T**estable: has Given/When/Then acceptance criteria a test can check.

When Small or Estimable fails, `hygiene.py` emits a `SPLIT` suggestion.

## EARS templates (system / non-UI requirements)

For NFR/SEC/DATA and other system-facing requirements, Gherkin's user framing
fits poorly: use EARS (Easy Approach to Requirements Syntax). Lead with the
trigger/condition, not bury it mid-sentence:

- **Ubiquitous:** "The system shall {{response}}."
- **Event-driven:** "When {{trigger}}, the system shall {{response}}."
- **State-driven:** "While {{state}}, the system shall {{response}}."
- **Optional-feature:** "Where {{feature is present}}, the system shall {{response}}."
- **Unwanted behaviour:** "If {{condition}}, then the system shall {{response}}."

`hygiene.py` emits an `EARS` suggestion when a non-UI requirement buries its
trigger or omits the normative verb.

## [NEEDS CLARIFICATION] tag

When a gap surfaces during authoring, do **not** guess: write the assumption
down as an inline, greppable tag:

```
[NEEDS CLARIFICATION: which auth provider (Auth0 or in-house)?]
```

`validate.py` scans for these and reports each one (MAJOR) so none ships silently.
Resolve every tag before hand-off, or move it to the decision log as an open question.

## Every requirement is also

- **Uniquely ID'd**: `PRD-<CAT>-NNN`, stable, never reused (see `requirement-standards.md`).
- **Traceable**: links back to an approved decision, a research finding, or a user need.
- **Evidence-tagged**: a finding, an evidence path, and a confidence level.
