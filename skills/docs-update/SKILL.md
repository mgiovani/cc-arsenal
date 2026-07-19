---
name: docs-update
description: Refresh existing docs (architecture, onboarding, data-model, deployment,
  security, contributing) so they match the current codebase, verifying every claim
  against real code instead of guessing. Use when the user says docs are stale, asks
  to sync docs with recent code changes, update a specific doc file, or update a whole
  category (core/data/infrastructure/development) after a refactor or schema change.
  Not for creating docs that don't exist yet (use docs-init) or scoring/auditing doc
  health without editing (use docs-check).
metadata:
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: '[all|<doc-name>|category:<name>]'
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task, TodoWrite
context: fork
agent: general-purpose
---

# Update Documentation

Synchronize documentation with the current codebase state — one file, a category, or everything in `docs/`.

## Anti-Hallucination Guidelines

Every statement written must trace back to a file read or grepped this run:
1. Verify each claim before writing it — read the actual source, don't recall it
2. Get counts from `find`/`grep`, never estimate ("5 services" means 5 files were counted this run)
3. Delete claims about features that no longer exist rather than leaving them stale
4. After writing, re-read the diff and drop anything not backed by evidence gathered this run

## Workflow

### Phase 1: Resolve Scope

Parse the invocation argument:
- No argument or `all` — update every doc that exists in `docs/`
- `<doc-name>` (e.g. `architecture`) — resolve via the mapping below, update only that file
- `category:<name>` (`core`, `data`, `infrastructure`, `development`) — update every doc in that category

| Argument | File Path | Category |
|---|---|---|
| `architecture` | `docs/architecture.md` | core |
| `onboarding` | `docs/onboarding.md` | core |
| `data-model` | `docs/data-model.md` | data |
| `deployment` | `docs/deployment.md` | infrastructure |
| `security` | `docs/security.md` | infrastructure |
| `contributing` | `docs/contributing.md` | development |

**Existence check — stop before doing anything else if the target is missing.** This skill only updates docs that already exist; it never creates one.

- `all` or `category:<name>` — silently exclude any mapped path that isn't on disk (e.g. `find docs/*.md` and intersect with the category's paths); the run proceeds with whatever remains
- `<doc-name>` — resolve the path, then check it with `test -f <resolved-doc-path>` (or Read). If it does not exist, STOP the entire skill run right here: do not read further, do not run Phase 2-5, do not Write or Edit that path under any pretext (not as a "special case," not with a caveat about verified content). Tell the user the doc doesn't exist yet and point them to `docs-init`, which owns creation and the canonical templates. This is the final action for that run.

For a multi-doc run that passes the existence check, track progress with TodoWrite — one todo per document, marked `in_progress` while it's being worked and `completed` once written.

### Phase 2: Check Freshness

For each doc resolved in Phase 1 — using its actual path, not a fixed one — compare its last commit against source changes since:

```bash
git log --since="$(git log -1 --format=%ai -- <resolved-doc-path> 2>/dev/null || echo '30 days ago')" --oneline --name-only -- . ':!docs' | head -30
```

A doc whose last update predates relevant source changes is a candidate for this run. If git history is unavailable (no `.git`, doc untracked, first commit), fall back to the commands in [references/change-detection.md](references/change-detection.md) and note in the final report that freshness couldn't be determined from git.

### Phase 3: Verify Against the Codebase

**Single document**: read it fully, then grep the codebase for each claim it makes (component names, counts, file paths, tech stack). No subagent needed — one Explore pass funnels into one file write either way.

**Multiple documents** (`all` or `category` mode): spawn one subagent per document so verification runs concurrently — see [references/update-strategies.md](references/update-strategies.md) for the per-document-type checklist and prompt pattern. If no Task/subagent tool is available, run the same read-verify-write pass for each document sequentially instead.

### Phase 4: Write Updates

- Preserve manually added sections and any content that doesn't match the template structure — only touch parts backed by verified facts from Phase 3
- Templates are shared with docs-init: [`../docs-init/assets/templates/`](../docs-init/assets/templates/) relative to this skill's own directory (works when both skills are installed side by side, e.g. via the cc-arsenal plugin or `npx skills add`). If docs-init isn't installed alongside this skill, fetch the same templates from the [cc-arsenal repo](https://github.com/mgiovani/cc-arsenal/tree/main/skills/docs-init/assets/templates) instead of inventing structure
- Before filling placeholders, run `grep -oE '\{\{[A-Z_]+\}\}' <template-file>` to see the tokens that specific template actually uses — each template has its own set (architecture.md alone uses over a dozen), never assume a fixed list
- Regenerate diagrams whose depicted components/entities changed
- Remove claims Phase 3 could not verify
- If it's ambiguous whether a section is custom or auto-generated, ask before overwriting rather than guessing

### Phase 5: Report

List documents updated (with what changed and numbers pulled from Phase 3, e.g. "3 services found" not "several services"), skipped (already fresh), and not found (excluded from an `all`/`category` run because the file doesn't exist — mention docs-init, don't create it). This skill never reports a "created" doc; creation is docs-init's job.

## Example Output: All Docs Update

```
Documentation Update Complete

Updated (2 docs):
  docs/architecture.md (added AuthService, NotificationService — found via grep of src/services/)
  docs/data-model.md (schema changed, ER diagram regenerated from 6 models)

Up to Date (1 doc):
  docs/onboarding.md (no source changes since last update)

Skipped — could not verify (1 doc):
  docs/security.md (claims about SSO could not be confirmed in code, left as-is, flagged for manual review)
```

## Example Output: Specific Doc Update

```
Architecture Documentation Updated

File: docs/architecture.md

Changes:
  Added 2 new services (AuthService, NotificationService) — src/services/auth.py, src/services/notify.py
  Updated architecture diagram to include the new message queue integration
  Preserved custom "Deployment Notes" section (not touched)

Verified:
  5 services total (find src/services -name '*.py' | wc -l)
  3 databases: PostgreSQL, Redis, MongoDB (grep of config/database.yml)
```

## Example Output: Target Doc Doesn't Exist

```
docs/security.md doesn't exist yet — nothing to update.

This skill only refreshes existing docs. Run docs-init to create
docs/security.md from the canonical template first, then re-run
docs-update security to keep it in sync going forward.
```

No file was written and no other phase ran.

## Notes

- Never creates a doc that doesn't exist — a missing target stops the run and points to docs-init instead
- Preserves custom content by default — asks rather than overwrites when a section's status is unclear
- Git-aware: freshness comes from `git log`, not assumption
- Safe to run repeatedly (after refactors, schema changes, infra changes, or before onboarding/releases)
- For a full category, see [references/update-strategies.md](references/update-strategies.md) for the category-level output format and per-doc-type verification steps

## Additional Resources

- [references/update-strategies.md](references/update-strategies.md) — parallel subagent pattern, per-document-type checklist, category-update output format
- [references/change-detection.md](references/change-detection.md) — fallback change-detection commands when git history is unavailable
