---
name: review-code
description: >-
  Runs one adaptive multi-agent code review of a PR, commit, or the whole codebase.
  Always covers six core dimensions (correctness, performance, code style, test coverage,
  error handling, simplicity/over-engineering) plus architecture and design patterns, then
  adds security, dependency, deep-performance, and UI/motion lanes when the change touches
  those areas. Critical and Major findings are adversarially verified before the severity-ranked
  report with file:line findings and fixes goes out in chat. Use when the user wants a thorough
  review, asks to review a PR or diff, or wants over-engineered code flagged. Analysis only:
  never edits code, commits, or applies fixes, and posts to GitHub only when explicitly asked.
  Not for a standalone security audit (use review-security), a standalone dependency audit
  (use review-deps), a standalone performance investigation (use review-perf), or a standalone
  UX/design critique (use review-design).
metadata:
  summary: "Adaptive multi-agent code review: core dimensions plus architecture, security, deps, perf and design lanes picked from the diff, with adversarial verification"
  author: mgiovani
  version: 2.0.0
---

# Code Review

One review, adaptive lanes. The six core dimensions and the architecture lane always run. Security, deps, deep-performance and design/motion lanes join when the diff touches their area. Critical and Major findings are then attacked by a verifier before they reach the report.

Analysis only. Never edit code, commit, apply fixes, or run anything that mutates the repo. The report goes to chat. Run `gh` write commands (reviews, comments) only when the user explicitly asks to post.

## Core rules

- Every finding cites a `file:line` you read, pointing at the offending statement itself, not the block around it. No hypothetical issues, no estimated counts.
- Review the diff, not the uncommitted working tree. Findings on changed lines are in-diff; findings on untouched lines of touched files are `preexisting`.
- Project rules (AGENTS.md, CLAUDE.md, `.claude/skills/*`) are the style standard. A violation is a finding. Personal preference is not.
- User context such as "another session is fixing X" is information, not an exclusion, unless the user says to exclude it.
- Strict by default: report every smell and rule violation, Nit included. Nothing is silently passed.
- Every subagent call sets `model` explicitly: review, research and verify use `sonnet`, planning uses `opus`. Never leave it inherited, never use `haiku`.

## Workflow

Copy this checklist and tick each step. Do not start a step before the previous gate holds.

```
- [ ] 0. Scope: diff retrieved, file list and hunk ranges known            (gate: non-empty diff)
- [ ] 1. Discovery: stack and project rules extracted into a numbered list  (gate: list written)
- [ ] 2. Lane selection: lanes chosen with a one-line reason each           (gate: printed)
- [ ] 3. Fan-out: all lane agents launched in ONE parallel batch            (gate: all findings files written)
- [ ] 4. Consolidate: merged, deduplicated, routed to the right dimension
- [ ] 5. Verify: Critical/Major findings attacked, REJECTED dropped         (gate: every survivor has a verdict)
- [ ] 6. Report: written in chat from the template
- [ ] 7. Post: ONLY if the user explicitly asked
```

### 0. Scope

Parse arguments: a PR number (`123`, `#123`), a commit SHA, `--all` or none (whole codebase), and `--focus <value>`.

```bash
gh pr diff <pr>                                   # PR
git fetch origin <base> && git diff origin/<base>...HEAD   # fallback when gh fails (e.g. diff too large)
git show <sha>                                    # commit
```

Create a scratch dir with `mktemp -d` (never inside the repo) and save the diff to `<scratch>/pr.diff`. Take the changed-file list from the same diff. From each hunk header `@@ -a,b +c,d @@`, the new-side range is lines `c` to `c+d-1`; anything outside those ranges is pre-existing. Re-reviewing after fixes is just a rerun: the diff is re-derived.

### 1. Discovery

Read the root and nested AGENTS.md / CLAUDE.md and `.claude/skills/*`. Turn every rule into a numbered checklist (comment policy, strict typing, file-size limits, empty `__init__`, no manual memo under React Compiler, and so on). This list goes into every agent prompt. Note the languages, frameworks and test setup.

### 2. Lane selection

| Lane | Findings file | Runs when the change touches | Prefix |
|------|---------------|------------------------------|--------|
| core (agents 1-6) | `core-<prefix>.json` per agent (`core-cl`, `core-pf`, `core-cs`, `core-tc`, `core-eh`, `core-oe`) | always | CL PF CS TC EH OE |
| architecture (agent 7) | `architecture.json` | always | AP |
| security-fe | `security-fe.json` | UI, client auth, storage, cookies, CSP | SEC |
| security-be | `security-be.json` | server code, auth, config, IaC, CI | SEC |
| deps | `deps.json` | a manifest or lockfile | DEP |
| perf-deep | `perf-deep.json` | DB, queries, hot loops, bundle or render paths | PF |
| design-motion | `design-motion.json` | UI, CSS, component files | DM |

With `--all`, run every lane that applies to the repo. With `--focus`, run only the matching lane. Print the chosen lanes with a one-line reason each, and a reason for each skipped lane. Lane prompts, sibling composition and installed-skill detection: [references/lanes.md](references/lanes.md). Architecture lens: [references/architecture-patterns.md](references/architecture-patterns.md).

### 3. Fan-out

Launch every selected lane in one parallel batch, explicit `model` on each call. Each agent gets the rule checklist, the diff scope, and the finding contract, and writes `<scratch>/findings/<lane>.json` as `{"lane": "...", "findings": [...]}`. Core agent prompts, grep patterns and the finding shape: [references/agent-prompts.md](references/agent-prompts.md).

Each agent: grep for patterns in scope, read each match to confirm it is real, quote 5-10 lines with `file:line`, explain why it matters, classify severity, give a concrete fix.

| Severity | Meaning |
|----------|---------|
| Critical | Data loss, crashes, security holes, incorrect business logic |
| Major | Significant reliability or performance harm, real maintainability risk |
| Minor | Readability, consistency, small inefficiencies |
| Nit | Cosmetic or optional |

Gate: a lane whose findings file is missing or invalid is re-run once. If it fails again, the report names the lane as failed instead of silently omitting it.

Sequential fallback: with no subagent tool, run the same lanes as sequential Grep+Read passes in table order, the verification pass last. Same prompts, same findings files, same gates.

### 4. Consolidate

Run `uv run <skill-dir>/scripts/merge_findings.py --findings <scratch>/findings --diff <scratch>/pr.diff --out <scratch>` to dedupe (same path, lines within 2, same dimension or same title). If it is unavailable, merge by hand with the same rules: one primary finding, the other agents' versions in a collapsed `<details>` block. Move praise and "resolved" notes out of findings into Positive Observations. Route a finding to its true dimension: an over-engineered function that is also buggy is a `CL-` finding, not `OE-`. If Agent 6 and Agent 7 disagree on the same code, keep the OE removal and drop the pattern suggestion.

### 5. Verify

Launch one adversarial verifier (`sonnet`) per batch of Critical/Major findings. It tries to disprove each, may run targeted read-only checks, and returns CONFIRMED / PLAUSIBLE / REJECTED with a corrected severity and a reason. Write each verdict, corrected severity and a new `reason` field back into the matching findings in `<scratch>/findings/*.json`, then re-run the merge script; the report and step 7 use that output (it drops REJECTED and renders `Verification: <VERDICT> (<reason>)`). A bug the user says they observed keeps its severity. Prompt, schema and rules: [references/verification.md](references/verification.md).

### 6. Report

Write the report in chat following [references/report-template.md](references/report-template.md): lane-selection line, executive summary, severity and verdict statistics, findings by dimension, pre-existing bucket, prioritized actions, positive observations. Zero surviving findings still produce the report (lanes line, statistics, positive observations); with posting requested, post a body-only review.

### 7. Post (explicit request only)

Only when the user asks ("post it on the PR", `--comment`). Run the merge script, show a preview with the count of inline comments versus body items, then post ONE review. Flow, anchoring rules and comment style: [references/github-review.md](references/github-review.md). Without an explicit request, run no `gh` write command.

## Usage

```bash
review-code 123                       # PR, lanes chosen from the diff
review-code abc123def                 # commit
review-code --all                     # whole codebase, every applicable lane
review-code 123 --focus security      # narrow to one lane
review-code 123 --comment             # also post the review to the PR
```

## Focus options

`correctness`, `performance`, `style`, `tests` and `errors` run the matching core agent, while `architecture`, `deps` and `design` (design-motion) run their own lane. `security` runs security-fe and security-be as applicable, and without `--focus` the lanes stay adaptive.

## Simplicity lens (Agent 6)

LLM-written code over-engineers: interfaces with one implementation, factories for one product, forwarding wrappers. None is a bug, so the other agents miss it. Agent 6 flags it as `OE-` (Minor/Nit by default). Prompt and tags: [references/agent-prompts.md](references/agent-prompts.md#agent-6---simplicity--over-engineering).

## Reference files

- [references/agent-prompts.md](references/agent-prompts.md): core agents 1-6, grep patterns, finding shape
- [references/architecture-patterns.md](references/architecture-patterns.md): agent 7, pain-to-pattern table, over-engineering counter-check
- [references/lanes.md](references/lanes.md): conditional lanes and the sibling skills they compose
- [references/verification.md](references/verification.md): verifier prompt, verdicts, drop rules
- [references/report-template.md](references/report-template.md): report layout
- [references/github-review.md](references/github-review.md): opt-in posting flow and comment style
- `scripts/merge_findings.py`: dedupe, drop REJECTED, validate RIGHT-side anchors, emit `merged.json` and `review-payload.json` (`--self-test` available)

## Limitations

- Static, pattern-based analysis: it cannot measure runtime impact, and some findings may be intentional design.
- Grep patterns lean toward C-like and Python syntax; adapt them for other languages.
- Verification may run read-only checks but never the full test suite or benchmarks.
- Does not modify code. For a deep standalone security, dependency, performance or design audit, use the matching sibling skill.
