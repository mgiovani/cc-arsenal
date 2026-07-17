---
name: git-release
description: Create semantic version releases with automated changelog generation
  from conventional commits, version file bumps (package.json, pyproject.toml,
  Cargo.toml, etc.), git tagging, and GitHub release publishing — for repos on a
  simple main-branch workflow (no release/hotfix branches). Use when users want
  to create a release, tag a version, generate a changelog, bump version numbers,
  cut a release, or publish a GitHub release. Not for release/hotfix branch
  topology or promoting one branch to another (use gitflow). Not for everyday
  conventional commit messages (use git-commit — this skill only creates the
  single release commit itself).
metadata:
  author: mgiovani
  version: 1.2.0
---

# Release Manager

Create semantic version releases with automated changelog generation from conventional commits, version file updates, and GitHub release publishing.

## Quality Guidelines

Release operations are high-consequence and irreversible once pushed:
1. **Verify every change** — analyze actual commits, not assumptions
2. **Confirm version bump** — the detected semver bump must match the change scope
3. **Validate changelog** — every entry must correspond to a real commit
4. **User approval required** — confirm before executing anything in Phase 5

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
 ```

3. **Validate preconditions**:
 - Working tree is clean: `git status --porcelain`
 - On the expected branch (main/master or release branch)
 - Remote is up to date: `git fetch origin && git log HEAD..origin/$(git branch --show-current) --oneline`
 - If there are no commits since the last tag, abort with a clear message

### Phase 2: Auto-Detect Version Bump

1. **Parse each commit** using conventional commit format:
 - Extract type: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
 - Extract scope (optional): text in parentheses after type
 - Detect breaking changes: `!` after type/scope OR `BREAKING CHANGE:` in commit body
 - For non-conventional commits, classify as `other`

 This is plain regex/string parsing over commit subjects — do it inline regardless of commit count, no agent needed.

2. **Determine version bump**: load `references/semver-guide.md` for the full commit-type → bump mapping and pre-1.0 rules. The highest-priority bump wins (major > minor > patch).

3. **Calculate new version**:
 - Parse last tag as semver (strip leading `v` if present)
 - If no previous tag, start from `0.1.0` (first feature release) or `1.0.0` if user specifies
 - Apply the detected bump
 - Respect `--major`, `--minor`, or `--patch` override from arguments

4. **Display version summary** — the counts must reflect commits you actually parsed in step 1, never estimated:
 ```
 Current version: v1.2.3
 Detected bump: minor (2 features, 5 fixes, 3 chores)
 New version: v1.3.0

 Breaking changes: none
 ```

### Phase 3: Build the CHANGELOG Entry

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
 ```

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
 gh repo view --json url -q .url 2>/dev/null || git remote get-url origin
 ```

4. **Construct the changelog entry**:
 - Use short commit hashes (7 chars) linked to the full commit URL
 - If scope exists, bold it: `**scope:** description`
 - If no scope: just the description
 - Date format: `YYYY-MM-DD`

5. **Insertion logic** (defines the mechanics only — nothing is written to disk yet, so the Phase 4 preview and a later abort both stay side-effect-free):
 - If CHANGELOG.md exists, insert the entry after the `# Changelog` header, preserving existing entries below it
 - If CHANGELOG.md does not exist, this entry becomes the file's first entry under a new `# Changelog` header
 - Maintain a blank line between the header and first entry, and between entries
 - The actual file write happens in Phase 5 step 2, or Phase 3b step 2 for changelog-only mode — both reuse this same logic

6. **Verify the write** (same call sites as step 5): after writing the file, re-read it and confirm the new version heading (`## [<new-version>]`) is present and that at least one section under it has a real bullet line, not just an empty `### Heading` with nothing below. A narrated changelog is not evidence the write succeeded — check the file on disk, e.g.:
 ```bash
 grep -A2 "## \[<new-version>\]" CHANGELOG.md
 ```
 If the heading is missing, or every section under it is empty, abort before creating the release commit: "CHANGELOG.md write produced empty sections — release aborted, no commit created." Do not proceed to Phase 5 step 3 (or, in changelog-only mode, report success) on a failed verification.

### Phase 3b: Changelog-Only Mode (if `--changelog-only`)

When `--changelog-only` is passed, skip Phases 4-6 entirely:

1. Run Phases 1-3 normally (collect commits, detect version bump, build the changelog entry)
2. Write CHANGELOG.md using the Phase 3 step 5 insertion logic, including its step 6 verification — abort here on a failed verification, do not report success
3. Display the updated changelog entry to the user
4. Stop here — no tag, version bump, commit, or GitHub release

Use case: draft a changelog before deciding on a release, or maintain a running changelog during development.

```bash
# Example output for --changelog-only
git-release --changelog-only
# → Scans commits since v1.2.3
# → Writes changelog entry to CHANGELOG.md
# → Reports: "CHANGELOG.md updated with 8 commits. No tag or release created."
```

### Phase 4: User Approval

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
 ```

2. **If `--dry-run` (or `-n`) was passed**: stop here. The summary above already shows everything that would happen — this flag is the only dry-run entry point, so no separate "preview" option is offered below.

3. **Otherwise, ask for confirmation**:
 - "Proceed with release" — continue to Phase 5
 - "Change version" — ask for the desired version, recalculate, re-display the summary
 - "Abort" — exit cleanly with "Release cancelled."

### Phase 5: Execute Release

Execute all release actions in strict order. Stop immediately if any step fails and report which step failed and what manual cleanup may be needed.

1. **Update version files** (detect and update all that exist):
 - `package.json`: Update `"version": "x.y.z"` field
 - `package-lock.json`: Update `"version": "x.y.z"` at root level
 - `pyproject.toml`: Update `version = "x.y.z"` under `[project]` or `[tool.poetry]`
 - `Cargo.toml`: Update `version = "x.y.z"` under `[package]`
 - `VERSION` or `VERSION.txt`: Replace entire file content
 - `setup.cfg`: Update `version = x.y.z` under `[metadata]`
 - `build.gradle` / `build.gradle.kts`: Update `version = "x.y.z"`
 - Other version files: Skip unknown formats, notify user

2. **Write CHANGELOG.md** using the Phase 3 step 5 insertion logic, including its step 6 verification — abort before step 3 below if verification fails.

3. **Create release commit**:
 ```bash
 git add -A
 git commit -m "chore(release): v<new-version>"
 ```

4. **Create annotated tag**:
 ```bash
 git tag -a v<new-version> -m "Release v<new-version>"
 ```

5. **Push commit and tag**:
 ```bash
 git push origin $(git branch --show-current)
 git push origin v<new-version>
 ```

6. **Create GitHub release** (unless `--no-github` flag is set):
 ```bash
 notes_file=$(mktemp -t release-notes)
 # write the changelog entry (without the "## [version]" header) to $notes_file
 gh release create v<new-version> \
   --title "v<new-version>" \
   --notes-file "$notes_file" \
   --latest
 rm -f "$notes_file"
 ```
 A fixed path (e.g. `/tmp/release-notes.md`) can collide across concurrent or repeated runs — `mktemp` guarantees a unique file.

7. **Display completion summary**:
 ```
 Release v1.3.0 completed successfully!

 - Commit: abc1234 chore(release): v1.3.0
 - Tag: v1.3.0
 - GitHub: https://github.com/owner/repo/releases/tag/v1.3.0
 - Changelog: Updated CHANGELOG.md
 ```

## Argument Parsing

Parse optional arguments from `command arguments`:
- `--major`: Force a major version bump (overrides auto-detection)
- `--minor`: Force a minor version bump (overrides auto-detection)
- `--patch`: Force a patch version bump (overrides auto-detection)
- `--dry-run` or `-n`: Show what would happen without making changes (see Phase 4 step 2 — the single dry-run entry point)
- `--no-github`: Skip GitHub release creation (only local tag + changelog)
- `--changelog-only`: Generate/update CHANGELOG.md only — skip tagging, version bumps, and GitHub release

When force flags conflict (e.g., `--major --minor`), use the highest: major > minor > patch.

## Edge Cases

- **No conventional commits**: If commits don't follow conventional format, default to `patch` bump and list all commits under **Other Changes**
- **Pre-release versions** (e.g., `0.x.y`): Follow semver pre-1.0 rules — breaking changes bump minor, features bump minor, fixes bump patch
- **Monorepo**: If multiple `package.json` files exist, only update the root one. Warn the user about other version files found
- **Dirty working tree**: Abort with a clear message asking the user to commit or stash changes first
- **No remote**: If `git push` fails due to no remote, skip push and GitHub release, warn the user
- **Tag already exists**: If the computed tag already exists, abort and suggest a force flag or a different version
- **CHANGELOG write verification fails**: If the re-read in Phase 3 step 6 shows a missing heading or empty sections, abort before the release commit — never commit a changelog write you haven't confirmed on disk

## Important Notes

- **Conventional Commits**: Works best with conventional commits (see the git-commit skill)
- **Tag Format**: Always uses `v` prefix (e.g., `v1.3.0`) unless existing tags use a different convention
- **CHANGELOG Format**: Follows [Keep a Changelog](https://keepachangelog.com/) conventions
- **Semver**: Follows [Semantic Versioning 2.0.0](https://semver.org/)
- **Never skip hooks**: Never pass `--no-verify` on the release commit
- **No inline execution**: Nothing in Phase 1-4 writes to the working tree — the first mutation is Phase 5 step 1, after approval

## Examples

```bash
# Auto-detect version bump from commits
git-release

# Force a major version bump
git-release --major

# Preview without making changes
git-release --dry-run

# Release without creating a GitHub release
git-release --no-github

# Force minor bump, dry run
git-release --minor --dry-run

# Update CHANGELOG.md only (no tag or release)
git-release --changelog-only
```
