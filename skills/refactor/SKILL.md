---
name: refactor
description: "Restructures existing code without changing its behavior — maps callers and test coverage, adds characterization tests where coverage is thin, then applies the change in small steps verified against the full test suite after each one. Use when the user wants to refactor, extract a method or class, simplify logic, reduce duplication, improve naming, restructure modules, or pay down technical debt in code that already works. Not for adding new functionality (use implement-feature) or fixing broken behavior (use fix-bug)."
disable-model-invocation: false
argument-hint: "<refactoring_description> [--scope file|module|project] [--interactive]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
hooks:
  Stop:
    - hooks:
      - type: agent
        prompt: "Run the Phase 4 Quality Gates Checklist from SKILL.md against the current diff and the test/lint/type-check commands discovered in Phase 0 (fall back to CLAUDE.md or project files if Phase 0 wasn't run). If any item fails, return decision: block with the specific failing item named. Only allow stopping when every item passes."
        timeout: 180
---

# Refactor

Refactor code safely using characterization tests, incremental changes, and continuous verification. Every change preserves existing behavior while improving code structure, readability, and maintainability.

## Refactoring Goal

$ARGUMENTS

## Core Principle: Behavior Preservation

Refactoring changes code structure WITHOUT changing behavior. Every step must be verified against existing tests. If tests break, the refactoring introduced a bug — revert and retry.

## Anti-Hallucination Guidelines

1. **Read before changing** — understand all callers and dependencies first.
2. **Test before and after** — full suite before starting, and again after every incremental change. Results must match.
3. **Characterization tests first** — where coverage is thin, capture current behavior in tests before restructuring.
4. **Incremental changes** — one small, verifiable change at a time. Never combine steps into a single edit.
5. **No feature changes** — refactoring doesn't add features, fix bugs, or change behavior; those are separate tasks (`implement-feature`, `fix-bug`). Phase 0's scope gate below is where this gets enforced, not just stated.
6. **Reference real code** — never claim a structure you haven't verified by reading the actual files.
7. **Prefer deletion over addition** — when several call sites share logic, consolidate it into one place and delete the copies, rather than wrapping them in a new abstraction.
8. **Never trim the floor** — simplifying structure must not drop a validation check, an error/data-loss path, a security control, or an accessibility branch. If a step would drop one, it's a behavior change, not a refactor — stop and re-scope it separately.

## Quality Gates

A Stop hook re-runs the Phase 4 Quality Gates Checklist automatically and blocks completion if any item fails — see the hook prompt above for the exact wording.

## Task Management

Whether the ceremony below (formal task chain, subagent fan-out) is worth it depends on blast radius, not on whether the skill fired.

The Phase 0 scope gate below always runs, even on the skip path — it's a five-second scan of the request, not ceremony.

**Skip the task chain** — grep the callers yourself, run the existing tests, make the change, run tests again; done:
- Single-variable/function rename
- Formatting or style-only fix
- Single-line simplification
- Any single-file refactor (extract method, inline variable, simplify conditional) where one Grep enumerates every caller

**Use the full task chain (Phase 0-6 below)** when:
- The refactoring spans multiple files
- It's an extract/move-class operation, or anything needing a dependency-graph analysis
- The caller list isn't obvious from a single grep
- Progress needs to be tracked across sessions

**Task structure:** a strict sequential chain — each phase blocked on the previous — so characterization tests exist before any structural change begins. `TaskCreate` returns the real task ID to use in `addBlockedBy`; don't hardcode literal IDs like `1`-`6`, other tasks may already exist in the session. After finishing each phase, mark its task `completed` and run `TaskList` to confirm the next one unblocked — this applies at the end of every phase below. Full `TaskCreate`/`TaskUpdate` templates and the Explore-agent prompts for Phase 0 and Phase 1 are in [references/task-chain.md](references/task-chain.md) — load it when actually running the full chain.

**Portability:** no `Task`/`TaskCreate` tools available? Drop the task chain and subagent fan-out — work through Phase 0-5 yourself, in order. The sequencing (characterization tests before structural change) is what matters, not the tracking mechanism.

## Implementation Workflow

### Phase 0: Scope Gate + Project Discovery

**Step 0a — Mixed-scope gate (blocking, do this before anything else, no exceptions):**

1. Read the request for anything that isn't a pure structural change to existing behavior — a new option, a new endpoint, a bug fix, "while you're in there, also add...". A rename/extract/move/inline/simplify/dedupe is refactor scope; anything that changes what the code *does* for a caller is not.
2. If the request is mixed-scope, do not write, edit, or commit any code for the behavior-changing half — not as a draft, not because "it's small anyway."
3. If the split is unambiguous, proceed with the refactor half only and skip to Step 0b.
4. If it's genuinely unclear which half the user wants (e.g. the request could be read as "rename only" or "rename plus feature, your call"), use `AskUserQuestion` to ask before writing any code. Don't guess.
5. Whichever path you took, the Phase 6 summary MUST name the deferred behavior-changing piece by name and point to `implement-feature` (or `fix-bug`). This is checked against the actual final message sent to the user, not against intent recorded earlier in the run — a run that does the refactor correctly but never says what it skipped has not passed this gate.

No mixed scope detected → proceed straight to Step 0b.

**Step 0b — Project discovery:** discover the project's test/lint/type-check commands (CLAUDE.md, Makefile/justfile/package.json/pyproject.toml — an Explore/Haiku agent works well here for wider projects, prompt in `references/task-chain.md`). Run the full test suite and record the baseline before touching any code. Pre-existing failures aren't yours to fix — just don't let the refactoring add new ones.

### Phase 1: Scope Analysis

Map every caller and dependent of the target (Grep for calls, imports, type references, and dynamic/string-based lookups), and map its existing test coverage — what's tested, what's a gap. For a single-file target with an obvious blast radius, do this yourself; for a wider one, two Explore agents in parallel (callers/dependencies, then test coverage) save tokens — prompts in `references/task-chain.md`.

If the refactoring touches more than 5 files, changes a public API, or affects external consumers, use `AskUserQuestion` to confirm scope before proceeding.

### Phase 2: Characterization Tests

Where Phase 1 found coverage gaps, write tests that capture CURRENT behavior — including quirks and edge cases, not desired behavior — before changing anything. Name them so they're identifiable as characterization tests (`test_char_*` in Python, `TestChar_*` in Go, a `characterization:` describe block in JS). Run the full suite; every one must pass against the pre-refactoring code. Skip this phase entirely when the target already has thorough coverage.

```python
def test_char_calculate_total_with_discount():
    """Characterization: captures current discount calculation behavior."""
    result = calculate_total(items=[100, 200], discount=0.1)
    assert result == 270.0  # current behavior: discount applied to sum
```

### Phase 3: Incremental Refactoring

Break the change into the smallest independently-verifiable steps. See [references/patterns.md](references/patterns.md) for the step sequence per technique (extract method, extract class, rename, move, simplify conditional, remove duplication, inline, decompose large function). For each step: make the change, run tests immediately.

Tests fail → stop, don't push through. Revert if it's a behavioral change and find a smaller step; only touch the test itself if it was asserting an implementation detail, not behavior; and check whether it's actually a pre-existing baseline failure. Never batch multiple steps before testing — that discipline is what separates refactoring from a rewrite in disguise.

For multi-file changes: update the target first, then update callers one at a time (testing after each), then clean up dead code last. When the change needs temporary duplication, keep old and new structures working side by side until every caller has migrated, then remove the old one.

### Phase 4: Final Verification

Run every quality check the project has, against the Phase 0 baseline.

**Quality Gates Checklist:**
- [ ] Full test suite passes (matches or exceeds Phase 0 baseline)
- [ ] Characterization tests pass
- [ ] No new lint or type errors
- [ ] Code is cleaner/simpler than before — the actual point of doing this
- [ ] No accidental behavior changes, debug code, or commented-out code
- [ ] All callers updated — no dangling references

Then read the actual diff (`git diff`) end to end for anything not on that list: leftover debug statements, unrelated formatting churn, missed import updates, orphaned code. Fix before proceeding — don't leave the task `in_progress` with a known-broken gate.

### Phase 5: Final Commit

Use the `git-commit` skill if available. Otherwise commit manually with type `refactor:`, a subject describing WHAT was restructured, a body explaining WHY, and always end with "No behavioral changes.":

```
refactor: extract validation logic from OrderProcessor

Moved order validation into dedicated OrderValidator class to improve
separation of concerns. OrderProcessor now delegates to OrderValidator
for all input validation.

No behavioral changes.
```

```
refactor(auth): simplify token refresh conditional logic

Replaced nested if/else chain with guard clauses and extracted
isTokenExpired() helper.

No behavioral changes.
```

### Phase 6: Summary Report

Report what was restructured, which technique was used, files touched, before/after test results (must match), any characterization tests added, and the commit hash. Only state metrics (line counts, complexity, coverage %) that came from a command actually run this session — never estimate them.

If Phase 0's scope gate deferred any behavior-changing work, state that by name here, explicitly, and point to `implement-feature`/`fix-bug` — even if it was already mentioned earlier in the run. The final message is what gets checked, not the earlier reasoning.

## Important Notes

- **Tests before and after every change** — non-negotiable.
- **No behavior changes** — refactoring changes structure only; if tests break, revert.
- **Minimal scope** — refactor only what was requested; resist "while I'm here" changes to adjacent code.
- **Ask when unsure** — better to clarify scope than to over-refactor.

## Additional Resources

- [references/patterns.md](references/patterns.md) — refactoring catalog with step-by-step procedures per technique; load when picking the step sequence for a specific refactoring type.
- [references/task-chain.md](references/task-chain.md) — `TaskCreate`/`TaskUpdate` templates and Explore-agent prompts; load when running the full multi-file task chain (Phase 0-1).
