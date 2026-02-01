# Change Detection

Commands for detecting codebase changes relevant to documentation updates.

## General Change Detection

```bash
# Check what changed since last doc update
!`git log --since="$(git log -1 --format=%ai docs/architecture.md 2>/dev/null || echo '30 days ago')" --oneline`

# Find modified source files
!`git diff --name-only HEAD@{7.days.ago}..HEAD 2>/dev/null | grep -E "\.(py|ts|js|java|go)$" | head -20`

# Check for new files
!`git log --since="7 days ago" --diff-filter=A --name-only --pretty=format: | sort -u | head -20`
```

## Per-Document Freshness Check

```bash
# Check when a specific doc was last modified
!`git log -1 --format="%ai" -- docs/architecture.md 2>/dev/null`

# Check recent changes to codebase since doc update
!`git log --since="$(git log -1 --format=%ai docs/architecture.md)" --oneline --name-only | head -30`

# Compare doc age with code age
!`git log --since="7 days ago" --oneline --name-only | head -50`
```

## Technology Stack Detection

```bash
# Check for language/framework
!`find . -name "package.json" -o -name "pyproject.toml" -o -name "go.mod" -o -name "Cargo.toml" | head -5`

# Check for database
!`find . -name "*models.py" -o -name "*schema.prisma" -o -name "*entity.ts" | head -5`

# Check for infrastructure
!`find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name "*.k8s.yaml" | head -5`
```

## Load Templates

Template location: `resources/templates/`

Load appropriate templates based on docs being updated. Use the same templates referenced in the init skill for consistent formatting across creation and updates.
