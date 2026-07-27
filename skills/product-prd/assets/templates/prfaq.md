<!-- template: prfaq (BIG tier / VALIDATION intent): Amazon working-backwards.
     Use when the question is "SHOULD we build this?" not "how do we build it?".
     Single PRD.md by default. -->
---
title: "{{PRODUCT}}: PR/FAQ"
tier: big
intent: validation
owner: "{{OWNER}}"
last_updated: "{{DATE}}"
---

# Press Release

<!-- Write it as if the product already shipped. One page, dated, customer-facing. -->

**{{CITY}}, {{DATE}}.** {{HEADLINE_ANNOUNCEMENT}}

{{SUBHEAD_THE_PROBLEM_AND_WHO_HAS_IT}}

{{HOW_THE_PRODUCT_SOLVES_IT}}

> "{{CUSTOMER_QUOTE}}" ({{CUSTOMER_NAME_ROLE}})

{{HOW_TO_GET_STARTED}}

# Top 3 reasons this will fail (mandatory)

<!-- Non-optional. The most honest section in the doc: if you can't fill it,
     you haven't pressure-tested the idea. -->
1. {{FAILURE_1}}
2. {{FAILURE_2}}
3. {{FAILURE_3}}

# External FAQ

<!-- What a customer / the press would ask. -->
**{{Q_EXTERNAL_1}}**
{{A_EXTERNAL_1}}

**{{Q_EXTERNAL_2}}**
{{A_EXTERNAL_2}}

# Internal FAQ

<!-- What the team / leadership would ask: sizing, cost, risk, dependencies,
     what we're NOT doing. Keep facts, assumptions, and recommendations separate.
     Tag unknowns [NEEDS CLARIFICATION: ...]. -->
**{{Q_INTERNAL_1}}**
{{A_INTERNAL_1}}

**{{Q_INTERNAL_2}}**
{{A_INTERNAL_2}}

# Non-Goals

<!-- Stated POSITIVELY: what's out of this bet and where/when it's revisited. -->
- {{NON_GOAL_1}}
- {{NON_GOAL_2}}

# Decision requested

<!-- The validation ask: build / don't build / gather more evidence, and what
     would change the answer. -->
{{DECISION_REQUESTED}}
