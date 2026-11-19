---
name: code-guidelines
description: "Generic coding rules for any language: the simplest complete change, comments only for a non-obvious why, guard clauses, immutable values, validation at trust boundaries, domain errors that name the fix, standard library before a dependency, test and Conventional Commit conventions, and a code-smell and refactoring catalog. Use when writing or changing code and the project has no stricter rule, or when asked about clean code, coding standards, naming, comments, error handling or test style. Not for stack-specific rules (use backend-guidelines or frontend-guidelines), for reviewing a diff (use review-code), or for performing a restructuring (use refactor)."
metadata:
  summary: "Generic coding rules for any language: simple changes, safe boundaries, tests, commits, smells"
---

# Code Guidelines

The project's own AGENTS.md or CLAUDE.md and its lint config win over this skill. Apply these rules only where the project is silent, and say so when you follow a project rule that differs.

Before the first edit, read the project's instruction files, its lint and formatter config, and the code next to the change. Find the real lint, type-check and test commands in the task runner (`justfile`, `Makefile`, package scripts) so you can run them at the end.

## Pick the reference

| What you are doing | Read |
|---|---|
| Deciding how much to build, splitting a function, planning a feature | [references/simplicity.md](references/simplicity.md) |
| Naming things, writing a comment, ordering imports, silencing a linter | [references/naming-and-comments.md](references/naming-and-comments.md) |
| Validating input, raising or catching errors, logging, writing files | [references/errors-and-boundaries.md](references/errors-and-boundaries.md) |
| Modelling values, enums, money, time, caches, migrations | [references/data-and-state.md](references/data-and-state.md) |
| Adding or choosing a dependency, drawing layer boundaries | [references/dependencies.md](references/dependencies.md) |
| Fixing a bug, writing or placing tests, claiming something is verified | [references/testing.md](references/testing.md) |
| Writing a commit, opening a PR, answering review comments | [references/commits-and-prs.md](references/commits-and-prs.md) |
| Naming a smell, picking the smallest refactoring, weighing a design pattern | [references/smells-and-patterns.md](references/smells-and-patterns.md) |

Read one reference per task. Read a second only when the task crosses both topics.

## Rules for every task

1. Make the simplest complete change. List every caller, test, fixture, config entry and export it must reach, then change only those. Say in one line what you left out on purpose.
2. Look in the repo, then the standard library, then the platform before writing a helper. A new dependency needs a written reason the standard library cannot meet.
3. Return early with a guard clause. Write no `else`. When the branches keep growing, use a dispatch map or polymorphism, not another `elif`.
4. Keep values frozen and functions pure. Build a new object instead of mutating one. Prefer composition to inheritance.
5. Comment only a non-obvious why: a workaround, a subtle constraint, a deliberate trade-off. When a comment feels needed, extract a function or constant whose name says the same thing.
6. Validate at trust boundaries: paths, names, request bodies, subprocess output, anything from outside the process. Never lose data silently. Create exclusively or refuse with a named error instead of checking and then writing.
7. A domain exception carries the facts the caller needs to act, and its message names the fix.
8. Fix the root cause, never the symptom. For a bug, find out why the tests missed it, write a test that fails because of the bug, then fix the code. Never rerun until green, raise a retry count or add a suppression to get a pass.
9. Test behaviour through the public API. Use a fake or the real thing before a mock. Mirror the source tree in the test tree.
10. Write Conventional Commits, one logical change each. Never skip a hook or a required check.
11. Add no AI attribution anywhere: no footer, no co-author trailer, no mention of an assistant, tool or prompt in code, commits or PR text.
12. Verify with the project's own lint and test commands before you call the work done. Report counts and exit codes from the run, never from memory.

## When rules clash

If two sources disagree, use this order: the project's written rules, the project's lint config, the code already there, then this skill. If the project's own files disagree with each other, follow the config that a tool enforces and mention the clash.

Where a shortcut has a known limit, write the limit and the trigger for lifting it as a why-comment. Do not leave TODO, FIXME or HACK markers: fix the cause, or open a tracked issue for work that is out of scope.
