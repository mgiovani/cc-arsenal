<!-- template: requirement: filled by the product-prd skill -->

### PRD-FR-001: {{title}}

**Status:** {{STATUS}} <!-- Approved (from an approved decision) | Assumption | Open -->

**Requirement**

<!-- One normative statement, one behaviour. RFC-2119: MUST / MUST NOT / SHOULD /
     SHOULD NOT / MAY. Never the eight vague terms (fast, scalable, intuitive,
     robust, secure, seamless, user-friendly, performant): give a measurable
     target instead. If two behaviours join with "and"/"or", split them into two
     requirements. See references/requirement-hygiene.md. -->

The system {{NORMATIVE_VERB}} {{REQUIREMENT_STATEMENT}}.

**Evidence** <!-- what backs this requirement; keep the three fields separate -->

- Finding: {{FINDING}}
- Evidence path: {{EVIDENCE_PATH}} <!-- repo file:line, a research-ledger row, or an approved decision ID -->
- Confidence: {{CONFIDENCE}} <!-- HIGH | MEDIUM | LOW -->

**Acceptance criteria**

1. Given {{GIVEN_1}}, when {{WHEN_1}}, then {{THEN_1}}.
2. Given {{GIVEN_2}}, when {{WHEN_2}}, then {{THEN_2}}.

**Scope boundary** <!-- state positively: what this requirement covers, and where the
     adjacent work lives: never "does not X". e.g. "Bulk export is handled in PRD-FR-014." -->

{{SCOPE_BOUNDARY}}

**Failure and edge cases**

{{FAILURE_AND_EDGE_CASES}}

<!-- Include the two sections below ONLY when this requirement is actually
     observable or touches user data / security. Delete them otherwise. -->

**Observability** (when relevant)

{{OBSERVABILITY}}

**Security and privacy** (when relevant)

{{SECURITY_AND_PRIVACY}}

<!-- Optional prioritization / metrics fields. Activate ONLY when finer
     granularity is wanted: see references/frameworks.md. Delete the ones you
     don't use; do not force all of them through every requirement. -->

<!--
**Priority (MoSCoW):** {{MOSCOW}}   <!-- Must | Should | Could | Won't -->
**Release:** {{RELEASE}}            <!-- MVP | Phase 1 | Phase 2 | Future -->
**Owner domain:** {{OWNER_DOMAIN}}
**Job to be done:** {{JTBD}}         <!-- When ..., I want ..., so I can ... -->
**Kano category:** {{KANO}}          <!-- Basic | Performance | Delighter -->
**RICE:** {{RICE}}                   <!-- Reach x Impact x Confidence / Effort -->
**North Star link:** {{NSM_LINK}}    <!-- how this moves the product's North Star metric -->
**HEART / AARRR:** {{METRIC_TAG}}    <!-- only the applicable category -->
-->

**Research references**

{{RESEARCH_REFERENCES}}

---

## ID categories

Requirement IDs follow `PRD-<CAT>-NNN` (e.g. `PRD-FR-001`), `<CAT>` one of six:

| CAT | Category | Owned by |
|---|---|---|
| FR | Functional | product-prd |
| NFR | Non-functional (performance, reliability, ops) | product-prd |
| UX | User experience | product-prd |
| SEC | Security & privacy | product-prd |
| DATA | Data & domain | product-prd |
| DES | Design (screens, tokens) | product-design-spec / product-design-tokens |
