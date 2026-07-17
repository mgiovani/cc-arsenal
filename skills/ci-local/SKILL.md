---
name: ci-local
description: Run the checks a GitHub Actions workflow would run, locally, when Actions
  is unavailable or out of quota. Parses .github/workflows/*.yml, extracts the jobs/steps
  that gate merges (lint, typecheck, test, build), translates them to local commands
  respecting the workflow's pinned node/python versions and env, executes them
  sequentially, and reports a parity table of what passed locally vs. what can't be
  replicated (service containers, secrets, matrix dimensions) and why. Activates on
  "CI quota", "Actions is down/unavailable", "run CI locally", "verify like CI would",
  "run the pipeline on my machine", or a pre-push request to check a branch the way
  CI checks it. Not for generating a new workflow file (use ci-generate), not for
  debugging why a specific CI run failed on GitHub (use fix-bug or review-code), and
  not for the release/hotfix gating process itself (use gitflow) — this skill only
  produces the local stand-in when the real thing isn't reachable.
disable-model-invocation: false
argument-hint: "[workflow-file] [--job name]"
allowed-tools: Read, Grep, Glob, Bash, Task
---

# CI Local

Reproduce a GitHub Actions run on the local machine. The workflow YAML is the spec —
read it, don't guess at what "the lint step" or "the test step" means.

## Scope

GitHub Actions only (`.github/workflows/*.yml`). If the repo uses GitLab CI, CircleCI,
or Jenkins instead, say so and stop — no translation layer exists for those yet
(add one if it comes up twice, not speculatively).

## Phase 1: Find the merge-gating jobs

1. If invoked with `[workflow-file]` and/or `--job name`, skip the glob — read only
   that file, and if `--job` is given, extract only that job. Otherwise `Glob` for
   `.github/workflows/*.yml` (and `.yaml`). If none exist, tell the user there's no
   workflow to mirror and stop.
2. Read each file. A job **gates merges** if its workflow triggers on `pull_request`
   or `push` to a protected branch — ignore jobs that only run on `schedule`,
   `workflow_dispatch`, or `release` unless the user asks for those specifically.
3. For a multi-file or multi-job repo, use a haiku `Explore` subagent to read all
   workflow files in parallel and return a structured list of: job name, trigger,
   runs-on, steps (with `uses`/`run`/`env`/`working-directory`), `services:`,
   `strategy.matrix`, and any `${{ secrets.* }}` references. Keep this out of the
   main thread — workflow YAML is verbose and you only need the extracted summary.
   No subagent tool available? Read the workflow files directly and extract the
   same summary inline.

## Phase 2: Translate steps to local commands

Walk the steps in order and translate each one. Do not invent a generic
`lint && test && build` — use exactly what the workflow does.

| Workflow step | Local translation |
|---|---|
| `actions/checkout` | no-op — you're already in the working tree |
| `actions/setup-node` with `node-version: X` | `fnm use X` (or `nvm use X`) before the next steps; if neither is installed, warn and continue on whatever `node -v` reports |
| `actions/setup-python` with `python-version: X` | `uv python pin X` / `uv run --python X ...`; same fallback-and-warn if `uv` isn't available |
| `run: <cmd>` with a `working-directory:` or `env:` block | run `<cmd>` from that directory with those env vars exported for just that command |
| cache steps (`actions/cache`) | no-op — local disk cache already exists |
| a `run:` step gated by `if:` on OS or event | skip if the condition can't hold locally (e.g. `runs-on: windows-latest` step on a Mac), and say so |

If no explicit version is pinned in the workflow, check `.nvmrc` / `package.json#engines.node`
or `.python-version` / `pyproject.toml#requires-python` before falling back to whatever's
on `PATH`.

**Can't be replicated — flag, don't fake:**
- `services:` (Postgres, Redis, etc.) — note the service and image; only attempt it if
  Docker is available and the user wants the extra step, otherwise mark the steps that
  depend on it as skipped.
- `${{ secrets.* }}` — check if a local `.env` supplies the same variable name; if not,
  mark the step as skipped with the missing secret name, never substitute a fake value.
- `strategy.matrix` — run the one combination that matches the local machine (current
  node/python/OS); list the other matrix entries as not covered.

## Phase 3: Execute sequentially

Run the translated commands via `Bash`, in the same order the workflow declares them,
stopping to report clearly the moment one fails (don't silently keep going past a
failed lint step and call the run "done"). Capture stdout/stderr for the report.

## Phase 4: Report the parity table

```
CI Local Parity — <workflow file>, job "<job name>"

Step                  Local result     Notes
---------------------------------------------------------------
checkout              n/a              already in working tree
setup-node 20         ok               fnm use 20
lint (eslint)          PASS
typecheck (tsc)        PASS
test (vitest)           FAIL            2 tests failing, see output above
build                  SKIPPED         not run, blocked by failing test
postgres service       NOT REPLICABLE  no service container locally (Docker not requested)
deploy (secrets.AWS_*)  NOT REPLICABLE  secret not present in .env
```

Any version-fallback warning from Phase 2 (pinned node/python version unavailable,
falling back to whatever's on `PATH`) must surface as a caveat/NOT REPLICABLE note in
this parity table — never absorbed into a PASS.

Every row's result comes from a command you actually ran this session — never write
PASS, FAIL, or a test count you didn't observe in the Phase 3 output.

State plainly at the end whether the branch would pass the real CI gate, and what's
still unverified because it couldn't run locally.

## Examples

**Targeted job, `--job lint` given:** skip the glob, read only the named job's steps
from the file the user pointed at, translate and run just those, report a parity
table scoped to that one job.

**Python repo, no pinned version in the workflow:** `actions/setup-python` has no
`python-version:` key → check `pyproject.toml#requires-python`, find `>=3.11`, run
`uv run --python 3.11 pytest`. Note the fallback source in the parity table
(`"version from pyproject.toml, not workflow"`), don't silently treat it as pinned.

**Matrix build, `strategy.matrix: node: [18, 20, 22]`:** run once on whatever `fnm`/`nvm`
resolves locally (say 20), mark 18 and 22 as `NOT REPLICABLE — matrix entry not run
locally` in the table instead of guessing they'd also pass.

## Notes

- This is read-only with respect to git — no commits, no pushes, no workflow file edits.
  Installing dependencies (`npm ci`, `uv sync`, etc.) as part of a step is expected and fine.
- If the same repo asks for this repeatedly, that's a signal to fix the actual CI quota/outage,
  not to keep leaning on the local stand-in — mention that once, don't nag.
