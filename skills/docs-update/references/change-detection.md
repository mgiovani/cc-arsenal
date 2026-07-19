# Change Detection

Fallback commands for detecting codebase changes when the primary freshness check
(SKILL.md Phase 2) can't run — no `.git`, the doc is untracked, or it's a first commit.
Replace `<doc-path>` with the actual resolved path from Phase 1 (e.g. `docs/architecture.md`)
— never hardcode a specific document here, this file backs every doc type.

## General Change Detection

```bash
# Find modified source files in the last 7 days
git diff --name-only HEAD@{7.days.ago}..HEAD 2>/dev/null | grep -E "\.(py|ts|js|java|go)$" | head -20

# Check for new files added in the last 7 days
git log --since="7 days ago" --diff-filter=A --name-only --pretty=format: | sort -u | head -20
```

## Per-Document Freshness Check

```bash
# When was this specific doc last modified? (empty output = untracked or doesn't exist yet)
git log -1 --format="%ai" -- <doc-path> 2>/dev/null

# No git history for the doc at all — fall back to a fixed lookback window
git log --since="7 days ago" --oneline --name-only | head -50
```

## Technology Stack Detection

```bash
# Check for language/framework
find . -name "package.json" -o -name "pyproject.toml" -o -name "go.mod" -o -name "Cargo.toml" | head -5

# Check for database
find . -name "*models.py" -o -name "*schema.prisma" -o -name "*entity.ts" | head -5

# Check for infrastructure
find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name "*.k8s.yaml" | head -5
```

## Load Templates

Template location: `../docs-init/assets/templates/` (shared with docs-init — see SKILL.md
Phase 4 for the standalone-install fallback). Load the template matching the doc being
updated for consistent formatting across creation and updates.
