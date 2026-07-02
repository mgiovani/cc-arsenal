# CHANGELOG.md format

`CHANGELOG.md` is updated during a release and a hotfix, never per-feature. It follows Keep a Changelog with entries grouped by Conventional Commit type, so the lines come straight from the merged PR subjects.

## Structure

The file opens with a fixed preamble, then one section per version, newest first:

```markdown
# Changelog

All notable changes to this project are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with entries grouped by [Conventional Commit](https://www.conventionalcommits.org/) type.

## [<x.y.z>] - <YYYY-MM-DD>

<One short paragraph summarizing the release. For a hotfix, one sentence on what it fixes.>

### Features

- feat(scope): subject of the PR (#NNN)

### Bug Fixes

- fix(scope): subject of the PR (#NNN)

### Tests, Build, and Tooling

- test/ci/chore/build/refactor lines worth surfacing
```

## How to assemble an entry

- Group the in-scope PRs by their Conventional Commit type. `feat` goes under Features, `fix` under Bug Fixes, and `test`/`ci`/`chore`/`build`/`refactor`/`perf` under a combined "Tests, Build, and Tooling" section (or their own `### Tests`, `### CI`, etc. if there are enough to warrant it; match what the existing file already does).
- Each bullet is the full Conventional Commit subject including scope and the `(#NNN)` PR number. Reuse the PR's squashed commit subject verbatim where you can; that is why feature PRs are squash-merged with a clean subject.
- Order within a section by significance, not strictly by PR number; lead with the changes a reader most cares about.
- Use the real merge date for the heading.

## Rules carried from the universal rails

- Keep commit messages, the changelog, and release notes clean and professional. The changelog is customer-and-team facing.
- Keep the summary paragraph concrete and plain. State what shipped, not how it was built.
- Only describe what is actually in scope for this version. If a PR was deliberately excluded from the release, it does not appear until the release that includes it.
