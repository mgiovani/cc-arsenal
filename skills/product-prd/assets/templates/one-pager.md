<!-- template: one-pager (MEDIUM tier): Lenny-style, <=2 pages. Single PRD.md.
     If this outgrows ~5-7 requirements or touches >1 team/system, STOP and
     restart in prd-full.md (the graduating guard). -->
---
title: "{{PRODUCT_OR_FEATURE}}"
tier: one-pager
owner: "{{OWNER}}"
last_updated: "{{DATE}}"
---

# {{PRODUCT_OR_FEATURE}}

## Problem & evidence

<!-- The problem, plus the evidence that it's real. Keep facts (CONFIRMED),
     assumptions, and recommendations separate: never present a recommendation
     as a fact. -->
{{PROBLEM_AND_EVIDENCE}}

## Appetite (optional)

<!-- Shape Up: set the time-box BEFORE the solution, not after. Delete if unused. -->
{{APPETITE}}

## Solution narrative

<!-- How it works for the user, in prose. WHAT/WHY, not implementation HOW. -->
{{SOLUTION_NARRATIVE}}

## Success metric(s)

<!-- 1-2 metrics, each traceable to the product's North Star. A metric with no
     link to the North Star is a signal the requirement may not belong. -->
- {{METRIC_1}}

## Scope: requirements

<!-- Each requirement: an ID, RFC-2119 language, one behaviour, GWT acceptance
     criteria. No vague terms. Use assets/templates/requirement.md per item. -->
### PRD-FR-001: {{TITLE}}
The system MUST {{STATEMENT}}.

**Acceptance criteria**

1. Given {{GIVEN}}, when {{WHEN}}, then {{THEN}}.

## Non-Goals (mandatory)

<!-- MANDATORY at this tier. Each stated POSITIVELY (where the excluded work
     lives or when it's revisited) because a downstream agent can't infer scope
     from omission. -->
- {{NON_GOAL_1}}
- {{NON_GOAL_2}}

## Open questions

<!-- Tag unresolved gaps [NEEDS CLARIFICATION: ...]; give each an owner. -->
- {{OPEN_QUESTION}}
