---
name: git-release
description: Create semantic version releases with automated changelog generation
  from conventional commits. This skill should be used when users want to create a
  release, tag a version, generate a changelog, bump version numbers, or publish a
  GitHub release.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
---

# Git Release

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Release Manager

Create semantic version releases with automated changelog generation from conventional commits, version file updates, and GitHub release publishing.

## Quality Guidelines

**CRITICAL**: Release operations are high-consequence and irreversible once pushed:
1. **Verify every change** - Analyze actual commits, not assumptions
2. **Confirm version bump** - Ensure the detected semver bump matches the change scope
3. **Validate changelog** - Every entry must correspond to a real commit
4. **User approval required** - Always confirm before executing the release

## Workflow

### Phase 1: Collect Commits Since Last Tag

1. **Find the latest tag**:
 ```bash
 git describe --tags --abbrev=0 2>/dev/null || echo "none"
 ```
 - If no tags exist, collect all commits on the current branch
 - If a tag exists, collect commits since that tag

2. **Collect commits**:
 ```bash
 # With existing tag
 git log <last-tag>..HEAD --format="%H %s" --no-merges

 # Without existing tag (first release)
 git log --format="%H %s" --no-merges
 3. **Validate preconditions**:
 - Working tree is clean: `git status --porcelain`
 - On the expected branch (main/master or release branch)
 - Remote is up to date: `git fetch origin && git log HEAD..origin/$(git branch --show-current) --oneline`
 - If there are no commits since the last tag, abort with a clear message

### Phase 2: Auto-Detect Version Bump (Use Parallel Analysis for Large Changelogs)

For releases with >20 commits, spawn a parallel agent for analysis:

```
Agent - Commit Classification:
- prompt: "Classify these git commits by conventional commit type. For each commit, identify: type (feat/fix/docs/etc.), scope, whether it has a BREAKING CHANGE footer or ! marker. Return a structured summary with counts per type and list any breaking changes."
- agent-type: "general-purpose"
1. **Parse each commit** using conventional commit format:
 - Extract type: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
 - Extract scope (optional): text in parentheses after type
 - Detect breaking changes: `!` after type/scope OR `BREAKING CHANGE:` in commit body
 - For non-conventional commits, classify as `other`

2. **Determine version bump** following semver rules:
 - **MAJOR** (`X.0.0`): Any commit with breaking change indicator (`!` or `BREAKING CHANGE:` footer)
 - **MINOR** (`x.Y.0`): Any `feat` type commit (without breaking change)
 - **PATCH** (`x.y.Z`): Any `fix` type commit, or only non-feature changes (`docs`, `refactor`, `perf`, `chore`, etc.)
 - The highest-priority bump wins (major > minor > patch)

3. **Calculate new version**:
 - Parse last tag as semver (strip leading `v` if present)
 - If no previous tag, start from `0.1.0` (first feature release) or `1.0.0` if user specifies
 - Apply the detected bump
 - Respect `--major`, `--minor`, or `--patch` override from arguments

4. **Display version summary**:
 ```
 Current version: v1.2.3
 Detected bump: minor (2 features, 5 fixes, 3 chores)
 New version: v1.3.0

 Breaking changes: none
 ### Phase 3: Generate CHANGELOG Entry

1. **Read existing CHANGELOG.md** (if it exists) to understand the current format and preserve it

2. **Group commits by type** using this order and heading format:
 ```markdown
 ## [1.3.0](https://github.com/owner/repo/compare/v1.2.3...v1.3.0) (YYYY-MM-DD)

 ### Breaking Changes
 - **scope:** description ([hash](url))

 ### Features
 - **scope:** description ([hash](url))

 ### Bug Fixes
 - **scope:** description ([hash](url))

 ### Performance
 - **scope:** description ([hash](url))

 ### Documentation
 - **scope:** description ([hash](url))

 ### Other Changes
 - **scope:** description ([hash](url))
 Type-to-heading mapping:
 - Breaking changes (any type with `!` or `BREAKING CHANGE:`) → **Breaking Changes**
 - `feat` → **Features**
 - `fix` → **Bug Fixes**
 - `perf` → **Performance**
 - `docs` → **Documentation**
 - `refactor`, `style`, `test`, `build`, `ci`, `chore`, `revert`, `other` → **Other Changes**

 Only include sections that have entries. Omit empty sections.

3. **Generate comparison URL**:
 ```bash
 # Get remote URL for links
 gh repo view --json url -q .url 2>/dev/null || git remote get-url origin
 4. **Construct the changelog entry**:
 - Use short commit hashes (7 chars) linked to the full commit URL
 - If scope exists, bold it: `**scope:** description`
 - If no scope: just the description
 - Date format: `YYYY-MM-DD`

5. **Prepend to CHANGELOG.md**:
 - If CHANGELOG.md exists, insert after the `# Changelog` header (preserve existing entries)
 - If CHANGELOG.md does not exist, create it with a `# Changelog` header followed by the entry
 - Maintain a blank line between the header and first entry, and between entries

### Phase 4: User Approval

**CRITICAL**: Always present the full release plan and wait for explicit approval before executing.

1. **Display release summary**:
 ```
 === Release Summary ===

 Version: v1.2.3 → v1.3.0 (minor)
 Tag: v1.3.0
 Commits: 12 commits since v1.2.3
 Branch: main

 Changelog preview:
 ─────────────────────
 ## [1.3.0](...) (2025-01-15)

 ### Features
 - **auth:** add OAuth2 login support (abc1234)
 - **api:** add rate limiting endpoint (def5678)

 ### Bug Fixes
 - **api:** resolve null pointer in user endpoint (ghi9012)
 ─────────────────────

 Version files to update:
 - package.json (1.2.3 → 1.3.0)
 - pyproject.toml (1.2.3 → 1.3.0)

 Actions:
 1. Update version files
 2. Update CHANGELOG.md
 3. Create git commit: "chore(release): v1.3.0"
 4. Create git tag: v1.3.0
 5. Push commit and tag to origin
 6. Create GitHub release with changelog
 2. **Ask for confirmation** using interactive clarification:
 - Option 1: "Proceed with release" — Execute all actions
 - Option 2: "Change version" — Allow manual version override
 - Option 3: "Dry run only" — Show what would happen without executing
 - Option 4: "Abort" — Cancel the release

3. **Handle responses**:
 - **Proceed**: Continue to Phase 5
 - **Change version**: Ask for the desired version, recalculate, re-display summary
 - **Dry run**: Display the summary and all file changes that would be made, then stop
 - **Abort**: Exit cleanly with "Release cancelled."

### Phase 5: Execute Release

Execute all release actions in strict order. Stop immediately if any step fails.

1. **Update version files** (detect and update all that exist):
 - `package.json`: Update `"version": "x.y.z"` field
 - `package-lock.json`: Update `"version": "x.y.z"` at root level
 - `pyproject.toml`: Update `version = "x.y.z"` under `[project]` or `[tool.poetry]`
 - `Cargo.toml`: Update `version = "x.y.z"` under `[package]`
 - `VERSION` or `VERSION.txt`: Replace entire file content
 - `setup.cfg`: Update `version = x.y.z` under `[metadata]`
 - `build.gradle` / `build.gradle.kts`: Update `version = "x.y.z"`
 - Other version files: Skip unknown formats, notify user

2. **Write CHANGELOG.md**:
 - Prepend the generated changelog entry (from Phase 3)
 - Preserve all existing content

3. **Create release commit**:
 ```bash
 git add -A
 git commit -m "chore(release): v<new-version>"
 4. **Create annotated tag**:
 ```bash
 git tag -a v<new-version> -m "Release v<new-version>"
 5. **Push commit and tag**:
 ```bash
 git push origin $(git branch --show-current)
 git push origin v<new-version>
 6. **Create GitHub release** (unless `--no-github` flag is set):
 ```bash
 gh release create v<new-version> \
 --title "v<new-version>" \
 --notes-file /tmp/release-notes-<timestamp>.md \
 --latest
 ```
 - Use the changelog entry (without the `## [version]` header) as release notes
 - Write release notes to a temp file first to avoid shell escaping issues

7. **Display completion summary**:
 ```
 Release v1.3.0 completed successfully!

 - Commit: abc1234 chore(release): v1.3.0
 - Tag: v1.3.0
 - GitHub: https://github.com/owner/repo/releases/tag/v1.3.0
 - Changelog: Updated CHANGELOG.md
 ## Argument Parsing

Parse optional arguments from `command arguments`:
- `--major`: Force a major version bump (overrides auto-detection)
- `--minor`: Force a minor version bump (overrides auto-detection)
- `--patch`: Force a patch version bump (overrides auto-detection)
- `--dry-run` or `-n`: Show what would happen without making changes
- `--no-github`: Skip GitHub release creation (only local tag + changelog)

When force flags conflict (e.g., `--major --minor`), use the highest: major > minor > patch.

## Edge Cases

- **No conventional commits**: If commits don't follow conventional format, default to `patch` bump and list all commits under **Other Changes**
- **Pre-release versions** (e.g., `0.x.y`): Follow semver pre-1.0 rules — breaking changes bump minor, features bump minor, fixes bump patch
- **Monorepo**: If multiple `package.json` files exist, only update the root one. Warn the user about other version files found
- **Dirty working tree**: Abort with a clear message asking user to commit or stash changes first
- **No remote**: If `git push` fails due to no remote, skip push and GitHub release, warn user
- **Tag already exists**: If the computed tag already exists, abort and suggest using a force flag or choosing a different version

## Important Notes

- **Conventional Commits**: This skill works best with conventional commits (from the git-commit skill)
- **Tag Format**: Always uses `v` prefix (e.g., `v1.3.0`) unless existing tags use a different convention
- **CHANGELOG Format**: Follows [Keep a Changelog](https://keepachangelog.com/) conventions
- **Semver**: Strictly follows [Semantic Versioning 2.0.0](https://semver.org/)
- **No --no-verify**: Never skip git hooks during the release commit
- **Atomic Operations**: If any step in Phase 5 fails, clearly report which step failed and what manual cleanup may be needed

## Examples

```bash
# Auto-detect version bump from commits
git-release

# Force a major version bump
git-release --major

# Preview without making changes
git-release --dry-run

# Release without creating GitHub release
git-release --no-github

# Force minor bump, dry run
git-release --minor --dry-run
```
