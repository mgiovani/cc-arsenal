# Architecture & Design Patterns (Agent 7)

Lens for the Architecture lane. Findings use the `AP-` prefix (AP-001, ...), dimension `AP`, lane `architecture`. Run on `model: sonnet`. Always on for every review.

## Contents

- [Rules](#rules)
- [Pattern catalog URLs](#pattern-catalog-urls)
- [Pain to pattern table](#pain-to-pattern-table)
- [Over-engineering counter-check](#over-engineering-counter-check)
- [Structure checks](#structure-checks)
- [Finding format](#finding-format)
- [Agent prompt](#agent-prompt)

## Rules

- Suggest a pattern only where the changed code shows the pain. No pain, no finding.
- Patterns are a vocabulary for a fix, not a goal. A smaller change that removes the pain beats a pattern.
- Review changed lines plus what they touch. Pre-existing structural problems in touched files go to the Pre-existing bucket.
- Apply the project-rule checklist first. A project rule about layering or file layout outranks a catalog pattern.

## Pattern catalog URLs

Catalog: https://refactoring.guru/design-patterns/catalog. One page per pattern: `https://refactoring.guru/design-patterns/<pattern>`, for example `adapter`, `strategy`, `state`, `null-object`, `chain-of-responsibility`, `facade`, `command`, `observer`, `factory-method`, `builder`, `decorator`.

Language examples: append `/python` or `/typescript` by the repo's main language, for example `https://refactoring.guru/design-patterns/adapter/typescript`. Detect the language from the changed files and the manifest (`pyproject.toml` vs `package.json`). For other languages use the base page.

Null Object has no catalog page. Cite the article instead: https://refactoring.guru/introduce-null-object.

Name the URL for the pattern you actually cite. Do not cite a pattern you did not map to a visible pain.

## Pain to pattern table

| Pain visible in the diff | Pattern | Target shape |
|---|---|---|
| Vendor SDK types or calls leak into domain or UI code | Adapter or Facade, with Dependency Inversion | Domain defines a small port; one module wraps the SDK behind it |
| Boolean flags or status strings that interact (`isLoading && !hasError && step === 2`), impossible combinations representable | State (or a discriminated union in TypeScript, a tagged dataclass union in Python) | One state value, one transition function |
| if/else or switch ladder choosing behavior by outcome, type or mode, growing with each feature | Strategy or Command | Map of key to handler; new case adds an entry, not a branch |
| Repeated `if (provider) ... else fallback` checks for an absent collaborator | Null Object | A no-op implementation of the same interface, chosen once at construction |
| Sequential guards (auth, rate limit, validation, feature gate) copy-pasted per handler | Chain of Responsibility (middleware, decorators, dependencies) | Ordered list of checks, each passes or stops |
| Many call sites reach through several subsystems for one operation | Facade | One entry function wrapping the sequence |
| Construction with many optional params or order-dependent setup | Builder, or a parameter object | Named fields, validated once |
| Object type chosen by scattered conditionals at creation | Factory Method | One creation function owns the choice |
| Same event fanned out by hand to several consumers | Observer (existing event emitter or signal) | Subscribe once; no producer edit per consumer |
| Cross-cutting behavior (logging, caching, retry) wrapped by copy at each call | Decorator | Wrapper applied at composition |

If the pain is not in this table, name the smell, not a pattern, and leave the fix to the CS lane.

## Over-engineering counter-check

Mandatory before emitting any AP finding. Agent 6 (Simplicity) reports the opposite direction, and the same code must not get both "add a pattern" and "remove an abstraction".

For each candidate AP finding, answer in order. Drop the finding on the first yes.

1. Would Agent 6 tag the code or the proposed result `[delete]`, `[unneeded]` or `[simplify]`? A one-implementation interface, a factory for one product, a pure-forwarding wrapper: the proposed pattern would create exactly these.
2. Does the code already have an equivalent helper or pattern elsewhere in the repo (`[reuse]`)? Point to it and extend it. Do not add a second mechanism.
3. Does the standard library (`[stdlib]`) or the framework or platform (`[builtin]`) already provide it? Use that.
4. Is there one call site, or two simple branches (a trivial two-branch `if`)? A pattern needs at least three variants or call sites, or a variant the diff shows being added next. "May need it later" is not pain.
5. Does the fix add more files, types or indirection than the pain it removes? Drop it.

When an AP candidate and an OE finding both land on the same lines, keep the OE finding and drop the AP one. Record the dropped candidates in a short "Rejected pattern suggestions" list with a one-line reason each, so the consolidation step can see the check ran.

## Structure checks

These need no catalog pattern. Report each as an AP finding with the concrete rule broken.

- Layering: UI code calling the database or HTTP client directly, domain code importing framework or transport types, a route handler holding business rules. Name the layer that should own it.
- Dependency direction: imports that point from stable core to volatile edge, circular imports between packages, a shared utility importing a feature module. Show the offending import line.
- Package placement: a new file whose responsibility belongs to another existing package or directory; a feature split across distant folders (Shotgun Surgery signal); a catch-all `utils` or `common` receiving domain logic. Follow the repo's existing layout, not an ideal one.
- Boundary leaks: ORM models or SDK response shapes returned across an API boundary, internal IDs or error strings exposed to clients.
- Cohesion: one module changed for unrelated reasons in this diff (Divergent Change signal).

Verify each by reading the import graph around the changed files (Grep the import lines) before reporting.

## Finding format

Each AP finding states:

1. The pain, with `path:line` evidence from the diff.
2. The pattern name and its URL, with the `/python` or `/typescript` page when the repo language has one. For structure checks, the layering rule broken.
3. A target sketch in the repo's language, 3 to 12 lines, using the repo's own names. Show the shape, not a full rewrite.
4. The counter-check result: one clause saying why this is not over-engineering (for example "three handlers already differ by mode, a fourth is in this diff").

Severity: Major when the structure breaks a project rule or causes a dependency cycle or layer violation; Minor when it adds cost to the next change; Nit for placement preferences. Never Critical.

Finding JSON: `{"id":"AP-001","path":"...","line":N,"side":"RIGHT","severity":"Major","dimension":"AP","title":"...","body":"...","preexisting":false,"verdict":null}`. Write `{"lane":"architecture","findings":[...]}` to `<scratch>/findings/architecture.json`.

## Agent prompt

```
Agent 7 - Architecture & Design Patterns:
- model: sonnet
- prompt: "Review [FILES_LIST] for architecture and design-pattern problems. If reviewing a PR/commit, analyze changed lines and read surrounding code for context.

Project rules (apply first, a violation is a finding): [RULE_CHECKLIST]

1. Detect the repo's main language (pyproject.toml vs package.json) to choose /python or /typescript example pages.
2. Read the changed files and Grep their import lines. Check layering, dependency direction, package placement, boundary leaks and cohesion.
3. Look for the pains in the pain-to-pattern table. For each, confirm the pain in code you read. Cite the pattern by name with its https://refactoring.guru/design-patterns/<pattern> URL.
4. Run the over-engineering counter-check on every candidate. Drop any that Agent 6 would tag [delete], [reuse], [stdlib], [builtin], [unneeded] or [simplify], and any with fewer than three variants or call sites.
5. For each surviving finding give: pain with path:line, pattern and URL, a short target sketch in the repo's language, and the counter-check clause.
6. Never suggest a pattern for a trivial two-branch conditional.

Write findings as JSON to [SCRATCH]/findings/architecture.json: {lane, findings:[{id (AP-NNN), path, line, side, severity, dimension:'AP', title, body, preexisting, verdict:null}]}. Include a 'Rejected pattern suggestions' list in your reply."
- subagent_type: "Explore"
```
