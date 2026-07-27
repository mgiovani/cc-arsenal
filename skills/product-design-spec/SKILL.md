---
name: product-design-spec
description: >-
  Authors the design specification for an approved PRD (information
  architecture, user flows, a screen inventory, and per-screen state and
  interaction specs), reusing the project's existing component library first
  and tracing every screen back to a PRD requirement ID. Lean by default: one
  design-spec.md, full specs for only the 2-3 most critical screens, WCAG 2.2 AA
  delegated to review-design. Use for "write a design spec", "map the user
  flows", "screen inventory with states", or "IA and screen states for this
  feature". Writes no UI code. Not for a UX critique of an existing UI (use
  review-design), the visual token system (use product-design-tokens), or
  rendering mockups and hero images (use codex-imagegen).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: "<prd-path | idea | #issue | PROJ-123> [--tier small|medium|big]"
context: fork
agent: general-purpose
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git *), Bash(gh *), Bash(python *), Bash(uv run *), Task, WebSearch, WebFetch, AskUserQuestion, Skill
---

# Product Design Spec

Turn an **approved PRD** into the design half of the spec (IA, flows, a screen inventory, and per-screen
state/interaction specs), spec'ing only as much as the work warrants. This skill **writes no UI code**; it
produces the design the build (`implement-feature`, `team-implement`) then works from. Output lands under
`docs/specs/design/`.

## Input

$ARGUMENTS

Parse the source (first match wins), then read it:

| Pattern | Source | Read via |
|---|---|---|
| existing `docs/specs/prd/*.md` or any path | the approved PRD / a file | Read it (grab every `PRD-<CAT>-NNN` ID) |
| `PROJ-123` | Jira | `jira issue view PROJ-123` |
| `#42` / `owner/repo#42` | GitHub issue | `gh issue view 42 --json title,body,labels,comments` |
| `http(s)://` | URL | `WebFetch` |
| anything else | plain text | the idea itself |

A trailing `--tier small|medium|big` overrides the size assessment.

## Prerequisites & fallback

Component-library detection and flow research use the `Task` tool with `Explore`/haiku subagents. **No `Task`
tool?** Run every detection and research step inline, sequentially: the phase → gate → phase structure below
is the workflow; subagents are just how it parallelizes.

## Gate: an approved PRD is the source of truth

A design spec **traces to requirements it does not invent**. Before spec'ing anything:

- If an approved PRD (or a clear requirement set) exists, read it and harvest every requirement ID.
- If **no PRD exists**, do not fabricate requirements. Stop and say so:
  > "There's no approved PRD to trace this design to. Point me at one, or run `product-prd` first and I'll spec
  > the design against it."

**Source-of-truth hierarchy (never silently violate it):** `approved requirement > design spec > mockup`. A
mockup or a nice-looking screen **never** overrides an approved requirement: if the design implies a change,
flag it as an open question against the PRD, don't quietly redesign the requirement away.

## Lean by default

The organizing principle. **Default to a single `docs/specs/design/design-spec.md`** and split a screen into
its own file under `docs/specs/design/screens/` only when it outgrows the inventory.

- **Full per-screen specs for only the 2-3 most critical screens.** Every other screen gets a one-line
  inventory entry. Speccing every screen is a failure mode, not thoroughness.
- **Thin-slice, not waterfall:** spec the IA and **one** critical journey end-to-end first, produce output
  early, then iterate for breadth.
- **Cost stop-condition:** if the work seems to want a giant state matrix or a screen-per-file tree, **stop and
  ask** before emitting it. Never auto-generate a 30-file design tree.

## Reuse the existing component library first

Before specifying anything bespoke, detect and adopt what the project already ships (spawn an `Explore`/haiku
agent or check inline):

| Marker | Library to reuse |
|---|---|
| `components.json` | shadcn/ui |
| `tailwind.config.*` | Tailwind |
| `@mui/material` in `package.json` | MUI |
| `*.swift` + SwiftUI / `@Composable` in Kotlin | native platform components |

Name the detected library in the spec and reference its components by name. Invent bespoke components only for
genuinely novel surfaces, and say why the library couldn't cover them.

## Tiers

| Tier | When | Output |
|---|---|---|
| **small** | one feature/surface | IA sketch + the single primary flow + a screen list with applicable states noted, one file |
| **medium** | a module or small app | IA + 2-3 key flows + a screen inventory + a full spec for the 1-2 most critical screens |
| **big** | a full product/app | full IA + primary+secondary flows + complete inventory + full spec for only the 2-3 most critical surfaces |

Full detail, the reuse ladder, and the source-of-truth rule: `references/design-workflow.md`.

## Workflow

Four phases: **Discover → thin-slice one journey → ═plan gate═ → Author → Validate & hand off.**

### Phase: Discover

Read the approved PRD and harvest its requirement IDs. Detect the component library (above). Pick the
discovery mode by context: cold start → 3-5 lettered clarifying questions (terse answers like `1A,2C`); warm
start → synthesize from the conversation + a repo scan, then run a lightweight gap check. Tag every finding
**CONFIRMED / INFERRED / UNKNOWN**: never present an inference as a fact.

### Phase: Thin-slice one journey

Sketch the IA (nav / screen map), then spec **one** critical journey end-to-end (the flow, its screens, and
their states) before going wide. This proves the shape early and is cheap to correct.

### Phase: Plan gate (authorization)

Present the IA + screen inventory + which 2-3 screens you'll spec in full, and ask:

> "Here's the IA, the screen inventory, and the 2-3 critical screens I'd spec in full, each traced to
> {req IDs}. Authorize me to author `docs/specs/design/design-spec.md`?"

**Stop here if the answer is no**: revise and re-present. Author nothing before authorization.

### Phase: Author

Create the single file from `assets/templates/design-spec.md`:

- **IA + flows:** delegate Mermaid flow/journey diagrams to the `docs-diagram` skill (via the `Skill` tool
  where available, otherwise apply its diagram conventions inline).
- **Screen inventory:** every screen is a row with a Screen ID (`SCR-NN`), a purpose, and the **PRD
  requirement ID(s) it traces to**. Fill the lightweight **traceability table** (requirement-ID ↔ screen-ID).
- **Critical screen specs (2-3 only):** use `assets/templates/screen-spec.md` (~10 fields). Enumerate the
  **applicable subset** of the ~10-state shortlist (`assets/templates/state-shortlist.md`): never just the
  happy path. Each critical screen carries an **accessibility/keyboard** field, a **responsive** field, and
  **acceptance criteria**. For AC quality, apply `product-prd`'s shared **requirement-hygiene** rulebook
  inline (via the `Skill` tool where available, else read `requirement-hygiene.md` from `skills/product-prd/references/`):
  do not duplicate it here.
- **Personas (only if the PRD lacks them and they change the design):** `assets/templates/persona.md`, ~6
  fields, evidence-labeled, **no invented demographics**.
- **Tag every unresolved gap `[NEEDS CLARIFICATION: ...]`** rather than guessing: it stays greppable.

### Phase: Validate & hand off

```bash
python skills/product-design-spec/scripts/screen-states.py --dir docs/specs/design   # gate: 0 MAJOR
```

Fix every MAJOR (a critical screen missing its empty/error/permission states, or missing an
a11y-keyboard / responsive / acceptance-criteria field, or a screen that traces to no requirement). Then:

- **Delegate the accessibility audit to `review-design`** (via the `Skill` tool where available, otherwise
  apply its checklist inline): WCAG 2.2 AA, including the 9 criteria new since 2.1 (24px target size, focus
  appearance, dragging alternatives, accessible authentication, consistent help, redundant entry). **Do not
  hand-roll the audit** and do not upgrade to WCAG 3.0 / APCA (`references/design-workflow.md` names the
  scope). Platform surfaces: Material 3 Expressive and Apple Liquid Glass: pair any translucent surface with a
  mandatory contrast check.
- **Self-grade** inline (no separate report file): does every screen trace to a requirement? Do the critical
  screens cover their error/empty/permission states? Is anything over-specced? State the readiness verdict in a
  sentence or two.
- **Hand off:** report the written path. Name the downstream consumers: `product-design-tokens` (consumes the
  screen inventory) and `implement-feature` / `team-implement` (builds the UI). Offer `project-planner` for a
  screen-build breakdown.

## Anti-hallucination

- Never invent a requirement. Every screen traces to a PRD requirement ID; a mockup never overrides an approved
  requirement (source-of-truth hierarchy above).
- Tag every finding CONFIRMED / INFERRED / UNKNOWN; never present an inference as a fact.
- Reuse the detected component library before inventing bespoke components; name what you detected.
- No invented personas or demographics: evidence-label every persona field and omit unbacked demographics.
- Delegate the WCAG audit to `review-design`; do not fabricate conformance claims. Run `screen-states.py`
  before declaring done.
- The plan gate is real: author files only after explicit authorization.

## References

- `references/design-workflow.md`: the four phases, thin-slice rule, tiers, the component-reuse ladder, the source-of-truth hierarchy, the ~10-state shortlist, WCAG 2.2 AA scope (delegated to review-design), Material 3 Expressive / Apple Liquid Glass
- `product-prd`'s shared **requirement-hygiene** rulebook: RFC-2119, the vague blocklist, INVEST, GWT; referenced inline for screen-level acceptance criteria, not duplicated. Read it from `skills/product-prd/references/` (its `requirement-hygiene.md`).
- `assets/templates/`: design-spec, screen-spec, state-shortlist, persona
- `scripts/screen-states.py`: critical-screen state/field/traceability linter

## Boundaries

- The requirements themselves → `product-prd`.
- The visual token system (DTCG / DESIGN.md) → `product-design-tokens`.
- A UX / accessibility critique of an existing or rendered UI → `review-design`.
- Rendering illustrative assets, mockups, heroes, or icons → `codex-imagegen` / `nanobanana`.
- Building the UI → `implement-feature` / `team-implement`.
- Enforces the source-of-truth hierarchy (approved requirement > design spec > mockup). Writes no application code.
