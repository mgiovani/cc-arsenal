# Release flow (dev to production)

A release promotes everything on `dev` to `main` (production) as a versioned, tagged release. Work top to bottom. Read the universal rails in `SKILL.md` first; they are assumed here.

## 0. Preconditions

- Confirm with the user which merged PRs belong in this release. It's common to exclude a few that aren't ready yet. If any are excluded, verify they're genuinely absent from `dev`'s history before you proceed (`git log origin/dev --oneline | grep '(#NNN)'`).
- Make sure `main` already carries a tag for the current production version. If this repo was live before its first tracked release, the baseline tag may need to be created retroactively: `git tag -a v<current> <main-sha> -m "..."` and push, so the new tag has something to diff against.
- Decide the new version, see Versioning in `SKILL.md`.

## 1. Cut the release branch

- Start from the tip of `dev`: `git fetch origin && git switch -c release/<x.y.z> origin/dev`.
- If the project has a manifest (`package.json`, `pyproject.toml`, `Cargo.toml`), bump its version to `<x.y.z>`. No manifest? Skip that step; the tag alone carries the version (see Versioning in `SKILL.md`).
- Updating `CHANGELOG.md` is not optional here: this is the moment it gets assembled from the PRs in scope (see `references/changelog.md`).
- Commit the result as `chore(release): v<x.y.z>`, either as one commit covering both the changelog and the bump, or split across two.

## 2. Open the PR to main

- Push the branch and open a PR from `release/<x.y.z>` into `main`. Opening it triggers the full Definition-of-Done gate automatically: lint, typecheck, tests, build, and anything else the project requires.
- A scoped code review of the release-risk surface (the diff `origin/main...release/<x.y.z>`) is optional but worth doing.

## 3. Wait for green, root-fix anything red

- Poll the checks every few minutes and hold the merge until everything is green. No CI pipeline in this repo? Skip the step, but say so.
- Treat a red check as a genuine defect, not noise to route around. Even if CI surfaces a latent test regression introduced by an earlier PR, fix the test to match the intended behavior and push the fix to the release branch.

## 4. Merge to main (this deploys production)

- Merge with a merge commit (`gh pr merge <n> --merge`) and capture the resulting SHA.
- Then confirm the deploy actually landed: the deploy pipeline's check on that commit goes green, and production looks healthy (a basic health probe returning the expected response is enough).

## 5. Tag and create the GitHub release

- Tag the merge commit: `git tag -a v<x.y.z> <merge-sha> -m "Release v<x.y.z>"`, then `git push origin v<x.y.z>`. The tag doesn't trigger a second deploy, the merge already did that.
- Create the GitHub release with `gh release create v<x.y.z> --target <merge-sha> --title "v<x.y.z>" --latest --notes "<highlights>"`, pulling the highlights straight from the changelog entry, and mark it latest.

## 6. Stage the break-glass revert PR (leave it OPEN, never merge)

This is the rollback path: merging it reverts the release on `main` and redeploys whatever production was running before.

- `git switch -c revert/release-<x.y.z> origin/main`
- `git revert -m 1 <merge-sha> --no-edit`, a first-parent revert of the release merge.
- Push it and open a PR into `main` titled something like "Revert v<x.y.z> release (break-glass rollback)"; state plainly in the body that this is a pre-staged rollback, not to be merged unless production actually needs it.
- Leave it open. Don't merge it. It's the safety net someone can trigger in seconds if things go wrong in production.

## 7. Back-merge to dev and clean up

- Open a PR from `release/<x.y.z>` into `dev` and merge it with a merge commit, so the version bump, changelog, and any release-stabilization fixes flow back and keep `dev` ahead of `main`. Wait for its checks to go green first.
- Once it merges, delete `release/<x.y.z>` from origin; that's harmless to the revert PR, since it lives on its own branch.
