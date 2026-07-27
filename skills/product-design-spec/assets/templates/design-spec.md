<!-- template: design-spec: filled by the product-design-spec skill. Single file
     by default: docs/specs/design/design-spec.md. Split a screen into
     docs/specs/design/screens/SCR-NN.md only when it outgrows its inventory row. -->
---
title: "{{PRODUCT_OR_FEATURE}}: Design Spec"
tier: "{{small|medium|big}}"
owner: "{{OWNER}}"
source_prd: "{{PATH_TO_APPROVED_PRD}}"   # the design traces to this, and never overrides it
last_updated: "{{DATE}}"
---

# {{PRODUCT_OR_FEATURE}}: Design Spec

## Reuse baseline

<!-- The component library detected in the repo (shadcn / Tailwind / MUI / native / ...). Screens below
     reference these components by name. Bespoke components appear ONLY where no library primitive fits,
     each with a one-line reason. -->
Detected component library: {{LIBRARY}} ({{HOW_DETECTED e.g. components.json}}).

## Information architecture

<!-- The screen map / navigation model. A Mermaid diagram here is delegated to the docs-diagram skill
     (via the Skill tool where available, else apply its conventions inline). -->
{{IA_MAP}}

## User flows

<!-- The primary journey first (thin-slice), then secondary flows at medium/big. Mermaid via docs-diagram. -->
{{FLOWS}}

## Screen inventory

<!-- EVERY screen is a row. Only the 2-3 most critical get a full spec below; the rest stay one-liners.
     "Traces to" is mandatory: the PRD requirement id(s) this screen exists to satisfy. -->

| Screen ID | Name | Purpose | Traces to | Spec depth |
|---|---|---|---|---|
| SCR-01 | {{NAME}} | {{ONE_LINE_PURPOSE}} | PRD-FR-001 | full |
| SCR-02 | {{NAME}} | {{ONE_LINE_PURPOSE}} | PRD-UX-003 | inventory |

## Traceability

<!-- Lightweight requirement-id <-> screen-id table. Every screen must appear against at least one
     requirement; a requirement with no screen is a gap (tag it [NEEDS CLARIFICATION]). -->

| Requirement | Screen(s) |
|---|---|
| PRD-FR-001 | SCR-01 |
| PRD-UX-003 | SCR-02 |

## Critical screen specs

<!-- 2-3 screens ONLY. Each uses assets/templates/screen-spec.md. Speccing every screen is a failure. -->

{{SCREEN_SPEC_SCR_01}}

{{SCREEN_SPEC_SCR_02}}

## Accessibility

<!-- The WCAG 2.2 AA audit is DELEGATED to review-design (do not hand-roll it here). This section records the
     scope handed off and any screen-specific notes. Exclude WCAG 3.0 / APCA. -->
- Target: WCAG 2.2 AA. Audit delegated to `review-design`, including the 9 criteria new since 2.1
  (24px targets, focus appearance, dragging alternatives, accessible authentication, consistent help,
  redundant entry).
- Platform: {{Material 3 Expressive | Apple Liquid Glass | web}}: any translucent surface carries a
  mandatory contrast check (token work lives in `product-design-tokens`).

## Open questions

<!-- Tag unresolved gaps [NEEDS CLARIFICATION: ...]; give each an owner. A design implication that would
     change a requirement goes here as a question against the PRD: never silently redesigned. -->
- {{OPEN_QUESTION}}
