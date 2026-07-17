# Hotfix flow (urgent fix straight to production)

A hotfix patches production now, without waiting for the next release. It branches from `main` (not `dev`), ships through the same production gate, and is then back-merged to `dev` so the fix is not lost. Read the universal rails in `SKILL.md` first.

Use this only when the fix genuinely cannot wait for a release. If it can wait, it is a feature/fix branch to `dev` (`references/feature.md`) and rides the next release.

## 1. Branch from main

- `git fetch origin && git switch -c hotfix/<x.y.z> origin/main`, where `<x.y.z>` is the current production version with the **patch** bumped (e.g. `1.1.0` to `1.1.1`).
- Branching from `main`, not `dev`, is the whole point: it isolates the urgent fix from unreleased `dev` work, so you ship only the fix.

## 2. Make the fix, with tests

- Implement the smallest correct fix. Add or update tests that would have caught the bug; a hotfix without a regression test invites the same incident again.
- Bump the version in your project manifest to the patch version. No manifest? Skip this — the tag alone carries the version (see Versioning in `SKILL.md`).
- Update `CHANGELOG.md` with a new `## [<x.y.z>] - <date>` entry for the fix (see `references/changelog.md`).
- Follow Conventional Commits throughout.

## 3. PR to main, wait for green

- Push and open a PR `hotfix/<x.y.z>` into `main`. The full Definition-of-Done gate runs automatically (same suite as a release).
- Wait for every check to be green. A red check is a defect to root-fix, not something to work around. No CI pipeline on the repo? Skip this step and say so.

## 4. Merge, deploy, tag, release

- Merge with a **merge commit**. Capture the merge SHA.
- Verify your deploy pipeline is green and production is healthy.
- Annotated tag `v<x.y.z>` on the merge commit, push it, and `gh release create v<x.y.z> --target <merge-sha> --latest --notes "<what the hotfix fixes>"`.

## 5. Break-glass revert PR (leave OPEN, never merge)

Identical to the release flow's revert step: branch `revert/hotfix-<x.y.z>` from `origin/main`, `git revert -m 1 <merge-sha> --no-edit`, push, open a PR into `main` describing it as a pre-staged rollback, and leave it OPEN. Do not merge it.

## 6. Back-merge to dev and clean up

- The fix exists on `main` but not `dev`, so it must be carried back or it will regress on the next release. Open a PR `hotfix/<x.y.z>` into `dev` and merge it with a **merge commit**.
- If `dev` has moved on and the back-merge conflicts, resolve in favor of keeping both the hotfix and the newer `dev` work; the hotfix's intent must survive.
- Delete `hotfix/<x.y.z>` from origin after it is merged to both `main` and `dev`.
