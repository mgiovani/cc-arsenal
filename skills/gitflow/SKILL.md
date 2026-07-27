---
name: gitflow
description: Manage a gitflow branching workflow, starting and finishing feature,
  release, and hotfix branches; cutting versioned releases with changelog generation;
  coordinating emergency hotfixes directly to production; and keeping long-lived
  branches in sync. Activates when users mention gitflow, feature/release/hotfix
  branches, cutting a release, branching strategy, promoting an integration branch
  to production, tagging a version, or rolling back a live release. Also reaches
  for it when the user says "promote dev to main" or "we need to hotfix prod"
  without naming gitflow. Not for a single commit message (use git-commit).
  Not for versioned releases on a simple main-branch workflow with no release/hotfix
  branches (use git-release). Not for the mechanical review-to-merge pipeline on
  a branch with no release/hotfix topology involved (use ship). Skip for general
  git mechanics (merge conflicts, interactive rebase, git education) or CI-failure
  debugging unrelated to a release.
metadata:
  author: mgiovani
  version: 1.0.0
---

# Gitflow

This skill covers the full gitflow branching model with two long-lived branches and short-lived branches off them.

- **`main`** is **production**. Merging to `main` triggers your deploy pipeline. Treat every merge to `main` as a production deploy that your users will see shortly after.
- **`dev`** (sometimes called `develop`) is the integration branch. Day-to-day feature and fix work lands here first.
- Short-lived branches: `feat/<desc>` and `fix/<desc>` off `dev`, `release/<x.y.z>` off `dev`, `hotfix/<x.y.z>` off `main`.

## Pick the flow

Read the matching reference in full and follow it step by step. Each one is self-contained.

| The user wants to...                                              | Flow    | Read                      |
| ----------------------------------------------------------------- | ------- | ------------------------- |
| Ship the accumulated `dev` work to production                     | Release | `references/release.md`   |
| Get an urgent fix into production now, can't wait for a release   | Hotfix  | `references/hotfix.md`    |
| Build a new feature or a fix that will ride the next release      | Feature | `references/feature.md`   |

If the intent is ambiguous (e.g. "ship the settings fix"), ask one question: is this urgent enough to go straight to production (hotfix), or does it ride the next release (feature now, release later)?

## Universal rails

These apply to every flow. They exist because `main` is live production and a mistake here is user-visible, so the cost of a shortcut is real.

- **`main` is a deploy button.** Never merge to `main` while any CI check is not green. The full Definition-of-Done gate runs on a PR to `main`; wait for all of it. Poll CI every few minutes rather than tight-looping, to keep token cost sane. No CI pipeline configured on the repo? Skip the wait-for-green step and say so explicitly before merging.
- **Always update `CHANGELOG.md`** during a release and a hotfix (never per-feature; the changelog is assembled at ship time). See `references/changelog.md` for the format.
- **Conventional Commits.** Follow the [Conventional Commits](https://www.conventionalcommits.org/) spec. Keep commit messages, PR titles, PR bodies, the changelog, and release notes clean and professional.
- **Never force-push.** Never bypass git hooks (`--no-verify` or equivalent). The pre-push hooks are part of the safety net. If a push fails due to a hook, investigate and root-fix the underlying issue; never bypass.
- **Stage only the files you intend.** Prefer `git add <specific-files>` over blanket staging commands. Verify what you are about to stage with `git diff --staged` before committing.
- **Verify before every push.** Run `git log --oneline <base>..HEAD` and `git diff --stat <base>..HEAD` so you know exactly what is going to the remote, especially before anything that touches `main`.
- **After any merge to `main` (release or hotfix), open a break-glass revert PR and leave it OPEN.** It is the one-click rollback. Never merge it yourself. See the shared procedure in `references/release.md` (the revert step is identical for hotfix).

## Versioning

Semantic versioning. The current version lives in your project manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.) on both long-lived branches (kept in sync; both are at the last released version). No version manifest in the repo? Version via the latest `git tag` alone and skip the bump-file step.

- **Release**: bump minor for new features (e.g. `1.1.0` to `1.2.0`), major for breaking changes.
- **Hotfix**: bump patch (e.g. `1.1.0` to `1.1.1`).
- The tag is `v<x.y.z>`, annotated, placed on the merge commit on `main`.

## Merge methods (they differ by target, on purpose)

- **Feature/fix PR into `dev`**: squash merge (one clean commit per PR with the `(#NNN)` suffix). This keeps `dev` history readable.
- **`release/*` or `hotfix/*` into `main`**: merge commit (`--no-ff`). This preserves the release as a first-parent merge so the break-glass revert (`git revert -m 1`) is clean.
- **Back-merge `release/*` or `hotfix/*` into `dev`**: merge commit.

Delete short-lived branches yourself once they are merged everywhere they need to go.

## Stay in the loop

These flows touch production. When CI is running or a deploy is in flight, report each milestone to the user as it lands (CI green, merged, deploy healthy, tagged) rather than going silent. If any gate is red, stop and root-fix; do not merge around it.
