# Verification Patterns

Detailed bash verification commands and patterns for documentation quality checking.

## Section-Level Verification (Single Document)

When checking ONE document, spawn subagents for each logical section:

```
Example: Checking docs/architecture.md

First, read the document and identify sections with verifiable claims:

Agent 1 - Verify Components:
- prompt: "Check the 'Components' section of docs/architecture.md. For EACH component name, search the codebase to verify it exists. Return: component_name -> exists (true/false) with evidence."
- subagent_type: "Explore"

Agent 2 - Verify Counts:
- prompt: "Find all numeric claims in docs/architecture.md (e.g., '5 services', '3 databases'). For each, run actual counts with find/glob. Return: claimed_count vs actual_count."
- subagent_type: "Explore"

Agent 3 - Verify Diagrams:
- prompt: "Extract all entities from Mermaid diagrams in docs/architecture.md. For each entity, verify it exists in the codebase. Return list of real vs hallucinated diagram elements."
- subagent_type: "Explore"

Agent 4 - Verify File References:
- prompt: "Find all file path references in docs/architecture.md. Check if each referenced file exists. Return: path -> exists (true/false)."
- subagent_type: "Explore"

Merge results into comprehensive verification report.
```

## Missing Documentation Detection

```bash
# Check for expected docs
!`ls -1 docs/ 2>/dev/null | grep -E "architecture|onboarding|data-model|deployment"`

# Check for ADRs
!`ls -1 docs/adr/*.md 2>/dev/null | wc -l`

# Check for RFCs
!`ls -1 docs/rfc/*.md 2>/dev/null | wc -l`
```

## Stale Documentation Detection

```bash
# Get last modification date of docs
!`find docs -name "*.md" -exec stat -f "%Sm %N" -t "%Y-%m-%d" {} \; 2>/dev/null || find docs -name "*.md" -exec stat -c "%y %n" {} \;`

# Get recent code changes
!`git log --since="30 days ago" --name-only --pretty=format: | sort -u | grep -v "^$" | head -30`
```

## Freshness Check Commands

```bash
# Check when files were last modified
!`git log -1 --format="%ai" -- docs/architecture.md 2>/dev/null`

# Check recent changes to codebase
!`git log --since="7 days ago" --oneline --name-only | head -50`
```

## Placeholder Check

```bash
# Find unreplaced placeholders
!`grep -r "{{.*}}" docs/ --include="*.md" 2>/dev/null`
```

## Broken Links Check

```bash
# Find markdown links
!`grep -r "\[.*\](" docs/ --include="*.md" -h | grep -o "\[.*\](.*)" | head -20`
```

## Hallucination Report Format

Include a dedicated section for detected hallucinations:
```
Hallucinations Detected:

docs/architecture.md:
  - Line 45: Claims "6 microservices" but only 3 found
  - Line 78: References "AuthService" which doesn't exist
  - Line 102: Diagram shows "Redis" but no Redis config found

docs/data-model.md:
  - Line 23: Claims "User has many Orders" but no Order model exists
  - Line 56: ER diagram shows "Payment" table not in schema

Verification commands used:
  - find . -name "*service*" -type f | wc -l -> 3 (not 6)
  - grep -r "class AuthService" . -> no results
  - find . -name "*redis*" -o -name "*.redis.*" -> no results
```

## Inferring Categories from What's Present

Don't check against a fixed list of doc names — group by what the repo actually has, then verify each group against what the codebase implies it should contain.

```
For each file found in docs/ (and docs/adr/, docs/rfc/):
  - Bucket it by what it's about (infer from filename + a quick skim), e.g.
    architecture.md / onboarding.md / adr/*.md -> architecture & process docs
    data-model.md / schema docs -> data docs
    deployment.md / docker/*.md -> infrastructure docs
  - For each bucket, cross-check against the detected stack:
    - Data docs: does a schema/migration directory exist? Do the described
      models match real model files?
    - Infrastructure docs: does a Dockerfile/compose file/k8s manifest exist
      that the doc should describe?
    - Architecture docs: do the described components/services exist?
  - A category with real signal in the codebase (schema files, Dockerfiles,
    service directories) but no matching doc is a Missing finding, not a
    silent skip.
```

This lets a repo with unconventional doc names (e.g. `SCHEMA.md` instead of
`data-model.md`) still get checked, and never invents a category — like
"infrastructure" — for a repo that has no Docker/deploy config to check
against.
