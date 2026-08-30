---
name: render
description: Turn a plan, PRD, review, audit, comparison, brainstorm, explanation
  or architecture map into an interactive HTML page the user marks up in place,
  then read their marks back and act on them. Every section carries an anchored
  comment affordance, so feedback returns bound to the exact thing it was left on.
  Use for "render this as a page", "make this visual", "I want to review this
  properly", "turn this plan into something I can comment on", or to wrap another
  skill's output (`render /review-code`). Not for generating a Mermaid diagram
  into docs/ (use docs-diagram), not for designing a UI for a product being built
  (use product-design-spec), and not for simplifying prose the user did not
  understand (use wtf).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: <mode|/skill|path> [subject]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task, Skill, Artifact
---

# Render

Build a page the user can work, not a document they have to scroll. Long
findings lists, requirement inventories, option matrices and step plans all lose
their shape as linear markdown. This skill gives them one, and gives the user a
way to answer back that survives the round trip.

## Invocation forms

| Form | Behavior |
|------|----------|
| `render <mode> [subject]` | Build that mode's page for the subject |
| `render /<skill> [args]` | Run the wrapped skill, then render its output in the matching mode |
| `render <path>` | Read an existing file and convert it to its matching mode |
| `render` | Show the mode table and ask which one; never pick one silently |

## Modes

| Mode | The page is | Per-item verdicts |
|------|-------------|-------------------|
| `prd` | Requirements grouped by family, the evidence behind each | keep / change / drop |
| `plan` | Ordered steps, their dependencies, the files each touches | approve / rework / cut |
| `review` | Findings by severity and file, with the code excerpt | fix / won't fix / discuss |
| `audit` | Whole-repo findings, filterable by area and severity | same triage as review |
| `compare` | Options against weighted criteria, evidence per cell | pick a winner |
| `brainstorm` | Idea cards, the tension each one resolves, by theme | shortlist / park / drop |
| `explain` | The one-line answer, the mechanism, then detail on demand | none, comments only |
| `map` | Module graph, data flow, entry points | none, comments only |

Each mode's contents are specified in `references/<mode>.md`. Load only the one
you need, and load it after the mode is settled.

## Workflow

### 1. Resolve the mode

From the first argument:

- A mode name: use it.
- A skill name with a leading slash: run that skill first, then map its output
  to a mode using the table in `references/wrapping.md`.
- A file path: read the file, then pick the mode its content matches. State
  which mode you picked and why, in one line, before building.
- Nothing: print the mode table above and ask. Do not guess.

### 2. Gather the real content

The page renders what the run actually produced. Never invent an item to fill a
grid, never write placeholder copy, never carry an example from a reference file
into a real page. If a section would be empty, the page says it is empty and
why.

A wrapped skill supplies its own output, and a file supplies its contents. With
a bare mode, do the work the mode implies before rendering: `render review` on a
diff runs the review first.

### 3. Load the design guidance

Load the `artifact-design` skill before writing any HTML. If the page will
declare a runtime capability, load `artifact-capabilities` too. These calibrate
the treatment and carry the current call contract; skipping them produces the
generic page this skill exists to avoid.

### 4. Build the page

[references/page-kit.md](references/page-kit.md) holds the document skeleton
and the state block, plus how a page is written and published. Anchors and the
comment affordance are specified in
[references/feedback-loop.md](references/feedback-loop.md), and every mode
carries them. Reach for [references/diagrams.md](references/diagrams.md) only
once the content turns out to have a shape worth drawing.

Five rules hold across every mode:

1. **Every page is annotatable.** Anchors and the comment affordance are not a
   per-mode feature. A page without them cannot return feedback, which is the
   point of the skill.
2. **Real content only.** See step 2.
3. **Theme-correct in all three states.** Define the light palette as tokens on
   bare `:root`, redefine those tokens under
   `@media (prefers-color-scheme: dark)` guarded by `:not([data-theme="light"])`,
   and redefine them again under `:root[data-theme="dark"]`. Give `body` an
   explicit token background. A color whose only definition sits inside a media
   block renders one theme's text on the other theme's background.
4. **Diagrams are inline SVG built from the page's own tokens.** Mermaid brings
   its own theme and fights the three-state setup above.
5. **State drives the DOM, never the reverse.** The page renders from its
   embedded state object. Saving serializes that object, never the live DOM.

### 5. Deliver and report

Report the output path, the published link if there is one, and whatever count
matters for this mode. Then say how to answer back: marks and comments are both
kept by the page, so the user presses save and tells you. Keep this to two
lines.

### 6. Read the marks back

When the user says they have marked it, read the page back per
`references/feedback-loop.md`, then act on what it returns. Group your response
by what they decided, not by page order, and name any comment whose anchor no
longer resolves rather than dropping it.

## Worked examples

**Bare mode** (`render compare postgres vs sqlite for the vault store`): gather
the real criteria from the project's own constraints and build the matrix with
evidence behind every cell. Publish it, report the link, and wait. The user
picks a winner on the page; you read it back and write the decision up.

**Wrapping a skill** (`render /review-security`): run `review-security` to
completion first. Its output is a severity-ranked list with file:line evidence,
which maps to `review` mode. Build the triage board from the findings it
actually produced, one anchor per finding.

**Converting a file** (`render docs/plans/auth.md`): read it first. It turns out
to be an ordered step list with dependencies, so say "rendering as `plan` mode"
before building. Do not rewrite the plan's content while converting it.

**No argument** (`render`): print the mode table and ask which mode. Build
nothing until that is answered.

## Notes

- The wrapped skill never needs to know this skill exists. `render /<skill>`
  runs it unchanged and renders what comes out.
- Re-running `render` on the same subject updates the same page when the output
  path matches. This is the intended way to revise, and it preserves comments
  whose anchors still resolve.
- Two modes carry no verdict controls, `explain` and `map`. They still carry
  anchored comments, which is usually the only feedback those pages need.
