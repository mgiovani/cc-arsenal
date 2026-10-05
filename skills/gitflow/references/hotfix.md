# Hotfix flow (urgent fix straight to production)

A hotfix patches production now, without waiting for the next release. It branches from `main` (not `dev`), ships through the same production gate, and is then back-merged to `dev` so the fix is not lost. Read the universal rails in `SKILL.md` first.

Use this only when the fix genuinely cannot wait for a release. If it can wait, it is a feature/fix branch to `dev` (`references/feature.md`) and rides the next release.

Copy this checklist into your reply and tick each step as it lands. Do the steps in order; the gates below say where a failure sends you.

```
- [ ] 1. Branch: git fetch origin && git switch -c hotfix/<x.y.z> origin/main (<x.y.z> = production version with the patch bumped, e.g. 1.1.0 to 1.1.1)
- [ ] 2. Fix: smallest correct change plus a regression test that would have caught the bug
- [ ] 3. Bump: set <x.y.z> in the manifest (no manifest: skip, the tag carries the version)
- [ ] 4. Changelog: add a "## [<x.y.z>] - <date>" entry (references/changelog.md)
- [ ] 5. Commit with Conventional Commits, then push
- [ ] 6. PR: open hotfix/<x.y.z> into main; the full Definition-of-Done gate runs
- [ ] 7. Green: wait for every check to pass (no CI: skip, say so)
- [ ] 8. Merge to main with a merge commit, capture <merge-sha>
- [ ] 9. Deploy: pipeline is green and production is healthy
- [ ] 10. Tag: annotated v<x.y.z> on <merge-sha>, push it
- [ ] 11. Release: gh release create v<x.y.z> --target <merge-sha> --latest --notes "<what the hotfix fixes>"
- [ ] 12. Revert PR: revert/hotfix-<x.y.z> from origin/main, git revert -m 1 <merge-sha> --no-edit, push, open a PR into main as a pre-staged rollback, leave it OPEN, never merge
- [ ] 13. Back-merge: PR hotfix/<x.y.z> into dev, merge with a merge commit
- [ ] 14. Clean up: delete hotfix/<x.y.z> from origin once merged to both main and dev
```

## Gates

- Step 1, why `main`: branching from `main`, not `dev`, isolates the urgent fix from unreleased `dev` work, so you ship only the fix. `hotfix/<x.y.z>` already on origin means a hotfix is in flight; stop and ask.
- Step 2, no regression test: do not proceed to step 3. A hotfix without one invites the same incident again.
- Step 7, CI red: a defect to root-fix, not something to work around. Fix on the hotfix branch, push, and return to step 7. If the same check is red after 3 fix rounds, stop and report.
- Step 8, merge blocked or conflicts with main: stop and ask.
- Step 9, deploy or health probe red: stop and tell the user before any further step. The revert PR from step 12 is the rollback; merging it is the user's call.
- Step 10, tag already exists: stop and ask. Never move or delete a pushed tag. If it already points at `<merge-sha>`, continue at step 11.
- Step 12: identical to the release flow's revert step (see `references/release.md`).
- Step 13, back-merge: the fix exists on `main` but not `dev`, so it must be carried back or it will regress on the next release. If `dev` has moved on and the merge conflicts, stop and ask before resolving; the resolution keeps both the hotfix and the newer `dev` work, and the hotfix's intent must survive. Red checks return to step 7 logic. Do not do step 14 until the back-merge lands.
