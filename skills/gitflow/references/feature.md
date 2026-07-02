# Feature flow (new work bound for the next release)

A feature or fix branch is everyday work that lands on `dev` and ships later as part of a release. It never touches `main` directly and never deploys production on its own. Read the universal rails in `SKILL.md` first.

## 1. Branch from dev

- `git fetch origin && git switch -c feat/<short-desc> origin/dev` for a feature, or `fix/<short-desc>` for a bug fix. Match the type to the dominant Conventional Commit type the work will use.
- Keep the description short and kebab-case (e.g. `feat/csv-export`, `fix/pagination-off-by-one`).

## 2. Build it to the project's bar

- Implement with tests. The project's Definition-of-Done gate (lint, typecheck, tests with coverage thresholds, build, and any other required checks) is what the PR must pass, so write to that bar as you go rather than discovering gaps at the end.
- Follow Conventional Commits. Stage only intended files.
- Do **not** edit `CHANGELOG.md` here. The changelog is assembled at release time from the merged PRs, so per-feature edits just cause churn and merge conflicts. Write a clear PR title in Conventional Commit form instead; that subject becomes the changelog line.

## 3. Open the PR to dev

- Push and open a PR `feat/<short-desc>` (or `fix/...`) into `dev`.
- Run the full gate locally before asking for merge so you are not merging untested work onto the integration branch.
- Address review feedback and any red checks at the root. The same no-red bar applies; `dev` is shared.

## 4. Merge with a squash

- Merge into `dev` with a **squash merge**, so the PR lands as a single clean commit ending in `(#NNN)`. That subject is what shows up in the next release's changelog, so make it a good Conventional Commit line.
- Delete the branch after merge.

## When this becomes a release

Once enough has accumulated on `dev`, promoting it to production is the **release** flow, not this one. Switch to `references/release.md`.
