# Release flow (dev to production)

A release promotes everything on `dev` to `main` (production) as a versioned, tagged release. Read the universal rails in `SKILL.md` first; they are assumed here.

Copy this checklist into your reply and tick each step as it lands. Do the steps in order; the gates below say where a failure sends you.

```
- [ ] 0. Scope: confirm with the user which merged PRs ship; decide <x.y.z> (Versioning in SKILL.md)
- [ ] 1. Baseline: main carries a tag for the current production version
- [ ] 2. Branch: git fetch origin && git switch -c release/<x.y.z> origin/dev
- [ ] 3. Bump: set <x.y.z> in the manifest (no manifest: skip, the tag carries the version)
- [ ] 4. Changelog: assemble CHANGELOG.md from the PRs in scope (references/changelog.md)
- [ ] 5. Commit: chore(release): v<x.y.z> (one commit or split), then push
- [ ] 6. PR: open release/<x.y.z> into main; the full Definition-of-Done gate runs
- [ ] 7. Green: poll checks every few minutes, hold the merge until all pass (no CI: skip, say so)
- [ ] 8. Merge to main: gh pr merge <n> --merge, capture <merge-sha> (this deploys production)
- [ ] 9. Deploy: pipeline check on <merge-sha> is green and a health probe passes
- [ ] 10. Tag: git tag -a v<x.y.z> <merge-sha> -m "Release v<x.y.z>" && git push origin v<x.y.z>
- [ ] 11. Release: gh release create v<x.y.z> --target <merge-sha> --title "v<x.y.z>" --latest --notes "<highlights from the changelog entry>"
- [ ] 12. Revert PR: stage the break-glass revert, leave it OPEN, never merge
- [ ] 13. Back-merge: PR release/<x.y.z> into dev, wait for green, merge with a merge commit
- [ ] 14. Clean up: delete release/<x.y.z> from origin
```

## Gates

- Step 0, excluded PRs: if any PRs are excluded, verify they are genuinely absent from `dev`'s history before step 2 (`git log origin/dev --oneline | grep '(#NNN)'`). If one is present, stop and ask the user.
- Step 1, no baseline tag: if this repo was live before its first tracked release, create the baseline retroactively (`git tag -a v<current> <main-sha> -m "..."`, push) so the new tag has something to diff against. Ask first; do not guess `<main-sha>`.
- Step 2, branch exists: `release/<x.y.z>` already on origin means a release is in flight. Stop and ask whether to resume or pick another version.
- Step 4, changelog: not optional. Release notes in step 11 come from this entry.
- Step 6, review: a scoped review of the release-risk surface (`git diff origin/main...release/<x.y.z>`) is optional but worth doing.
- Step 7, CI red: treat red as a genuine defect, not noise. Even if it is a latent test regression from an earlier PR, fix the test to match the intended behavior, push the fix to the release branch, and return to step 7. Never merge around it. If the same check is red after 3 fix rounds, stop and report.
- Step 8, merge blocked or conflicts with main: stop and ask. Never force-push or merge from the UI around a rule.
- Step 9, deploy or health probe red: stop and tell the user before any further step. The revert PR from step 12 is the rollback; staging it now is fine, merging it is the user's call.
- Step 10, tag: the tag does not trigger a second deploy, the merge already did that.
- Step 10, tag already exists: stop and ask. Never move or delete a pushed tag. If it already points at `<merge-sha>`, skip to step 11; if it points elsewhere, someone released this version already.
- Step 11, release exists: `gh release view v<x.y.z>` succeeding means skip creation and tell the user.
- Step 13, conflicts or red checks: if `dev` moved on and the back-merge conflicts, stop and ask before resolving. The release's version bump, changelog, and stabilization fixes must all survive, and merging keeps `dev` ahead of `main`. Red checks go back to the root-fix loop in step 7 logic. Do not do step 14 until the back-merge lands.

## Step 12: the break-glass revert PR

This is the rollback path: merging it reverts the release on `main` and redeploys whatever production was running before.

- `git switch -c revert/release-<x.y.z> origin/main`
- `git revert -m 1 <merge-sha> --no-edit`, a first-parent revert of the release merge.
- Push it and open a PR into `main` titled something like "Revert v<x.y.z> release (break-glass rollback)"; state plainly in the body that this is a pre-staged rollback, not to be merged unless production actually needs it.
- Leave it open. Don't merge it. It's the safety net someone can trigger in seconds if things go wrong in production.

Deleting `release/<x.y.z>` in step 14 is harmless to the revert PR, since it lives on its own branch.
