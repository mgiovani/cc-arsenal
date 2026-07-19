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

Base each check on the actual output of the command you ran (`ls`, `grep`, `just --list`) — never assert a file is absent without having listed the directory. If two of these are present, ask the user which one is authoritative rather than running both. If none are found, stop and say so — do not invent a screenshot workflow.

For an unfamiliar repo, where a subagent/Task tool is available, delegate this discovery to it rather than grepping inline yourself; otherwise run the greps above directly. Either way, keep the discovered commands around for the rest of the run.

## Step 2: Run the diff

Run the discovered **diff** target, not the **update** target, even if the user asked to "fix the visual tests" — you need to see what changed before deciding anything should be updated.

```bash
just visual-diff        # or whatever Step 1 found
```

Capture:
- Which snapshots failed (component/story names)
- Where the diff images landed (commonly `__diff_output__/`, `.storybook-out/`, `test-results/`, or a Chromatic build URL)

If the run reports zero failures, stop here and tell the user the UI is clean — do not proceed to triage or update anything.

## Step 3: Triage each failure — once

This is the step that actually matters — do not skip to updating snapshots. Read the diff report ONE time and build ONE triage table directly from it: `Component/story | Changed on this branch? | Classification | Evidence`.

Fill "Changed on this branch?" from ground truth, not from the diff tool's own attribution: run `git diff --name-only <merge-base>...HEAD` (or `git log --name-only` for the branch) and check whether files that could plausibly affect this component actually appear in that list. A diff tool pointed at the wrong target (a stale mock, a decoy script from ambiguous discovery in Step 1) will confidently blame a commit message for a file that commit never touched — the git history is the only thing that can't be fooled by that.

Classify each row:

**Real regression** — the diff shows something nobody meant to change: wrong color, shifted layout, overlapping text, a broken icon, on a component whose files are NOT the ones the branch's intended change targets. Root cause is usually a shared style/layout/theme file the branch also touched.

**Intended change** — the diff matches a change the branch is actually making, AND the component's files show up in the branch's changed-file list. Confirm both: the visual diff looks like the described change, and git confirms this component's source was actually edited.

**Flaky/non-deterministic** — a few pixels of anti-aliasing, a font-rendering difference, or a mid-frame animation capture, with no corresponding file in the branch's changed-file list. Note it as flaky; don't silently update over it — a flaky baseline hides real regressions later.

**Needs human review** — the diff, the commit history, or the component ownership is ambiguous even after checking git. Use `AskUserQuestion` or say so plainly. Never default an ambiguous row to "approved" — snapshot updates are hard to undo once merged.

Build the table top to bottom, once, per failure — not as a single batch judgment on the whole run (a branch that legitimately redesigns the button can still introduce an unrelated regression in the header). If evidence gathered later changes a row's classification, edit that row in place. Never draft a second, competing triage table or report later in the same run: two analyses of the same diff report means the model is negotiating with itself, and whichever draft comes last can silently overwrite a correct earlier finding as the final answer. There is exactly one triage table per run, and it is the one Step 5 reports.

## Step 4: Update snapshots — only for confirmed-intended failures

Update snapshots one component/story at a time (or by the tool's targeted-update flag if it has one), not with a blanket `--update-all`:

```bash
just visual-update --story=Button   # targeted, not the whole suite
```

If the invocation used this skill's `--update` / `--component name` shorthand, map them to whatever the discovered tool actually calls its own flags: `--update` → the tool's write-mode flag (`--update-snapshots` for Playwright, `-u` for Jest/Storybook test-runner, or the task runner's `visual-update` target); `--component name` → its targeted-story filter (`--grep name` for Playwright, `--story=name` for a Storybook-runner wrapper, or the task runner's argument for the same). If Step 1 found no targeted-update flag at all, fall back to updating everything and re-diffing, per below.

If the tool only supports updating everything at once, re-run the diff afterward and confirm the only changes are the ones you approved — a blanket update can silently accept a regression sitting next to the real change.

Never update a snapshot for a failure classified as a real regression — that's hiding a bug in the baseline. Fix the regression, then re-run Step 2 to confirm it's gone before moving on.

## Step 5: Summarize

Report the same triage table from Step 3 — do not regenerate it from scratch or produce a second version. Add one column: Action taken (fixed the code / updated the snapshot / flagged as flaky / left open for human review).

End with a one-line verdict: clean to merge, or blocked on N unresolved regressions/human-review rows. A "needs human review" row always blocks the verdict — it never rounds up to clean.

Example, for a branch that redesigned `Button` but also shifted `Header` by accident:

```
| Component/story          | Changed on branch? | Classification | Evidence                                    | Action              |
|---------------------------|---------------------|-----------------|----------------------------------------------|----------------------|
| Button (primary variant) | Y (Button.css)      | Intended        | Matches redesign commit; git confirms Button.css edited | Snapshot updated    |
| Button (disabled variant)| Y (Button.css)      | Intended        | Same redesign                               | Snapshot updated    |
| Header                   | N (theme.css only)  | Regression      | 8px top margin shift; git shows only a shared spacing token in theme.css touched, not Header itself | Left open, NOT updated |

Verdict: blocked on 1 unresolved regression (Header).
```
