# Update Strategies

Parallel subagent pattern and per-document-type checklist for multi-document updates
(SKILL.md Phase 3, "all" or "category" mode). For a single document, SKILL.md's inline
one-pass approach is enough, this file is only for the concurrent case.

## Spawning One Agent Per Document

```
Agent 1 - Architecture Update:
- prompt: "Update docs/architecture.md. Read it fully, grep the codebase to verify every
  claim (service names, counts, tech stack), remove anything that can't be confirmed,
  add missing components found in the code, preserve custom sections."
- subagent_type: "general-purpose"

Agent 2 - Data Model Update:
- prompt: "Update docs/data-model.md. Find actual ORM models, verify the ER diagram
  matches them, preserve custom sections."
- subagent_type: "general-purpose"

Agent 3 - Onboarding Update:
- prompt: "Update docs/onboarding.md. Verify every setup command and file path
  mentioned actually exists/runs, preserve custom sections."
- subagent_type: "general-purpose"
```

If no Task/subagent tool is available, run each of these prompts as a sequential
read-verify-write pass instead: same checklist, one document at a time.

## Per-Document-Type Checklist

**Architecture**: scan for services/modules/components, identify databases/caches/queues,
map data flow, regenerate the architecture diagram, preserve custom architecture notes.

**Data Model**: find ORM models, extract entities and relationships, regenerate the ER
diagram, document constraints, preserve custom data notes.

**Deployment**: find Docker/K8s configs, map services to infrastructure, document the
CI/CD pipeline, update environment configs, preserve custom deployment notes.

**Security**: find auth/authz code, map security boundaries, document encryption points,
identify security controls, preserve custom security notes.

## Example Output: Category Update

```
Core Documentation Category Updated

Updated (2 docs):
  docs/architecture.md (added microservices diagram — 5 services found in src/services/)
  docs/onboarding.md (setup instructions updated for new tooling in package.json)

Verified but unchanged (1 doc):
  docs/adr/ (5 records, all still accurate)

Next Steps:
  1. Review updated documentation
  2. Regenerate diagrams if code changes again: docs-diagram arch
  3. Create a new ADR for the recent decision: docs-adr "Decision Title"
```
