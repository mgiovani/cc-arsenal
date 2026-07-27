<!-- template: decision-log: ONE append-only, typed log. Replaces the old four
     ledgers. Never rewrite a row; append a new one (SUPERSEDED the old). The
     `type` column carries what used to be four separate tables. -->

# Decision Log: {{PRODUCT}}

Append-only. Rows are never edited or deleted: to change an entry, add a new
row and mark the old one `SUPERSEDED`. One table, four `type`s:

- **decision**: a product/architecture choice the user approved.
- **assumption**: a working belief pending validation.
- **question**: an open item, ideally with an owner.
- **finding**: an externally-sourced research fact (always cited).

| # | Type | Summary | Status | Evidence / Source | Confidence | Date |
|---|---|---|---|---|---|---|
| 1 | decision | {{DECISION}} | APPROVED | {{APPROVED_BY_OR_REF}} |  | {{DATE}} |
| 2 | assumption | {{ASSUMPTION}} | UNCONFIRMED | {{BASIS}} | MEDIUM | {{DATE}} |
| 3 | question | {{OPEN_QUESTION}} | OPEN ({{OWNER}}) |  |  | {{DATE}} |
| 4 | finding | {{RESEARCH_FINDING}} | COMPLETE | {{SOURCE_URL}} | HIGH | {{DATE}} |

<!-- Status vocabulary by type:
     decision:   PENDING | APPROVED | DEFERRED | REJECTED | SUPERSEDED
     assumption: UNCONFIRMED | CONFIRMED | INVALIDATED | SUPERSEDED
     question:   OPEN | ANSWERED | DEFERRED | SUPERSEDED
     finding:    PLANNED | IN_PROGRESS | COMPLETE | BLOCKED | SUPERSEDED
     Confidence (findings/assumptions): HIGH | MEDIUM | LOW. Triangulate any
     legal/security/compliance finding to HIGH before it drives a MUST. -->
