---
name: fix-bug
description: Fixes a bug through test-driven debugging — reproduces it with a failing
  test, locates the root cause with evidence (file:line), then applies the smallest
  fix that resolves it without refactoring unrelated code. Use when the user wants to
  fix a bug, debug an issue, resolve an error, or investigate a failing test. Not for
  building new functionality (use implement-feature) or restructuring working code
  with no bug involved (use refactor).
disable-model-invocation: false
argument-hint: "[bug_description_or_issue_id] [--branch name] [--interactive]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
---

# Bug Fix

Fix the bug described by the user (a plain description, an issue ID, or a failing
test name) using test-driven debugging: reproduce it, find the root cause with
evidence, apply the smallest fix, verify, commit.

## Anti-Hallucination Guidelines

A fix that "should work" but was never run against a failing test is a guess, not a fix:

1. **Reproduce first** — don't fix what you haven't seen fail.
2. **Test-driven** — write or locate a failing test before implementing the fix; confirm it actually fails.
3. **Verify root cause** — locate the bug with grep/read evidence (file path, line number), not intuition.
4. **Verify the fix** — run the full test suite; all tests must pass before calling the bug fixed.
5. **No invented fixes** — only implement solutions that address the demonstrated root cause.
6. **Reference real code** — never make claims about code you haven't read.

## Workflow Mode: Inline by Default

Most bugs are a single file, single root cause, fixable and verifiable in one sitting.
For those, run Phases 0–5 below yourself, in order, inline — no task chain, no
subagent fan-out. That's the default; don't create tasks unless the case below applies.

**Use a task chain instead** when the bug spans multiple files/components, the root
cause is unclear enough to need a dedicated analysis phase, or the fix will span
multiple sessions and needs progress tracking across them. In that case, before
Phase 0, create six tasks (Discovery, Reproduce & Analyze, Plan, Implement, Verify,
Commit) with a strict sequential chain — each `addBlockedBy` the one before it:

```
TaskCreate: { subject: "Phase 0: Discover project workflow", activeForm: "Discovering project workflow" }
TaskCreate: { subject: "Phase 1: Reproduce and analyze bug", activeForm: "Analyzing bug" }
TaskCreate: { subject: "Phase 2: Plan fix", activeForm: "Planning fix" }
TaskCreate: { subject: "Phase 3: Implement fix", activeForm: "Implementing fix" }
TaskCreate: { subject: "Phase 4: Verify quality", activeForm: "Verifying fix quality" }
TaskCreate: { subject: "Phase 5: Final commit", activeForm: "Creating final commit" }
TaskUpdate: { taskId: "2", addBlockedBy: ["1"] }
TaskUpdate: { taskId: "3", addBlockedBy: ["2"] }
TaskUpdate: { taskId: "4", addBlockedBy: ["3"] }
TaskUpdate: { taskId: "5", addBlockedBy: ["4"] }
TaskUpdate: { taskId: "6", addBlockedBy: ["5"] }
TaskUpdate: { taskId: "1", status: "in_progress" }
```

**Task lifecycle rule** (applies to every phase below when a chain exists — not
repeated per phase): mark that phase's task `in_progress` the moment you start it,
and `status: "completed"` immediately before moving to the next phase, then run
`TaskList` to confirm the next task unblocked.

**Portability**: no `Task`/`TaskCreate` tools in this environment? Always use the
inline path above — the phases are the methodology, the task tooling is just how
Claude Code tracks and parallelizes them in the multi-file case.

## Phase 0: Project Discovery

Discover the project's test, lint, and type-check commands before touching anything —
guessing wastes a cycle when the wrong command silently no-ops.

If the codebase is large or unfamiliar, offload this to an Explore subagent:

```
Task tool, Explore agent, model haiku:
"Discover the development workflow for this project:
 1. Read CLAUDE.md/AGENTS.md if present — extract debugging/testing conventions.
 2. Check task runners: Makefile, justfile, package.json scripts, pyproject.toml.
 3. Identify the test command, and how to run a single test/file.
 4. Identify the lint and type-check commands.
 5. Identify the dev server command if this is a web app.
 6. Note pre-commit hooks or other quality gates.
 Return a structured summary of all available commands."
```

Otherwise just check these yourself with Read/Grep. Store what you find — it's used
in every later phase.

## Phase 1: Bug Analysis & Reproduction

**Goal**: understand the bug, locate it in code, reproduce it reliably.

1. **Understand symptoms.** If given an issue ID, read it (`gh issue view`, `jira issue view`, etc.). Identify expected vs. actual behavior and any error messages.

   **If the report is too vague to reproduce** (no expected/actual behavior, no repro steps, no error message — e.g. "something is broken sometimes"): stop here. Call `AskUserQuestion`; if that tool isn't available, end your turn with the specific questions in your final message instead — reproduction steps, expected vs. actual behavior, environment/error messages — and go no further. Do not infer a root cause from a code read alone or invent your own repro scaffolding to stand in for a real report. Running in an automated, sandboxed, or non-interactive context is not a reason to guess instead of asking — it's a reason to put the questions in the final message rather than wait for a reply.
2. **Locate or create a failing test.** Grep for existing coverage. If none exists, write a minimal test that reproduces the bug, in the location and style the existing test suite uses.
3. **Reproduce it — a hard gate, not prose.** Run the reproduction test against the current (unfixed) code with the discovered test command, and show the actual failing output before touching the fix. If the report names a specific symptom (e.g. "double-charges on retry"), confirm the assertion for *that* symptom is what fails — a suite with some unrelated test failing while the reported-symptom assertion already passes is not a reproduction. If the test passes pre-fix, the reproduction is wrong: stop, don't proceed to Phase 2, and rewrite the test until it actually captures the reported bug. A test that never failed proves nothing about the fix you're about to write.
4. **Find the root cause.** For a localized bug, just grep/read the relevant file yourself. Reserve parallel subagents for bugs spanning multiple files or with unclear scope:

```
Agent 1 (Explore, haiku) — Bug Location:
  "Find the exact bug location (file:line), read the buggy code and its
   surrounding context, explain why it produces the wrong behavior, and
   provide evidence (stack trace, variable values, control flow)."

Agent 2 (Explore, haiku) — Impact Analysis:
  "Search the codebase for other code affected by the same issue, similar
   patterns with the same bug, related tests that might also fail, and
   callers of the buggy code."

Agent 3 (general-purpose, haiku, only if an external library is implicated):
  "Search Context7/web for documented solutions or known issues matching
   this bug in [LIBRARY_NAME]."
```

5. **Confirm the theory.** Re-read the buggy code and check it explains every symptom, including edge cases. If still uncertain, use `AskUserQuestion` before writing a fix on an unconfirmed theory.

## Phase 2: Fix Planning

**Goal**: a minimal, focused fix that addresses the root cause without side effects.

Design a fix that:
1. Addresses only the root cause — no drive-by refactoring.
2. Follows the project's existing patterns.
3. Has minimal scope (fewest lines changed).
4. Introduces no breaking changes.
5. Handles the edge cases found in Phase 1.
6. Never trims validation, error/data-loss handling, or security to keep the diff small — scope is what shrinks, not the safety floor. If a full fix isn't feasible right now, ship the safe partial fix and leave `// LEAN-DEBT: <limitation>. Upgrade when <trigger>.` rather than silently shipping the gap.

**Get approval for non-trivial fixes**: if the fix touches >3 files, modifies a
public API, has performance implications, or is otherwise breaking, use
`AskUserQuestion` to present the plan before implementing.

## Phase 3: Implementation

1. Apply the fix with Edit — minimal, focused changes.
2. Run the specific failing test and confirm it now passes. If it doesn't, that means the root-cause theory was wrong or incomplete — go back to Phase 1, not to a bigger patch on top of the current one.
3. Run the full test suite to check for side effects.
4. If new failures appear, adjust the fix (or correct a wrongly-specified test) and repeat until everything passes.

## Phase 4: Quality Verification

Run all quality checks using the commands discovered in Phase 0, then confirm every
line of this checklist — it's the single authoritative copy, used at completion time:

- [ ] Previously failing test now passes
- [ ] Full test suite passes (no regressions)
- [ ] No new linting errors
- [ ] No new type errors (if the language is typed)
- [ ] Fix addresses the root cause only, no unrelated refactoring
- [ ] Change is minimal and follows existing code patterns
- [ ] Any partial fix carries a `LEAN-DEBT` marker (see Phase 2)

If any item fails, fix it before proceeding — don't commit broken code, and don't
mark the phase complete until every box is checked.

## Phase 5: Final Commit

If the `git-commit` skill is available, use it. Otherwise commit manually:

```bash
git add [files modified]
git commit -m "fix: [concise description of what was fixed]

- [Root cause]
- [Solution approach]
- [Issue/ticket reference if applicable]

Closes #[ISSUE_NUMBER]"
```

## Phase 6: Verification Summary

Report to the user: bug description, root cause (file:line), the fix, files
modified, test results (previously-failing test, full suite, lint, type-check —
each pulled from the command output you actually ran, never invented), commit
info, and any `LEAN-DEBT` markers left behind.

## Additional Resources

- [references/examples.md](references/examples.md) — worked examples, argument
  parsing for optional flags (`--branch`, `--interactive`, `--test-only`), browser
  testing integration, and error-handling patterns (test-still-fails, ambiguous
  report, can't reproduce, multiple root causes). Load when you need one of those
  specifics; the phases above are sufficient for a standard fix.

## Important Notes

- **Test-driven**: see the test fail before writing the fix.
- **Minimal changes**: fix the bug, don't refactor unrelated code.
- **Evidence-based**: cite real file paths and line numbers, never a guess.
- **All tests must pass** before this is done; never commit with failing tests.
- **Ask when unsure** — clarifying is cheaper than guessing wrong and redoing it.
- **Browser testing is optional** — only when the bug is UI-facing and the tooling is available (see references/examples.md).
