<!-- template: prd-full (BIG tier / EXECUTION intent): the numbered, traceable
     PRD for "we've decided to build this; here's exactly what". ~8 pages cap.
     Single PRD.md by default; split a section into its own file (or use
     scaffold.py --enterprise) ONLY when that section outgrows itself. -->
---
title: "{{PRODUCT}}: Product Requirements"
tier: big
intent: execution
status: "{{STATUS}}"  # Draft | In Review | Approved
owner: "{{OWNER}}"
target_release: "{{TARGET_RELEASE}}"
last_updated: "{{DATE}}"
---

# {{PRODUCT}}

## 1. Problem & evidence

<!-- The evidenced problem. CONFIRMED / INFERRED / UNKNOWN tags; cite every
     external claim. -->
{{PROBLEM_AND_EVIDENCE}}

## 2. Goals & success metrics

<!-- Each metric with baseline / target / measurement window, traceable to the
     North Star. See references/frameworks.md for the metrics pipeline. -->
| Metric | Baseline | Target | Window |
|---|---|---|---|
| {{METRIC}} | {{BASELINE}} | {{TARGET}} | {{WINDOW}} |

## 3. Non-Goals (mandatory)

<!-- MANDATORY. Each stated POSITIVELY: where the excluded work lives or when
     it's revisited. -->
- {{NON_GOAL_1}}
- {{NON_GOAL_2}}

## 4. Scope & release boundaries

<!-- What's in this release vs deferred. RICE only on genuinely disputed edges
     (references/frameworks.md): don't score everything. -->
{{SCOPE}}

## 5. Requirements (numbered)

<!-- One requirement per item via assets/templates/requirement.md: ID, RFC-2119
     language, one behaviour, evidence block, GWT acceptance criteria, positive
     scope boundary. No vague terms. Split compound "and/or" statements. -->
### PRD-FR-001: {{TITLE}}
The system MUST {{STATEMENT}}.

**Acceptance criteria**

1. Given {{GIVEN}}, when {{WHEN}}, then {{THEN}}.

## 6. Edge & failure cases

{{EDGE_AND_FAILURE_CASES}}

## 7. Open questions

<!-- Each with an owner and a deadline. Tag anything still unresolved
     [NEEDS CLARIFICATION: ...] rather than guessing. -->
| Question | Owner | Deadline |
|---|---|---|
| {{QUESTION}} | {{OWNER}} | {{DEADLINE}} |

## 8. Changelog (dated)

| Date | Change |
|---|---|
| {{DATE}} | Initial draft |
