# Code Review - Agent Prompts & Patterns

Detailed grep patterns and agent prompts for each review dimension. Load this reference when fanning out the core agents. Agent 7 (architecture) lives in `architecture-patterns.md`.

## Contents

- [Shared preamble](#shared-preamble)
- [Agent 1 - Correctness & Logic](#agent-1---correctness--logic)
- [Agent 2 - Performance](#agent-2---performance)
- [Agent 3 - Code Style & Patterns](#agent-3---code-style--patterns)
- [Agent 4 - Test Coverage Gaps](#agent-4---test-coverage-gaps)
- [Agent 5 - Error Handling & Edge Cases](#agent-5---error-handling--edge-cases)
- [Agent 6 - Simplicity & Over-engineering](#agent-6---simplicity--over-engineering)
- [Review Best Practices by Audience](#review-best-practices-by-audience)

## Shared preamble

Prepend this block to every agent prompt below, filling the bracketed values. Every Agent call also sets `model` explicitly (all lanes here use `sonnet`). `[LANE]` is the lane name; each core agent uses its own `core-<prefix>` (`core-cl`, `core-pf`, `core-cs`, `core-tc`, `core-eh`, `core-oe`) so parallel agents never write the same file.

```
Project rules (numbered checklist extracted from AGENTS.md / CLAUDE.md / .claude/skills):
[RULES_CHECKLIST]
A violation of a numbered rule is a finding, cited by rule number. Report every violation, Nit included. Do not silently pass anything.

Diff hunks (from the base...HEAD diff): [HUNK_RANGES]
A hunk header @@ -a,b +c,d @@ covers new-file lines c..c+d-1. A finding whose line falls outside every hunk of its file is preexisting: true. Otherwise preexisting: false.

Output: write [SCRATCH]/findings/[LANE].json as {"lane": "[LANE]", "findings": [...]}, one object per finding:
{"id": "<PREFIX>-001", "path": "...", "line": 12, "side": "RIGHT", "severity": "Critical|Major|Minor|Nit", "dimension": "<PREFIX>", "title": "...", "body": "problem, then fix, with a short snippet", "preexisting": false, "verdict": null, "reason": null}
Use the file path relative to the repo root and a new-file line number. IDs count up per prefix. Leave verdict and reason null; the verification step sets them.
```

## Contents

- [Agent 1 - Correctness & Logic](#agent-1---correctness--logic)
- [Agent 2 - Performance](#agent-2---performance)
- [Agent 3 - Code Style & Patterns](#agent-3---code-style--patterns)
- [Agent 4 - Test Coverage Gaps](#agent-4---test-coverage-gaps)
- [Agent 5 - Error Handling & Edge Cases](#agent-5---error-handling--edge-cases)
- [Agent 6 - Simplicity & Over-engineering](#agent-6---simplicity--over-engineering)
- [Review Best Practices by Audience](#review-best-practices-by-audience)

## Agent 1 - Correctness & Logic

```
Agent 1 - Correctness & Logic Analysis:
- prompt: "Scan for correctness and logic issues in [FILES_LIST]. If reviewing a PR/commit, focus analysis on changed lines while using surrounding code for context.

**Bug Patterns:**
Use Grep to search for:

*Off-by-one and boundary errors:*
- < len\( where <= len\( may be needed (or vice versa)
- range\(.*-1\) or range\(.*\+1\) — verify boundary correctness
- \[.*-1\] or \[.*\+1\] — array index edge cases
- i < arr.length vs i <= arr.length patterns

*Null/undefined safety:*
- \.(\w+)\. chains without null checks (long property chains)
- Optional chaining missing: accessing .property without ?. in TypeScript/JavaScript
- None checks missing after .get(), .find(), dict[key] in Python
- Potential NoneType or TypeError from unchecked returns

*Type mismatches and coercion:*
- == instead of === in JavaScript (loose equality)
- str() + int() concatenation without conversion in Python
- Implicit type coercion in comparisons
- parseInt without radix parameter

*Race conditions and concurrency:*
- Shared mutable state without locks/synchronization
- async/await missing: calling async function without await
- TOCTOU (time-of-check-time-of-use) patterns
- Non-atomic read-modify-write sequences

*Logic errors:*
- Inverted conditions: if (!condition) with wrong branch
- Short-circuit evaluation issues: && and || precedence
- Unreachable code after return/break/continue
- Variable shadowing in nested scopes
- Mutation of function parameters (unintended side effects)

*Copy-paste errors:*
- Duplicate conditions in if/else chains
- Same variable assigned twice without use between
- Identical branches in conditional logic

*State, routing and lifecycle (CL):*
- Module-level mutable latches: a top-level let/var or singleton flag set once and never reset (leaks across users, tests and hot reloads)
- map[code] ?? 'fallback' (or dict.get(code, default)) that routes an unknown error code to the wrong UI state or handler; unknown input should hit an explicit unknown branch
- Stringly-typed state allowing impossible combinations (status: string plus nullable data and error); suggest a discriminated union
- Cache or query client not fully cleared on identity change, 401, or sign-out (shared-workstation data leak); check queryClient.clear/removeQueries, store resets, and persisted storage
- Production config silently falling back to dev endpoints or dev keys when an env var is missing; prod should fail fast

For each finding:
1. Read the file to verify the issue in context
2. Determine if the pattern is actually a bug (not an intentional design choice)
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain the specific bug scenario and potential impact
5. Classify severity: Critical (data loss/crash), Major (incorrect behavior), Minor (edge case), Nit (style)
6. Provide a concrete fix with code example

Return structured findings with file path, line numbers, severity, code snippet, explanation, and fix suggestion."
- subagent_type: "Explore"
- model: "sonnet"
```

## Agent 2 - Performance

```
Agent 2 - Performance Analysis:
- prompt: "Scan for performance issues in [FILES_LIST]. If reviewing a PR/commit, focus analysis on changed lines while using surrounding code for context.

**Performance Patterns:**
Use Grep to search for:

*Algorithmic complexity:*
- Nested loops over collections: for.*for.*in (potential O(n²))
- .filter\(.*\).map\( or .map\(.*\).filter\( — redundant iterations
- .find\( inside loops — linear search in a loop (O(n²))
- Array.includes or .indexOf inside loops
- Repeated .sort() calls on same data
- String concatenation in loops (use StringBuilder/join)

*Database and query issues:*
- N+1 query patterns: queries inside loops (for.*query, for.*await.*find)
- SELECT \* — fetching all columns when only few needed
- Missing pagination: .find\(\) or .findAll\(\) without limit
- Missing indexes: queries filtering on non-indexed fields
- Unbounded queries without LIMIT

*Memory and resource leaks:*
- Event listeners added without removal: addEventListener without removeEventListener
- setInterval without clearInterval
- Open file handles without close/context manager
- Growing arrays/maps without bounds (cache without eviction)
- Large objects held in closure scope

*Unnecessary allocations:*
- Object/array creation inside loops
- Regex compilation inside loops: new RegExp\( or re.compile\( in loop body
- String template literals or format strings in hot paths
- Creating Date/moment objects repeatedly

*Missing caching and memoization:*
- Repeated expensive computations with same inputs
- API calls for static data without caching
- File reads in request handlers without caching
- Missing useMemo/useCallback for expensive React renders

*Async and I/O patterns:*
- Sequential awaits that could be parallel: multiple await statements that are independent
- Synchronous I/O in async context: fs.readFileSync in async function
- Missing connection pooling for database/HTTP clients
- Unbounded Promise.all with large arrays (use batching)

For each finding:
1. Read the file to verify the pattern and understand the context
2. Assess the actual performance impact (hot path vs. cold path, data volume)
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain the performance implication with estimated complexity
5. Classify severity: Critical (system-level impact), Major (noticeable degradation), Minor (optimization opportunity), Nit (micro-optimization)
6. Provide a concrete optimized alternative with code example

Return structured findings with file path, line numbers, severity, code snippet, explanation, and optimized code."
- subagent_type: "Explore"
- model: "sonnet"
```

## Agent 3 - Code Style & Patterns

```
Agent 3 - Code Style & Patterns Analysis:
- prompt: "Scan for code style and pattern issues in [FILES_LIST]. If reviewing a PR/commit, focus analysis on changed lines while using surrounding code for context.

**IMPORTANT**: Before flagging style issues, understand the project's existing conventions by reading configuration files (.eslintrc, .prettierrc, ruff.toml, pyproject.toml) and observing patterns in existing code. Only flag deviations from the project's own standards.

**Style & Pattern Issues:**
Use Grep to search for:

*DRY violations:*
- Nearly identical code blocks (>5 lines) in multiple locations
- Repeated magic numbers or string literals
- Copy-pasted logic with minor variations
- Duplicated validation logic across handlers

*SOLID violations:*
- God classes/modules: files >500 lines with mixed responsibilities
- Functions with >5 parameters (possible object parameter needed)
- Functions >50 lines (possible decomposition needed)
- Direct instantiation instead of dependency injection in key classes
- Switch/if-else chains on type (Open-Closed Principle violation)

*Naming and readability:*
- Single-letter variables outside of loops/lambdas: [^for.*]\b[a-z]\b\s*=
- Inconsistent naming: camelCase mixed with snake_case in same file
- Boolean naming: is/has/should prefix missing on boolean variables
- Misleading names: variable name suggests different type/purpose than actual usage
- Abbreviations that harm readability

*Framework idiom violations:*
- React: useEffect with missing dependencies, state updates in render, prop drilling >3 levels
- Express/Fastify: middleware not using next(), error handler without 4 params
- Django: raw SQL instead of ORM, missing model Meta, N+1 in templates
- Go: error not checked, returning error and value without checking error first
- Python: mutable default arguments, bare except, manual resource management instead of context manager

*Import and module organization:*
- Circular imports or dependency cycles
- Wildcard imports: from module import *, import * from
- Unused imports (if not caught by linter)
- Deeply nested relative imports

*Dead code:*
- Commented-out code blocks (>3 lines)
- Unused functions/classes (never called/referenced)
- Unreachable branches
- TODO/FIXME/HACK comments older than the review scope

*Code smell catalog (refactoring.guru):*
Map each smell to its named fix technique and cite the URL in the finding. Report every smell you can anchor to a line, Nit included.
- Long Method, Large Class, Primitive Obsession, Long Parameter List, Data Clumps: Extract Method (https://refactoring.guru/extract-method), Extract Class (https://refactoring.guru/extract-class), Introduce Parameter Object (https://refactoring.guru/introduce-parameter-object), Replace Primitive with Object
- Switch Statements, repeated type-code conditionals: Replace Conditional with Polymorphism (https://refactoring.guru/replace-conditional-with-polymorphism)
- Duplicate Code: Extract Method, Pull Up Method (https://refactoring.guru/smells/duplicate-code)
- Feature Envy, Message Chains, Middle Man: Move Method (https://refactoring.guru/move-method), Hide Delegate, Remove Middle Man
- Temporary Field, Speculative Generality, Dead Code, Lazy Class: Remove or inline (https://refactoring.guru/smells/speculative-generality)
- Comments that restate code or explain a confusing block: Extract Method, Rename Method
- Cross-file smells (read the callers and siblings, not just the changed file):
  - Shotgun Surgery: one logical change forces edits in many files (https://refactoring.guru/smells/shotgun-surgery); fix with Move Method / Inline Class
  - Divergent Change: one module changes for unrelated reasons (https://refactoring.guru/smells/divergent-change); fix with Extract Class
  - Parallel tables for one concept: two or more maps, enums or switch statements keyed by the same set of values that must be edited together; fold into one table or a polymorphic object
  - Inappropriate Intimacy: one module reaching into another's internals, for example a hook that exposes or leaks setState (https://refactoring.guru/smells/inappropriate-intimacy); fix with Move Method or Hide Delegate

For each finding:
1. Read the file to verify the issue in context
2. Check if the pattern matches the project's conventions (do not flag intentional choices)
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain why the pattern is problematic for maintainability
5. For a smell, name it and the fix technique, and include its refactoring.guru URL
6. Classify severity: Critical (architectural issue), Major (significant maintainability risk), Minor (readability improvement), Nit (style preference)
7. Provide a refactored alternative with code example

Return structured findings with file path, line numbers, severity, code snippet, explanation, and suggested improvement."
- subagent_type: "Explore"
- model: "sonnet"
```

## Agent 4 - Test Coverage Gaps

```
Agent 4 - Test Coverage Gap Analysis:
- prompt: "Analyze test coverage gaps in [FILES_LIST]. If reviewing a PR/commit, focus on whether new/changed code has adequate test coverage.

**Test Coverage Analysis:**

*Step 1: Map source files to test files*
Use Glob to discover test files:
- **/*.test.{js,ts,tsx}, **/*.spec.{js,ts,tsx}
- **/test_*.py, **/*_test.py, **/tests/*.py
- **/*_test.go, **/tests/**
- Match each source file to its corresponding test file

*Step 2: Identify untested source files*
For each source file in scope:
- Check if a corresponding test file exists
- If no test file exists, flag as Critical (for business logic) or Major (for utilities)

*Step 3: Analyze test quality in existing test files*
Use Grep and Read to check for:

*Missing test scenarios:*
- Happy path only: tests that only check success cases
- Missing error path tests: no tests for thrown exceptions or error returns
- Missing boundary tests: no tests for empty input, null, zero, max values
- Missing integration: unit tests only, no integration or E2E coverage for critical flows

*Weak assertions:*
- toBeTruthy/toBeFalsy instead of specific value checks
- assert True or self.assertTrue without meaningful condition
- Missing assertion count: test functions without any assert/expect
- Snapshot-only tests without behavioral assertions

*Test anti-patterns:*
- Tests depending on execution order
- Shared mutable state between tests (missing setup/teardown)
- Tests that always pass (tautological assertions)
- Excessive mocking that tests implementation rather than behavior
- Tests that test the framework rather than the application code
- Flaky indicators: setTimeout, sleep, retry in tests
- Vacuous absence assertions: expect(...).not.toBeInTheDocument / queryBy* / toBeNull / not.toHaveBeenCalled that runs before the async work resolves, so it passes whether or not the code works; require awaiting the settled state first (waitFor, findBy*, flushPromises) or asserting the positive outcome
- Class-name or CSS-selector assertions (toHaveClass, querySelector('.x')) that test implementation rather than behavior or accessible output
- Safety validators (sanitizers, allowlists, URL or path checks) tested only against a hard-coded probe list; require property-style or adversarial cases (encodings, case variants, nested and boundary inputs)

*Coverage gaps for common patterns:*
- Public API methods without tests
- Error handling branches without tests
- Conditional logic branches (if/else, switch) without tests for each branch
- Async error paths: missing tests for rejected promises or failed async operations
- Edge cases: empty arrays, null inputs, boundary values, unicode, special characters

For each finding:
1. Read both the source file and its test file (if exists)
2. Identify specific untested code paths or scenarios
3. Reference the source code line that lacks coverage
4. Classify severity: Critical (untested business logic), Major (untested error paths), Minor (untested edge cases), Nit (additional coverage nice-to-have)
5. Provide a concrete test case example with code

Return structured findings with source file:line reference, missing test scenario description, severity, and example test code."
- subagent_type: "Explore"
- model: "sonnet"
```

## Agent 5 - Error Handling & Edge Cases

```
Agent 5 - Error Handling & Edge Cases Analysis:
- prompt: "Scan for error handling and edge case issues in [FILES_LIST]. If reviewing a PR/commit, focus analysis on changed lines while using surrounding code for context.

**Error Handling Patterns:**
Use Grep to search for:

*Missing error handling:*
- Promises without .catch(): \.then\( without \.catch\(
- Async calls without try/catch: await without surrounding try
- Error callbacks ignored: function\(err.*\)\s*\{ without err check
- Go errors unchecked: _, err := or err := without if err != nil
- Python: calls that can raise without try/except in appropriate scope

*Poor error handling:*
- Empty catch blocks: catch\s*\(.*\)\s*\{\s*\} or except.*:\s*pass
- Swallowed errors: catch that only logs without re-throwing or handling
- Generic catches: catch\(Exception\), except Exception:, catch\(e\) that handle all errors identically
- console.log in catch instead of proper error reporting
- Error messages without context: throw new Error\( with generic message

*Input validation gaps:*
- Missing parameter validation at function entry points
- No type checking for external inputs (API request bodies, query params)
- Missing length/size limits on string/array inputs
- Missing range validation for numeric inputs
- No sanitization of user-provided file paths or URLs
- Missing content-type validation for file uploads

*Boundary conditions:*
- Division by zero: / without zero check on denominator
- Empty collection access: \[0\] or .first without empty check
- Integer overflow potential: unchecked arithmetic on user input
- String operations on potentially empty/null strings
- Date/time edge cases: timezone handling, daylight saving, leap year

*Graceful degradation:*
- Missing fallback for external service calls
- No timeout configuration for HTTP requests or database queries
- Missing retry logic for transient failures
- No circuit breaker for cascading failure prevention
- Missing default values for optional configuration

*Resource cleanup:*
- Missing finally blocks for resource cleanup
- Database connections not closed in error paths
- File handles left open after exceptions
- Missing cleanup in React useEffect return

For each finding:
1. Read the file to verify the pattern and understand the error handling context
2. Assess the impact: what happens when the error/edge case occurs?
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain the specific failure scenario
5. Classify severity: Critical (crashes/data loss on error), Major (poor user experience on error), Minor (missing robustness), Nit (defensive improvement)
6. Provide a concrete fix with proper error handling code

Return structured findings with file path, line numbers, severity, code snippet, failure scenario, and fix code."
- subagent_type: "Explore"
- model: "sonnet"
```

## Agent 6 - Simplicity & Over-engineering

```
Agent 6 - Simplicity & Over-Engineering (Explore, Sonnet):
  prompt: "Review [SCOPE] for unnecessary complexity — code that does more than the
    current, concrete requirement needs.

    1. Grep for interfaces/abstract classes/protocols with exactly one concrete
       implementation, factories that construct exactly one product, wrapper
       functions or classes that only forward calls without adding behavior, and
       configuration flags or parameters that no caller ever varies.
    2. Read each match plus surrounding context to confirm it's genuinely
       unnecessary, not a documented extension point for a real second caller or
       plugin contract.
    3. Before flagging something as speculative, check whether equivalent behavior
       already exists — in this codebase (search first), the standard library, or
       the framework/platform in use.
    4. Classify each confirmed finding with exactly one tag:
       - [delete] — dead/unused code with no live caller
       - [reuse] — equivalent logic already exists elsewhere in this codebase
       - [stdlib] — the standard library already covers it
       - [builtin] — the framework/platform already provides it
       - [unneeded] — speculative code with no current caller (unused flag,
         unexercised branch, extension point nobody extends)
       - [simplify] — a one-implementation interface/factory, or a pure-forwarding
         wrapper, that should be inlined or merged
    5. If a finding is really a correctness bug, a security hole, or a performance
       problem rather than just unnecessary complexity, do NOT tag it here — note
       it separately as out-of-scope-for-OE so it can be routed to the
       Correctness, Performance, or Error Handling reviewer instead. Complexity
       must never be used to mask, or be mistaken for, a real bug.
    6. For each finding report: file:line, the one tag, a one-sentence description
       of what's unnecessary and why, the suggested deletion or replacement, and
       the number of lines that change would remove.
    7. Sum the lines-removed across findings you are confident about, from code you
       actually read — not estimated. Report that sum as a static count only. Do
       not state or imply runtime, token, bundle-size, or percentage savings: the
       simplified version was never built or run, so there is no measured baseline
       to compare against. If a real benchmark already exists in the codebase for
       the code in question, you may cite it — otherwise say nothing about
       performance impact."
  subagent_type: "Explore"
  model: "sonnet"
```

Counter-check with Agent 7: Agent 7 (`architecture-patterns.md`) may suggest adding a pattern, Agent 6 may suggest removing an abstraction. Both use the same tag vocabulary above so the consolidator can spot a clash. Agent 7 must not recommend a pattern for code Agent 6 tags [delete], [unneeded] or [simplify], and Agent 6 must not tag [simplify] on an Adapter, State or Strategy that Agent 7 justifies by a concrete pain in the diff. When both flag the same lines, keep one finding and prefer the removal unless the pain is demonstrated in code.

Report Addendum (Phase 4/5): add a sixth dimension, Simplicity & Over-engineering, finding prefix `OE-`, default severity Minor or Nit (escalate to Major only when the complexity itself causes a reliability/maintainability failure, not merely because it exists). Per-finding fields: severity, `file:line`, the single tag, description, suggested deletion/replacement, lines-removed. Report the aggregate separately:

> Estimated lines removable (static count, not a benchmark): ~N

`N` is the sum of lines-removed across all `OE-` findings, counted from code actually read. Never state or imply a percentage, runtime, token, or bundle-size saving next to this number: no leaner version was built or measured. If a real, previously-measured benchmark exists for the flagged code, cite it instead of inventing a figure.

## Review Best Practices by Audience

### For code authors

| Practice | Detail |
|----------|--------|
| Address Critical/Major first | fix issues that affect correctness and reliability |
| Understand the why | learn the reasoning behind each finding before fixing |
| Request re-review | run the skill again after fixes, it re-derives the current diff and re-scopes on its own |
| Push back on Nits | not every suggestion needs to be accepted |
| Add tests for bugs found | each correctness finding should have a regression test |

### For reviewers

| Practice | Detail |
|----------|--------|
| Validate findings | verify each finding is a genuine issue, not a false positive |
| Consider context | some patterns are acceptable in specific contexts |
| Prioritize | not every finding needs to block a PR |
| Be constructive | focus on the code, not the author |
| Acknowledge good work | highlight well-written code and patterns |

### For tech leads

| Practice | Detail |
|----------|--------|
| Track trends | monitor recurring issue types across reviews |
| Update standards | use findings to improve coding guidelines |
| Share learnings | use reviews as teaching opportunities |
| Calibrate severity | ensure severity ratings match team standards |
| Automate what you can | add linting rules for frequently caught patterns |
