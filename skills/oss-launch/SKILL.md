---
name: oss-launch
description: Takes a private side project from "done" to a public GitHub launch — pre-flight checks (confirm the repo is still private, scan for leaked secrets, verify a license exists), applies review-code findings, generates brand art (logo/hero via codex-imagegen or nanobanana), rewrites the README and repo description for discoverability, scrubs internal or AI-tooling mentions from code and docs (only after explicit confirmation of what to remove), optionally rewrites git history while the repo is still private, then flips the repo public with topics and description set. Use for "open source this", "get this repo ready to go public", "launch prep", "make this repo public", "prep this for launch", or "clean this up before I open source it". Not for PR/merge mechanics on an already-public repo (use ship) or cutting version releases (use git-release). Not for the actual image-generation call itself (use codex-imagegen or nanobanana directly) or a standalone secrets/license audit with no launch intent (use env-setup).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: "[--skip-brand] [--rewrite-history]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git *), Bash(gh *), Task, Skill, TodoWrite, AskUserQuestion
---

# OSS Launch

Take a private side project from "done" to a public GitHub launch in seven staged gates: pre-flight, review, brand, README, mention scrub, history rewrite (optional, hard-gated), public flip. Like `ship`, every stage reports the real command it ran and the run stops at the first gate that isn't met — never estimate a result, never skip a gate silently.

Track progress with `TodoWrite` (one line per stage) so the user sees where the launch train is if a gate stops it.

## The stages

| # | Stage | Gate |
|---|-------|------|
| 1 | Pre-flight | Repo is private; no leaked secrets; a license exists |
| 2 | Review | No unresolved Critical/High findings |
| 3 | Brand | (optional) logo/hero generated or reused |
| 4 | README + description | Value-prop-first README, topics set |
| 5 | Mention scrub | User confirms exactly what gets removed |
| 6 | History rewrite | Private only, ever-public check, explicit confirmation this turn |
| 7 | Public flip | Every earlier stage passed |

## Stage 1: Pre-flight

- `gh repo view --json isPrivate,licenseInfo,forkCount,stargazerCount -q .` — record `isPrivate`; this is the launch's core assumption and Stage 6 rechecks it independently.
- Secrets scan: run the same check `env-setup`'s Phase 6 does — grep tracked files and `.env`/git history for key/secret/password/token patterns (see that skill's `references/scan-patterns.md` if you need the full pattern set). **Any hit stops the whole train** — report the finding as `file:line` only, never the matched value, and go no further.
- License: check for `LICENSE`/`LICENSE.md`/`COPYING` at the repo root. Missing license is not an auto-fill — ask the user which license they want (MIT, Apache-2.0, etc.) before continuing; don't pick one for them.

## Stage 2: Review

Invoke the `review-code` skill (via `Skill`, or a `Task`/`Explore`→`sonnet` subagent if that's unavailable) against the default branch. Any **Critical/High** finding stops the train — report it and let the user decide (fix and re-run, or explicitly accept the risk). Medium/Low findings are reported but don't block.

## Stage 3: Brand

Check first whether the repo already has a logo/hero asset (`ls` common paths: `assets/`, `docs/`, `.github/`, README image references) — reuse before generating. If none exists and the user wants one, invoke `codex-imagegen` (falls back to `nanobanana` if that skill or its prerequisites aren't available) to generate a logo/hero, then wire the resulting path into the README. Skip this stage entirely (report `SKIPPED: not requested`) if the user didn't ask for art and none is needed for the README rewrite.

## Stage 4: README + description

Rewrite (don't append to) the README so it leads with the value proposition, not a feature dump. Full checklist (badges, install snippet, demo asset, topics/keyword sourcing) is in [references/readme-checklist.md](references/readme-checklist.md) — load it before writing the file. Draw the topics/keywords and repo description from what the codebase actually is (`package.json`/`pyproject.toml`/`Cargo.toml` name+description, detected language/framework) — never invent a tagline the project doesn't back up.

## Stage 5: Mention scrub

Grep for internal-tooling and AI-assistant mentions across tracked files *and* commit messages — pattern list in [references/mention-scrub-patterns.md](references/mention-scrub-patterns.md), load it before scanning.

- Present the **full match list** (file:line or commit ref) to the user, even if it's empty — don't summarize it away.
- Distinguish a leftover-scaffolding mention (a "Generated with Claude Code" footer, a `Co-Authored-By:` trailer, a stray internal Slack/Jira reference) from a mention that's part of the product's actual described functionality (e.g. a comment explaining a real Claude API integration the product ships) — flag both but don't frame them identically.
- **Never silently edit or remove anything here.** Ask which matches to remove; apply only what the user confirms.

## Stage 6: History rewrite (optional, hard gate)

Only reachable if the user explicitly asks for it (a `--rewrite-history` flag or plain-language request). This is the one stage in this skill allowed to force-push, and only under every one of these conditions:

1. **Re-check visibility right now** with a fresh `gh repo view --json isPrivate` — don't reuse Stage 1's result, time has passed. `isPrivate: false` → **refuse outright**, explain that a public repo may already have been cloned and rewriting shared history would break those clones. Stop here; no backup, no rewrite command, nothing mutates.
2. **"Ever public" is not directly queryable.** Treat `forkCount > 0` or `stargazerCount > 0` from the same `gh repo view` call as evidence the repo may have been cloned or seen while public — refuse unless the user explicitly overrides after being shown those numbers.
3. **Explicit confirmation in this turn.** A general "yes, launch it" earlier in the conversation does not count — ask specifically, in this turn, whether to proceed with an irreversible history rewrite, and wait for a direct yes.
4. **Back up first.** Full procedure (backup ref/bundle, `git filter-repo` usage, verification, the narrow force-push exception) is in [references/history-rewrite.md](references/history-rewrite.md) — load it only once conditions 1–3 are satisfied, never before.

If any condition fails, report the refusal and move on — don't block the rest of the launch on a history rewrite the user can always do later while still private.

## Stage 7: Public flip

Only run once every earlier stage that applied is reported as passed (or explicitly skipped with a reason). Confirm with the user one last time — this is the point of no return for "nobody's cloned it yet."

```bash
gh repo edit --visibility public --accept-visibility-change-consequences
gh repo edit --description "<real value-prop, matches the README>" --add-topic <topic1> --add-topic <topic2>
```

Never invent topics or a description that don't match what Stage 4 actually wrote.

## Reporting

End every run — stopped or completed — with a stage table: `# | Stage | Command | Result`, one row per stage above, in order. `Command` is the literal command (or skill invocation) actually run; `Result` is its actual output or exit status. A stage not reached gets `Command: —`, `Result: SKIPPED: <reason>`. Never fill a row from what a stage "should" produce — only from a command that actually ran this session.

### Example: stopped at pre-flight (secrets found)

```
OSS Launch stopped at stage 1/7 — pre-flight.

| # | Stage          | Command                                   | Result                                    |
|---|-----------------|--------------------------------------------|---------------------------------------------|
| 1 | Pre-flight      | grep -iE "(secret|api_key|token)\s*=" .env | .env:14 — possible leaked key (STRIPE_SECRET_KEY) — BLOCKED |
| 2 | Review          | —                                          | SKIPPED: not reached                        |
| 3 | Brand           | —                                          | SKIPPED: not reached                        |
| 4 | README          | —                                          | SKIPPED: not reached                        |
| 5 | Mention scrub   | —                                          | SKIPPED: not reached                        |
| 6 | History rewrite | —                                          | SKIPPED: not reached                        |
| 7 | Public flip     | —                                          | SKIPPED: not reached                        |

Rotate the key and remove it from .env before this can proceed — I won't scan further or touch anything else until the secret is out.
```

### Example: refused history rewrite on an already-public repo

```
OSS Launch: history-rewrite request refused.

| # | Stage          | Command                                    | Result                                       |
|---|-----------------|----------------------------------------------|------------------------------------------------|
| 6 | History rewrite | gh repo view --json isPrivate,forkCount,stargazerCount | isPrivate: false, forkCount: 2, stargazerCount: 5 — already public, refused |

This repo is already public and has 2 forks — rewriting history now would break those clones. I didn't touch git, and nothing else ran. If there's exposed data, rotate/redact it going forward instead, or say so if you want me to proceed anyway knowing the forks will break.
```

### Example: full launch, completed

```
OSS Launch complete — repo is now public.

| # | Stage          | Command                                                        | Result                                  |
|---|-----------------|-------------------------------------------------------------------|--------------------------------------------|
| 1 | Pre-flight      | gh repo view --json isPrivate,licenseInfo; secrets grep            | private, MIT license present, 0 secrets    |
| 2 | Review          | Skill: review-code                                                 | 0 Critical/High, 1 Low (non-blocking)      |
| 3 | Brand           | Skill: codex-imagegen (hero.png)                                   | assets/hero.png generated, wired into README |
| 4 | README          | Rewrote README.md                                                   | value-prop lead, install, demo gif, badges |
| 5 | Mention scrub   | grep AI-tooling/internal patterns                                    | 1 match (README credit line) — user confirmed removal |
| 6 | History rewrite | —                                                                    | SKIPPED: not requested                     |
| 7 | Public flip     | gh repo edit --visibility public --accept-visibility-change-consequences | ✓ now public, topics set                |
```
