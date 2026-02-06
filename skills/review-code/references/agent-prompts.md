# Code Review - Agent Prompts & Patterns

Detailed grep patterns and agent prompts for each review dimension. Load this reference when running Phase 3 parallel specialist review.

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

For each finding:
1. Read the file to verify the issue in context
2. Determine if the pattern is actually a bug (not an intentional design choice)
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain the specific bug scenario and potential impact
5. Classify severity: Critical (data loss/crash), Major (incorrect behavior), Minor (edge case), Nit (style)
6. Provide a concrete fix with code example

Return structured findings with file path, line numbers, severity, code snippet, explanation, and fix suggestion."
- subagent_type: "Explore"
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

For each finding:
1. Read the file to verify the issue in context
2. Check if the pattern matches the project's conventions (do not flag intentional choices)
3. Extract exact code snippet (5-10 lines) with file:line reference
4. Explain why the pattern is problematic for maintainability
5. Classify severity: Critical (architectural issue), Major (significant maintainability risk), Minor (readability improvement), Nit (style preference)
6. Provide a refactored alternative with code example

Return structured findings with file path, line numbers, severity, code snippet, explanation, and suggested improvement."
- subagent_type: "Explore"
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
```

## Review Best Practices by Audience

### For Code Authors
1. **Address Critical/Major first**: Fix issues that affect correctness and reliability
2. **Understand the why**: Learn the reasoning behind each finding before fixing
3. **Request re-review**: Run the skill again after fixes for diff-only validation
4. **Push back on Nits**: Not every suggestion needs to be accepted
5. **Add tests for bugs found**: Each correctness finding should have a regression test

### For Reviewers
1. **Validate findings**: Verify each finding is a genuine issue, not a false positive
2. **Consider context**: Some patterns are acceptable in specific contexts
3. **Prioritize**: Not every finding needs to block a PR
4. **Be constructive**: Focus on the code, not the author
5. **Acknowledge good work**: Highlight well-written code and patterns

### For Tech Leads
1. **Track trends**: Monitor recurring issue types across reviews
2. **Update standards**: Use findings to improve coding guidelines
3. **Share learnings**: Use reviews as teaching opportunities
4. **Calibrate severity**: Ensure severity ratings match team standards
5. **Automate what you can**: Add linting rules for frequently caught patterns
