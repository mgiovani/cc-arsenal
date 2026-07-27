# Design-Spec Workflow: phases, tiers, reuse ladder, states, accessibility scope

Companion to `SKILL.md`. The SKILL.md body is the source of truth for the flow; this file carries the detail
that would bloat it.

## The four phases

1. **Discover**: read the approved PRD, harvest every `PRD-<CAT>-NNN` id, detect the component library, pick
   the discovery mode (cold → 3-5 lettered questions; warm → synthesize + gap check). Tag findings
   CONFIRMED / INFERRED / UNKNOWN.
2. **Thin-slice one journey**: sketch the IA, then spec **one** critical journey end-to-end (flow → screens →
   states) before going wide. Produce output early; it is cheap to correct a thin slice and expensive to
   correct a finished tree.
3. **Plan gate (authorization)**: present the IA, the screen inventory, and the 2-3 screens you'll spec in
   full (each with its requirement ids). Author nothing until the user says yes.
4. **Author → Validate & hand off**: write the single `design-spec.md`, run `screen-states.py`, delegate the
   WCAG audit to `review-design`, self-grade, hand off.

## Tiers

Pick by the size of the surface, not by ambition. Every tier is single-file by default.

| Tier | When | Deliverable |
|---|---|---|
| **small** | one feature / one surface | IA sketch + the single primary flow + a screen list with applicable states noted |
| **medium** | a module or small app | IA + 2-3 key flows + a screen inventory + a full spec for the 1-2 most critical screens |
| **big** | a full product / app | full IA + primary+secondary flows + a complete inventory + full spec for **only** the 2-3 most critical surfaces |

At every tier the rest of the screens get a one-line inventory row, not a full spec. If a screen genuinely
outgrows its inventory row, split it into `docs/specs/design/screens/SCR-NN.md`: one screen at a time, not a
tree. Cost stop: if the work wants a giant state matrix or a screen-per-file explosion, stop and ask first.

## Reuse the existing component library first (the ladder)

Inventing a bespoke component is the **last** rung, not the first. Detect what the project already ships and
adopt it by name:

| Marker file / signal | Reuse |
|---|---|
| `components.json` | shadcn/ui: reference its primitives (Button, Dialog, Form, …) |
| `tailwind.config.*` | Tailwind utility system + any existing component layer |
| `@mui/material` in `package.json` | MUI components + theme |
| `chakra`, `@radix-ui/*`, `antd`, `mantine` in deps | that library's components |
| SwiftUI (`*.swift`) / Jetpack Compose (`@Composable`) | native platform components |

Name the detected library in the spec and reference its components. Only specify a bespoke component when no
library primitive fits, and record *why*.

## Source-of-truth hierarchy

`approved requirement > design spec > mockup`. A mockup or a good-looking screen **never** silently overrides
an approved requirement. If the design implies the requirement should change, raise it as an open question
against the PRD (`[NEEDS CLARIFICATION: ...]`): don't quietly redesign the requirement away. Every screen in
the inventory traces to at least one requirement id; the lightweight traceability table
(requirement-id ↔ screen-id) makes the chain greppable without a 17-hop matrix.

## The ~10-state shortlist

For each **critical** screen, cover the **applicable subset**: not every state on every screen, but never
just the happy path. The commonly-forgotten trio (empty, error, permission-denied) is required unless the
screen explicitly marks it N/A with a reason.

1. **loading**: data in flight (skeleton / spinner).
2. **empty**: no data yet / first run / zero results.
3. **populated**: the default content state.
4. **validation-error**: user input is invalid (inline, field-level).
5. **recoverable-error**: a system/network failure the user can retry.
6. **permission-denied**: the user isn't allowed (403 / locked / gated).
7. **offline**: no connectivity, where relevant.
8. **success**: an action confirmed.
9. **disabled / read-only**: the surface or an action is inert.

Add others only if applicable to this surface (e.g. onboarding/first-run, no-search-results, expired-session,
partial/optimistic). See `assets/templates/state-shortlist.md`.

## Accessibility scope: delegated, not hand-rolled

The WCAG audit is **delegated to `review-design`** (via the `Skill` tool where available, otherwise apply its
checklist inline). The target is **WCAG 2.2 AA** (W3C Recommendation since Oct 2023). Explicitly **exclude
WCAG 3.0 and APCA**: WCAG 3.0 is an unfinished Working Draft with no conformance model; do not let an agent
"upgrade" the guidance to it.

Hand `review-design` this checklist of the **9 success criteria new since WCAG 2.1** so a legacy 2.1-era pass
doesn't silently miss them:

| SC | Name | Level |
|---|---|---|
| 2.4.11 | Focus Not Obscured (Minimum) | AA |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA |
| 2.4.13 | Focus Appearance | AAA |
| 2.5.7 | Dragging Movements (a non-drag alternative) | AA |
| 2.5.8 | Target Size (Minimum), **24×24 CSS px** | AA |
| 3.2.6 | Consistent Help | A |
| 3.3.7 | Redundant Entry | A |
| 3.3.8 | Accessible Authentication (Minimum) | AA |
| 3.3.9 | Accessible Authentication (Enhanced) | AAA |

The AA target hinges on the AA/A rows (target size, focus not obscured, dragging, accessible auth, consistent
help, redundant entry). Each critical screen still carries its own **accessibility/keyboard** field so the
audit has something concrete to check.

## Platform currency

- **Material 3 Expressive** (rolled out 2025-2026): cite spring-based (stiffness/damping) motion tokens, not
  duration/easing; Jetpack Compose is the reference implementation.
- **Apple Liquid Glass** (WWDC25 / OS-26): the current material language. Any translucent surface **must** be
  paired with a WCAG 2.2 AA contrast check, since dynamically-tinted translucency is a documented
  contrast-failure risk. The token-level contrast work belongs to `product-design-tokens`.
