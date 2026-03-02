# Common Issues in SaaS Codebases

Catalog of frequently found issues during code review of SaaS applications. Each entry includes detection hints and recommended resolution approach.

---

## Category 1: API Design

### 1.1 Inconsistent Error Response Format

**Description**: Different endpoints return errors in different shapes (`{error: "..."}`, `{message: "..."}`, `{detail: "..."}`, plain strings).

**Detection**: Compare error responses across 3+ endpoints for inconsistency.

**Resolution**: Establish a single error response schema used everywhere:
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
```

### 1.2 Leaking Internal Details in Errors

**Description**: Stack traces, SQL query text, or internal identifiers returned to API clients.

**Detection**: Look for exception handlers that return `error.message` or `error.stack` directly.

**Resolution**: Log the full error internally; return a sanitized message to clients.

### 1.3 Missing Pagination on List Endpoints

**Description**: List endpoints return all records without pagination, causing timeouts as data grows.

**Detection**: List endpoints that return arrays without `limit`/`offset` or cursor parameters.

**Resolution**: Add mandatory pagination with a maximum page size; return pagination metadata.

### 1.4 Wrong HTTP Methods or Status Codes

**Description**: Using GET for mutations, returning 200 for created resources, returning 200 for not-found instead of 404.

**Detection**: Check that: POST creates (201), PUT/PATCH updates (200), DELETE removes (204), GET reads (200).

---

## Category 2: Authentication & Session Management

### 2.1 Tokens Stored in localStorage

**Description**: JWT or session tokens stored in `localStorage` are accessible to any JavaScript on the page, making them vulnerable to XSS.

**Detection**: Search for `localStorage.setItem` with token-related keys.

**Resolution**: Use `httpOnly` cookies for session tokens.

### 2.2 No Token Expiry Validation

**Description**: Tokens accepted regardless of expiry claim, or expiry not checked server-side.

**Detection**: JWT decode/verify code that does not check `exp` claim.

**Resolution**: Verify `exp` claim on every request; implement refresh token flow.

### 2.3 Session Not Invalidated on Logout

**Description**: Logging out only removes the client-side token but does not invalidate the server-side session.

**Detection**: Logout handler that only sends a "clear cookie" response without any server-side session revocation.

**Resolution**: Maintain a revocation list or implement short-lived tokens with server-side session store.

---

## Category 3: Database Access

### 3.1 N+1 Query Pattern

**Description**: A list of N items is fetched, then for each item, a separate query is made, resulting in N+1 total queries.

**Detection**: Loops that execute database queries on each iteration.

```python
# BAD
users = db.query("SELECT * FROM users")
for user in users:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")
```

**Resolution**: Use JOIN queries, ORM eager loading (`.include()`, `.prefetch_related()`), or batch loading.

### 3.2 Missing Database Indexes

**Description**: Queries filter or sort on columns without indexes, causing full table scans.

**Detection**: WHERE clauses on columns that lack index definitions in migration files.

**Resolution**: Add index to frequently filtered/sorted columns, especially foreign keys and status fields.

### 3.3 Raw SQL with String Interpolation

**Description**: SQL queries constructed via string concatenation with user-supplied values.

**Detection**: String format operations inside database query calls.

**Resolution**: Use parameterized queries or ORM abstractions exclusively.

### 3.4 Transactions Not Used for Multi-Step Operations

**Description**: Multiple related database operations executed without a transaction, leaving data partially updated on failure.

**Detection**: Functions that call multiple write operations without transaction wrapping.

**Resolution**: Wrap related writes in a database transaction.

---

## Category 4: Async & Concurrency

### 4.1 Unhandled Promise Rejections

**Description**: Async operations that can reject are called without `.catch()` or try/catch, causing silent failures.

**Detection**: `.then()` chains without `.catch()`, `async` functions called without `await` or error handling.

**Resolution**: Always handle rejections explicitly; use global unhandled rejection handlers as a safety net.

### 4.2 Shared Mutable State in Concurrent Operations

**Description**: Multiple async operations modifying the same in-memory object, leading to race conditions.

**Detection**: Multiple concurrent operations reading and writing the same variable or object property.

**Resolution**: Use atomic operations, locks, or redesign to avoid shared state.

### 4.3 Background Jobs Without Idempotency

**Description**: Background jobs that create side effects (emails, charges, database records) are not idempotent, causing duplicate actions on retry.

**Detection**: Job handlers without idempotency keys or duplicate-check logic.

**Resolution**: Design jobs to be safe to run multiple times; use idempotency keys for external operations.

---

## Category 5: Frontend / UI

### 5.1 No Loading States

**Description**: Async operations triggered by user actions provide no feedback during execution.

**Detection**: Event handlers that call async functions without setting loading state.

**Resolution**: Show loading indicators; disable submit buttons during pending operations.

### 5.2 No Optimistic Update Rollback

**Description**: UI updated optimistically on user action but not reverted on API failure.

**Detection**: State updates before API call completes, without an error handler that reverts the state.

**Resolution**: Either wait for API confirmation or implement rollback on error.

### 5.3 Sensitive Data in Browser History

**Description**: Sensitive identifiers or data in URL query parameters that end up in browser history.

**Detection**: Search results or filter states with sensitive data (order IDs, user IDs) in URL params.

**Resolution**: Use POST for sensitive operations; keep sensitive identifiers out of query strings.

---

## Category 6: Configuration & Environment

### 6.1 Missing Environment Variable Validation at Startup

**Description**: Application starts without required environment variables, failing at runtime when those values are accessed.

**Detection**: No startup validation that checks all required env vars are present and non-empty.

**Resolution**: Validate all required configuration at application startup; fail fast with a clear error message.

### 6.2 Secrets in Source Code or Logs

**Description**: API keys, database passwords, or private keys committed to the repository or logged.

**Detection**: Check git history for secrets; search logs for sensitive patterns.

**Resolution**: Use environment variables or secret management services; filter sensitive keys from logs.

### 6.3 Different Behavior Per Environment Without Documentation

**Description**: Code branches on environment name (`if process.env.NODE_ENV === 'production'`) in ways that make behavior unpredictable.

**Detection**: Multiple branches on environment name in business logic (not just config loading).

**Resolution**: Keep environment-specific differences to configuration values; document them clearly.

---

## Category 7: Dependency Management

### 7.1 Unpinned Dependency Versions

**Description**: Dependencies with `^` or `~` version prefixes can silently update to incompatible versions.

**Detection**: `package.json` or `requirements.txt` with non-exact version pins.

**Resolution**: Pin to exact versions in production; use lockfiles and review updates explicitly.

### 7.2 Unused Dependencies

**Description**: Packages listed in dependency files that are no longer imported anywhere.

**Detection**: Compare `package.json` dependencies against actual imports in the codebase.

**Resolution**: Remove unused dependencies to reduce attack surface and bundle size.

---

## Category 8: Testing Gaps

### 8.1 No Integration Tests for Critical Flows

**Description**: Unit tests exist but critical end-to-end flows (checkout, signup, payment) are not integration-tested.

**Detection**: Critical business flows with only unit test coverage and no integration or API tests.

**Resolution**: Add at least one integration test per critical user flow.

### 8.2 Tests Depend on Execution Order

**Description**: Tests share state and pass only when run in a specific order.

**Detection**: Tests that fail when run in isolation but pass as part of the full suite.

**Resolution**: Make each test fully self-contained; set up and tear down state within each test.

### 8.3 External Services Not Mocked

**Description**: Tests make real calls to external APIs (payment processors, email services), causing flaky tests and unexpected charges.

**Detection**: Tests importing real API clients without mock/stub setup.

**Resolution**: Mock external service calls in unit/integration tests; use dedicated test environments for E2E tests.
