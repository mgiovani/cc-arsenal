---
name: vrt-check
description: Runs the project's visual regression testing (VRT) workflow — detects
  whatever tooling the repo actually uses (justfile/Makefile/package.json targets like
  visual-diff or visual-update, Storybook test-runner, Playwright screenshot tests,
  Chromatic, Loki, Percy), executes the diff, and triages every failure as a real
  regression or an intended change by inspecting the diff images and the components
  that changed on this branch. Only updates snapshots for changes confirmed intended;
  never blanket-approves a diff run. Use when the user says "run the visual diff",
  "check for visual regressions", "VRT", "did I break the UI", "update snapshots",
  "storybook snapshot tests failing", or before merging a branch that touches UI
  components. Not for a subjective UX/design critique with no baseline (use
  review-design) or writing new tests from scratch (use test-suite).
disable-model-invocation: false
argument-hint: "[--update] [--component name]"
allowed-tools: Read, Bash, Grep, Glob, Task, AskUserQuestion
---

# VRT Check

Run visual regression tests, then triage every failure by eye before touching a snapshot. The workflow's only real risk is rubber-stamping `--update` on a diff nobody looked at — everything below exists to prevent that.

## Step 1: Discover the tooling

Never assume a command. Different repos wire VRT through different tools. Look for, in order:

1. **Task runner targets** — `just --list` or `grep -E 'visual|screenshot|chromatic|snapshot' justfile Makefile` for targets like `visual-diff`, `visual-update`, `test:visual`.
2. **package.json scripts** — `grep -A2 '"scripts"' package.json` for `chromatic`, `test:visual`, `storybook:test`, `playwright test.*visual`.
3. **Storybook test-runner** — presence of `.storybook/test-runner.ts` or `@storybook/test-runner` in `package.json`.
4. **Playwright screenshot tests** — `toHaveScreenshot(` calls in `*.spec.ts`, or a `playwright.config.*` with `snapshotDir`/`toMatchSnapshot` settings.
5. **Chromatic** — `chromatic.config.json` or a `chromatic` devDependency; these run in CI and produce a web UI, not local diff images — say so and point the user there instead of trying to fake a local diff.
6. **Loki** — `.loki` config or `loki` devDependency.

If two of these are present, ask the user which one which is authoritative rather than running both. If none are found, stop and say so — do not invent a screenshot workflow.

For an unfamiliar repo, delegate discovery to an Explore subagent (haiku) rather than grepping inline yourself; keep the discovered commands in this conversation for the rest of the run.

## Step 2: Run the diff

Run the discovered **diff** target, not the **update** target, even if the user asked to "fix the visual tests" — you need to see what changed before deciding anything should be updated.

```bash
just visual-diff        # or whatever Step 1 found
```

Capture:
- Which snapshots failed (component/story names)
- Where the diff images landed (commonly `__diff_output__/`, `.storybook-out/`, `test-results/`, or a Chromatic build URL)

If the run reports zero failures, stop here and tell the user the UI is clean — do not proceed to triage or update anything.

## Step 3: Triage each failure

This is the step that actually matters — do not skip to updating snapshots. For every failed snapshot, classify it:

**Real regression** — the diff shows something nobody meant to change: wrong color, shifted layout, overlapping text, a broken icon. Root cause: some code change on this branch touched shared styles/layout/a component this story doesn't "own." Evidence: `git diff` on the branch for files that could plausibly affect this component (shared CSS, layout primitives, theme tokens), not just the story's own file.

**Intended change** — the diff matches a change the branch is actually making: the PR/commit description says "redesign the button," and the diff shows the button looking like the redesign. Confirm by reading the diff image (or Playwright's actual/expected/diff triptych) against the component file that changed, not by assuming intent from the failure alone.

**Flaky/non-deterministic** — diff is a few pixels of anti-aliasing, a font-rendering difference, or an animation caught mid-frame, with no corresponding code change nearby. Note it as flaky; don't silently update over it without flagging — a flaky baseline hides real regressions later.

Do this per-failure, not as a batch judgment on the whole run. A branch that legitimately redesigns the button can still introduce an unrelated regression in the header.

If a failure's cause is ambiguous after inspecting the diff and the git history for that component, use `AskUserQuestion` rather than guessing — snapshot updates are hard to undo once merged.

## Step 4: Update snapshots — only for confirmed-intended failures

Update snapshots one component/story at a time (or by the tool's targeted-update flag if it has one), not with a blanket `--update-all`:

```bash
just visual-update --story=Button   # targeted, not the whole suite
```

If the tool only supports updating everything at once, re-run the diff afterward and confirm the only changes are the ones you approved — a blanket update can silently accept a regression sitting next to the real change.

Never update a snapshot for a failure classified as a real regression — that's hiding a bug in the baseline. Fix the regression, then re-run Step 2 to confirm it's gone before moving on.

## Step 5: Summarize

Report, per failure:
- Component/story name
- Classification (regression / intended / flaky)
- What changed in the diff
- Action taken (fixed the code / updated the snapshot / flagged as flaky / left open)

End with a one-line verdict: clean to merge, or blocked on N unresolved regressions.
