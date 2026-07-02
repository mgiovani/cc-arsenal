# Release flow (dev to production)

A release promotes everything on `dev` to `main` (production) as a versioned, tagged release. Work top to bottom. Read the universal rails in `SKILL.md` first; they are assumed here.

## 0. Preconditions

- Confirm with the user which merged PRs are in scope. It is common to exclude a few that are not ready; if so, confirm they are genuinely absent from `dev`'s history before proceeding (`git log origin/dev --oneline | grep '(#NNN)'`).
- Make sure `main` is tagged with the current production version. The very first release in a repo that was already live may need the baseline tagged retroactively (`git tag -a v<current> <main-sha> -m "..."` and push) so the new tag has a predecessor.
- Decide the new version (see Versioning in `SKILL.md`).

## 1. Cut the release branch

- Branch from the tip of `dev`: `git fetch origin && git switch -c release/<x.y.z> origin/dev`.
- Bump the version in your project manifest (e.g. `package.json`, `pyproject.toml`, `Cargo.toml`) to `<x.y.z>`.
- Update `CHANGELOG.md` (see `references/changelog.md`). This is mandatory and is the moment the changelog is assembled from the PRs in scope.
- Commit: `chore(release): v<x.y.z>` (changelog and version bump can be one commit or two).

## 2. Open the PR to main

- Push the branch and open a PR `release/<x.y.z>` into `main`.
- Opening it runs the full Definition-of-Done gate automatically (lint, typecheck, tests, build, and whatever else your project requires).
- Optionally run a scoped code review of the release-risk surface (the diff `origin/main...release/<x.y.z>`).

## 3. Wait for green, root-fix anything red

- Poll the checks every few minutes. Do not merge until every check is green.
- A red check is a real defect to root-fix. If CI exposes a latent test regression introduced by an earlier PR, fix the test to match the intended behavior and push to the release branch.

## 4. Merge to main (this deploys production)

- Merge with a **merge commit** (`gh pr merge <n> --merge`). Capture the merge commit SHA.
- Verify the deploy landed: your deploy pipeline's check on the merge commit goes green, and production is healthy (e.g. a basic health probe returns the expected response).

## 5. Tag and create the GitHub release

- Annotated tag on the merge commit: `git tag -a v<x.y.z> <merge-sha> -m "Release v<x.y.z>"` then `git push origin v<x.y.z>`. Tags do not trigger an additional deploy; the merge already did.
- `gh release create v<x.y.z> --target <merge-sha> --title "v<x.y.z>" --latest --notes "<highlights>"`. Pull the highlights from the changelog entry. Mark it latest.

## 6. Stage the break-glass revert PR (leave it OPEN, never merge)

This is the rollback path. Merging it reverts the release on `main` and redeploys the previous production build.

- `git switch -c revert/release-<x.y.z> origin/main`
- `git revert -m 1 <merge-sha> --no-edit` (first-parent revert of the release merge)
- Push and open a PR into `main` titled like "Revert v<x.y.z> release (break-glass rollback)", with a body stating it is a pre-staged rollback and must not be merged unless a production rollback is required.
- Leave it OPEN. Do not merge it. It is the safety net someone can merge in seconds if production misbehaves.

## 7. Back-merge to dev and clean up

- Open a PR `release/<x.y.z>` into `dev` and merge it with a **merge commit**. This carries the version bump, the changelog, and any release-stabilization fixes back into `dev` so `dev` stays ahead of `main`.
- Wait for its checks to be green before merging.
- After it merges, delete `release/<x.y.z>` from origin. Deleting it does not close the revert PR (that lives on a different branch).
