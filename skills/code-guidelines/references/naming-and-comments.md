# Naming and comments

## Comments

Clean code explains itself. No comment restates what the code says.

Comment only a non-obvious why: a workaround, a subtle constraint, a deliberate trade-off. Keep it to one or two lines.

When a comment feels necessary, extract a function or constant whose name carries the same message. Do that first.

Some projects ban comments and docstrings outright and enforce it with a lint rule. If the project's config does, follow it: the extracted name is then the only documentation.

Other rules for comments:

- No docstrings on private helpers.
- A public function or class may take a one-line note that states behaviour or a constraint, unless the project bans them.
- Tool directives stay (shebang, `# syntax=`).
- Stand-in text is a defect: "example usage", "for demonstration purposes", "replace with your actual", "logic would go here". Move demos into tests or docs.
- Evidence belongs in the commit message or PR body: measurements, issue numbers, rejected alternatives. Code comments stay about the code.
- A deliberate shortcut says its limit and the trigger for lifting it, in one why-comment.

## Names

- Use one term for one concept. A second word for the same idea ("config" and "settings") is a defect. Keep the project's vocabulary and coin no synonyms.
- Name a thing for what it means, not its type or its value. Tokens take a role (`surface`, `action`) and not a value (`blue-800`), because a value name stops being true when a theme changes.
- Booleans take `is`, `has`, `can` or `should`. Event handlers take `handle`, and props that accept a handler take `on`.
- Use no single-letter names except a loop index or a lambda parameter.
- Follow the file's own case convention. Do not mix camelCase and snake_case in one file.
- Test names are full sentences of behaviour.
- Constants are `UPPER_SNAKE` at the top of the module, and a bare number in code gets a named constant.
- Keep the project's language for identifiers, logs, messages and test names. Default to English for code, and let user-facing text follow the product language.

## Imports and modules

- Import from the module that defines the name. Keep Python `__init__.py` files empty, with no re-exports.
- Use absolute imports inside the package. No wildcard imports.
- A module or package appears when something uses it. Name a module for its role (`models`, `service`, `exceptions`) and give a concept its own module once it has its own vocabulary.

## Suppressions

A lint suppression, `@ts-ignore`, `# type: ignore` or `eslint-disable` is a red flag, not a fix. Fix the root cause first, even for a nit.

If the project allows a suppression, scope it to one rule code and add the reason on the same line. Never add one to make a run pass. If a type stub gap forces one, stop and report it instead of silencing the error.

## Prose in code, docs and messages

- No em dashes. Use a colon to introduce an explanation, a comma for an aside, and a period or semicolon between full clauses.
- Use no decorative separators (middle dot, bullet, arrow) between tokens in UI text.
- Keep sentences short. One concept, one term, within a section.
- Formatting belongs to the formatter. Nobody formats by hand.
