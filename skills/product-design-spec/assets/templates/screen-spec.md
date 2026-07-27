<!-- template: screen-spec: authored IN FULL only for the 2-3 most critical screens.
     Heading MUST carry the screen id (SCR-NN) so scripts/screen-states.py picks it up.
     ~10 fields. Keep the bold field labels intact: the linter keys off them. -->

### SCR-01: {{SCREEN_NAME}}

**Purpose**: {{WHY_THIS_SCREEN_EXISTS, one sentence}}

**Entry / exit**: how the user arrives here and where each action leads.

**Key components**: reuse the detected library by name (e.g. shadcn `Form`, `Dialog`, `DataTable`).
Bespoke components appear only with a one-line reason no primitive fit.

**Primary actions**: the main things a user does here.

**States**: cover the applicable subset of the ~10-state shortlist
(`assets/templates/state-shortlist.md`). The trio **empty / error / permission-denied** is required unless you
mark it `N/A: <reason>`. Never document only the happy path.

| State | Behaviour |
|---|---|
| loading | {{...}} |
| empty | {{...}} |
| populated | {{...}} |
| validation-error | {{...}} |
| recoverable-error | {{...}} |
| permission-denied | {{...}} |
| success | {{...}} |

**Validation**: input rules and the messages shown (field-level, inline).

**Accessibility / keyboard**: focus order, keyboard operability, visible focus, target size (≥24px), and
anything the `review-design` audit should check on this screen.

**Responsive**: behaviour across breakpoints (mobile / tablet / desktop) or platform size classes.

**Acceptance criteria**: Given/When/Then, testable. Apply the shared rulebook
`skills/product-prd/references/requirement-hygiene.md` (via the `Skill` tool where available, else read it).

1. Given {{GIVEN}}, when {{WHEN}}, then {{THEN}}.

**Traces to**: the PRD requirement id(s) this screen satisfies (e.g. `PRD-FR-001`, `PRD-UX-003`). A screen
that traces to nothing does not belong in the spec.
