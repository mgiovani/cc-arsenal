---
description: "Update documentation by syncing with current codebase state"
argument-hint: "[all|<doc-name>|category:<name>]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash(git *)", "Task", "TodoWrite"]
---

# Update Documentation

Synchronize documentation with the current codebase state. Can update all docs, specific files, or entire categories.

## Anti-Hallucination Guidelines

**CRITICAL**: Documentation updates must reflect REALITY, not assumptions:
1. **Explore before updating** - Use Explore agent to understand actual codebase state
2. **Verify every claim** - Before writing any statement, verify it with code
3. **Count accurately** - Use find/glob for exact counts, never estimate
4. **Remove stale content** - Delete claims about features that no longer exist
5. **Cross-reference** - After updating, verify the update matches reality

## Your Task

### Phase 1: Deep Codebase Analysis (Use Explore Agent)

**IMPORTANT**: Before updating ANY documentation, thoroughly explore the codebase:

```
Use Task tool with Explore agent:
- prompt: "Comprehensively analyze this codebase. Find: 1) All actual source files and their purposes, 2) Real component counts (services, models, APIs), 3) Actual directory structure with content verification, 4) Technologies actually in use (check package files). Return ONLY verified facts with file paths as evidence."
- subagent_type: "Explore"
```

### Phase 2: Track Progress (Use TodoWrite)

For updating multiple documents, use TodoWrite to track progress:
```
Create todos for each document to update, marking them in_progress as you work
```

### Phase 3: Parse Arguments
   - Extract update mode from `$ARGUMENTS`
   - Modes:
     - No args or `all` → Update all relevant docs
     - `<doc-name>` → Update specific doc (e.g., `architecture`)
     - `category:<name>` → Update category (e.g., `category:data`)
   - Default: Update all

2. **Determine Update Scope**:

   **For "all" mode**:
   - Analyze entire project
   - Identify all relevant documentation types
   - Update everything that exists or should exist

   **For specific doc mode**:
   - Validate doc name
   - Find the corresponding file
   - Update only that document

   **For category mode**:
   - Parse category name: `core`, `data`, `infrastructure`, `development`
   - Identify all docs in that category
   - Update all docs in the category

3. **Analyze Codebase**:
   - Detect technology stack
   - Find database models (for data docs)
   - Find deployment configs (for infrastructure docs)
   - Identify services and components (for architecture)
   - Check for recent code changes

4. **Check Documentation Freshness**:
   ```bash
   # For each doc, compare with related code changes
   !`git log --since="$(git log -1 --format=%ai docs/architecture.md)" --oneline --name-only | head -30`
   ```
   - Identify which docs are outdated
   - Prioritize updates

5. **Load Templates**:
   - Template location: `resources/templates/`
   - Load appropriate templates based on docs being updated

### Phase 4: Parallel Updates (Use SubAgents)

#### For Multiple Documents ("all" or "category" mode)

Spawn parallel subagents for each document:

```
Use Task tool with multiple parallel agents:

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

#### For Single Document (Section-Level Parallelization)

**Even when updating ONE document**, spawn subagents for each major section:

```
Example: Updating docs/architecture.md

First, read the document and identify logical sections, then spawn parallel agents:

Agent 1 - Components Section:
- prompt: "Verify the 'Components' section in docs/architecture.md. For each component listed, confirm it exists in the codebase. Report which are real and which are hallucinations."
- subagent_type: "Explore"

Agent 2 - Technology Stack Section:
- prompt: "Verify the 'Technology Stack' section in docs/architecture.md. Check package.json/pyproject.toml for actual dependencies. Report mismatches."
- subagent_type: "Explore"

Agent 3 - Diagrams Section:
- prompt: "Verify all diagrams in docs/architecture.md. For each node/entity in diagrams, confirm it exists in code. Report diagram elements that don't exist."
- subagent_type: "Explore"

Agent 4 - Data Flow Section:
- prompt: "Verify the 'Data Flow' section. Trace actual imports and function calls to confirm the described flow is accurate."
- subagent_type: "Explore"

After all agents return, merge their findings and update the document.
```

**Section identification pattern**:
```
1. Read the target document
2. Identify H2 (##) sections as logical blocks
3. For each section with verifiable claims, spawn an Explore agent
4. Collect results and apply updates
```

6. **Update Each Document**:
   - Re-analyze relevant parts of codebase
   - **Verify each claim before writing** - Read actual files
   - Regenerate diagrams if needed
   - Update content while preserving custom sections
   - Replace placeholders with current values
   - **Remove claims that cannot be verified**

### Phase 5: Post-Update Verification

**After updating, verify the updates are accurate**:
```
For each updated document:
1. Re-read the document
2. For each major claim, verify against actual code
3. If any claim cannot be verified, remove it
4. Run /docs:check to validate
```

7. **Preserve Custom Content** (Important):
   - Keep manually added sections
   - Preserve non-template content
   - Only update auto-generated parts
   - If unsure, ask before overwriting

8. **Report Results**:
   - List documents updated
   - List documents skipped (up to date)
   - List documents created (if missing)
   - Show summary of changes

## Documentation Categories

### Core Documentation
Files that are always relevant:
- `docs/architecture.md` - System architecture
- `docs/onboarding.md` - Developer onboarding
- `docs/adr/` - Architecture Decision Records

**Update when**: Architecture changes, setup process changes

### Data Documentation
Files relevant if database detected:
- `docs/data-model.md` - Database schema & ER diagrams

**Update when**: Schema changes, models modified

### Infrastructure Documentation
Files relevant if deployment configs detected:
- `docs/deployment.md` - CI/CD & deployment
- `docs/security.md` - Security architecture

**Update when**: Infrastructure changes, security updates

### Development Documentation
Files relevant for collaborative projects:
- `docs/contributing.md` - Contribution guidelines
- `docs/rfc/` - RFC documents
- `docs/api-documentation.md` - API documentation

**Update when**: Process changes, API changes

## Usage

Update all documentation:
```
/docs:update
/docs:update all
```

Update specific document:
```
/docs:update architecture
/docs:update data-model
/docs:update onboarding
/docs:update deployment
/docs:update security
```

Update entire category:
```
/docs:update category:core
/docs:update category:data
/docs:update category:infrastructure
/docs:update category:development
```

With context:
```
/docs:update architecture after microservices refactor
/docs:update data-model after schema migration
/docs:update category:core for onboarding review
```

## Document Name Mapping

| Argument        | File Path                  |
|----------------|----------------------------|
| `architecture` | `docs/architecture.md`     |
| `onboarding`   | `docs/onboarding.md`       |
| `data-model`   | `docs/data-model.md`       |
| `deployment`   | `docs/deployment.md`       |
| `security`     | `docs/security.md`         |
| `contributing` | `docs/contributing.md`     |
| `api-docs`     | `docs/api-documentation.md`|

## Update Process Detail

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

## Change Detection

```bash
# Check what changed since last doc update
!`git log --since="$(git log -1 --format=%ai docs/architecture.md 2>/dev/null || echo '30 days ago')" --oneline`

# Find modified source files
!`git diff --name-only HEAD@{7.days.ago}..HEAD 2>/dev/null | grep -E "\.(py|ts|js|java|go)$" | head -20`

# Check for new files
!`git log --since="7 days ago" --diff-filter=A --name-only --pretty=format: | sort -u | head -20`
```

## Template Placeholder Replacement

Replace these placeholders during update:
- `{{PROJECT_NAME}}` - Current project name
- `{{DATE}}` - Current date
- `{{TECH_STACK}}` - Detected technologies
- `{{ER_DIAGRAM}}` - Generated ER diagram
- `{{ARCHITECTURE_DIAGRAM}}` - Generated architecture diagram
- `{{ENTITIES}}` - Extracted entity descriptions
- `{{COMPONENTS}}` - Extracted component descriptions

## Important Notes

- **Preserves custom content**: Doesn't blindly overwrite
- **Smart updates**: Only updates outdated sections
- **Diagram regeneration**: Auto-regenerates diagrams
- **Git-aware**: Uses git to detect what changed
- **Safe**: Asks before major changes
- **Incremental**: Can be run frequently

## Example Output

### All Docs Update
```
Documentation Update Complete ✓

Updated (4 docs):
  ✓ docs/architecture.md (new microservices added)
  ✓ docs/data-model.md (schema changed, ER diagram regenerated)
  ✓ docs/deployment.md (K8s config updated)
  ✓ docs/adr/ (meta-ADR updated)

Up to Date (2 docs):
  • docs/onboarding.md (no changes needed)
  • docs/security.md (no changes needed)

Created (1 doc):
  + docs/contributing.md (collaborative project detected)

Changes Summary:
  - 3 diagrams regenerated
  - 12 sections updated
  - 1 new document created
  - 0 manual sections affected
```

### Specific Doc Update
```
Architecture Documentation Updated ✓

File: docs/architecture.md

Changes:
  ✓ Added 2 new services (AuthService, NotificationService)
  ✓ Updated architecture diagram
  ✓ Documented new message queue integration
  ✓ Preserved custom deployment notes

Detected:
  - 5 services total
  - 3 databases (PostgreSQL, Redis, MongoDB)
  - 2 message queues (RabbitMQ, Kafka)
  - 8 external API integrations

Diagram: Updated with latest component relationships
```

### Category Update
```
Core Documentation Category Updated ✓

Updated (3 docs):
  ✓ docs/architecture.md
  ✓ docs/onboarding.md
  ✓ docs/adr/ (5 records)

Changes:
  - Architecture: Added microservices diagram
  - Onboarding: Updated setup instructions for new tooling
  - ADRs: Verified all properly formatted

Next Steps:
  1. Review updated documentation
  2. Consider updating diagrams: /docs:diagram arch
  3. Create new ADR for recent decision: /docs:adr "Decision Title"
```

## When to Run

Run this command:
- After major refactoring
- When database schema changes
- After adding new features or components
- Before onboarding new team members
- When documentation becomes stale
- As part of release process
- After infrastructure changes
- Before documentation reviews

## Best Practices

- **Run regularly**: Keep documentation current
- **Review changes**: Always review auto-generated updates
- **Preserve custom**: Keep manual additions safe
- **Commit with code**: Update docs alongside code changes
- **Be specific**: Use specific doc names for targeted updates
- **Bulk updates**: Use category updates for efficiency
- **Verify diagrams**: Check generated diagrams for accuracy

---

**Template Location**: `resources/templates/`
**Output Directory**: `docs/`
**Safe Mode**: Always preserves custom content
