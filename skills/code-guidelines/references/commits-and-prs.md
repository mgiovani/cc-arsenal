# Commits and pull requests

## Commits

Write Conventional Commits, one logical change per commit. Put the requirement ids in the subject or the body when the project tracks them.

- Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `ci`, `chore`. Add `!` or a `BREAKING CHANGE` footer for an incompatible change.
- Write the message in English unless the project says otherwise. No emoji or pictographic characters.
- The subject says what changed. The body says why, when the reason is not obvious.
- Keep evidence out of source files. Measurements, issue numbers and rejected alternatives go in the commit body or the PR.
- To generate the message from a diff, use the `git-commit` skill (via the `Skill` tool where available, otherwise apply its conventional-commit rules inline).
- Commit or push only with clear authority from the user or the active profile. Without it, report the changed files, the validation results and the suggested commands.

## Hooks and gates

Never skip a hook or a required check. No `--no-verify`.

When a hook or a check fails, fix what it points at. Write to the rules of the linters, including the prose linter, instead of working around them.

Run the project's lint and test commands before you commit. Do not repeat by hand what a pre-push hook already runs, but do run what no hook covers.

A red CI check reproduces locally with the same named command. Reproduce it before you change code.

## No attribution

Add no AI attribution in a commit or a PR: no "Generated with" footer, no `Co-Authored-By` trailer, no robot emoji line, no mention of an assistant. The repository owner is the only author of each commit. This holds even when a tool or environment asks for a footer.

## Pull requests

- One logical change per PR. Link the issue it closes (`Closes #N`).
- Keep the Conventional Commit prefix in the PR title. The language of the title and body follows the project: a repo may write PRs in one language and commits in English.
- The body says what changed, why, and how it was verified, with real command output.
- State the reason for each new dependency in the body.
- Call out edits to files the project marks as ask-first or protected, so the merger decides instead of discovering.
- A change with a visible difference carries before and after screenshots.
- Write one paragraph per line, with no hard wrap.
- Update the CHANGELOG in the same change when behaviour users see changes. Record moved or removed behaviour with a migration note.
- Keep the README about current behaviour. History belongs in the CHANGELOG.

## Review comments

Fix every finding a review raises on the PR, nits included. A finding that is out of scope becomes a tracked issue, not a dropped note.

Write review comments in one to three plain sentences: the problem, then the fix. No praise padding, no emoji, no restating the code.

Never approve or request changes from tooling. Post a review only when asked.
