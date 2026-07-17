# Update Strategies

Parallel subagent patterns for documentation synchronization across multiple files.

## Single Document Updates

One Explore pass is enough: read the whole document, grep the codebase for each claim it makes,
and apply the fixes in the same write. Splitting one file's sections across multiple agents
just adds merge overhead for a result that funnels into a single file anyway.

## Multiple Document Updates ("all" or "category" mode)

Spawn one agent per document so they run concurrently:

```
Agent 1 - Architecture Update:
- prompt: "Update docs/architecture.md. Explore codebase, verify claims, remove false info, add missing components."
- subagent_type: "general-purpose"

Agent 2 - Data Model Update:
- prompt: "Update docs/data-model.md. Find actual models, verify ER diagram accuracy."
- subagent_type: "general-purpose"

Agent 3 - Onboarding Update:
- prompt: "Update docs/onboarding.md. Verify setup instructions and commands exist."
- subagent_type: "general-purpose"
```

## Update Process by Document Type

### For Architecture Documentation
1. Scan for services, modules, components
2. Identify databases, caches, queues
3. Map data flow
4. Generate architecture diagram
5. Update component descriptions
6. Preserve custom architecture notes

### For Data Model Documentation
1. Find ORM models
2. Extract entities and relationships
3. Generate ER diagram
4. Document constraints
5. Update entity descriptions
6. Preserve custom data notes

### For Deployment Documentation
1. Find Docker/K8s configs
2. Map services to infrastructure
3. Document CI/CD pipeline
4. Update environment configurations
5. Preserve custom deployment notes

### For Security Documentation
1. Find auth/authz code
2. Map security boundaries
3. Document encryption points
4. Identify security controls
5. Preserve custom security notes

## Example Output: All Docs Update

```
Documentation Update Complete

Updated (4 docs):
  docs/architecture.md (new microservices added)
  docs/data-model.md (schema changed, ER diagram regenerated)
  docs/deployment.md (K8s config updated)
  docs/adr/ (meta-ADR updated)

Up to Date (2 docs):
  docs/onboarding.md (no changes needed)
  docs/security.md (no changes needed)

Created (1 doc):
  docs/contributing.md (collaborative project detected)

Changes Summary:
  - 3 diagrams regenerated
  - 12 sections updated
  - 1 new document created
  - 0 manual sections affected
```

## Example Output: Specific Doc Update

```
Architecture Documentation Updated

File: docs/architecture.md

Changes:
  Added 2 new services (AuthService, NotificationService)
  Updated architecture diagram
  Documented new message queue integration
  Preserved custom deployment notes

Detected:
  - 5 services total
  - 3 databases (PostgreSQL, Redis, MongoDB)
  - 2 message queues (RabbitMQ, Kafka)
  - 8 external API integrations

Diagram: Updated with latest component relationships
```

## Example Output: Category Update

```
Core Documentation Category Updated

Updated (3 docs):
  docs/architecture.md
  docs/onboarding.md
  docs/adr/ (5 records)

Changes:
  - Architecture: Added microservices diagram
  - Onboarding: Updated setup instructions for new tooling
  - ADRs: Verified all properly formatted

Next Steps:
  1. Review updated documentation
  2. Consider updating diagrams: /docs-diagram arch
  3. Create new ADR for recent decision: /docs-adr "Decision Title"
```
