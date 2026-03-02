# QA Checklist for SaaS Features

Comprehensive checklist for validating SaaS feature implementations. Use this alongside the acceptance criteria from the story file — this checklist catches common omissions that ACs often leave implicit.

---

## 1. Functional Correctness

### Happy Path
- [ ] Core feature works as described in the story
- [ ] Data is persisted correctly and retrievable after operation
- [ ] UI/API response matches expected format and content
- [ ] Success states are communicated clearly to users

### Error Paths
- [ ] Invalid input returns appropriate error (not 500)
- [ ] Missing required fields are rejected with clear messages
- [ ] Operations on non-existent resources return 404 / not found
- [ ] Operations on resources the user does not own return 403 / forbidden

### Edge Cases
- [ ] Empty collections handled (zero results, empty list)
- [ ] Maximum allowed input sizes handled (long strings, large files)
- [ ] Concurrent operations do not corrupt state (where applicable)
- [ ] Idempotent operations remain safe when repeated

---

## 2. Authentication & Authorization

- [ ] Unauthenticated requests to protected endpoints are rejected (401)
- [ ] Authenticated users can only access their own resources (not others')
- [ ] Role/permission boundaries enforced for elevated operations
- [ ] Tokens/session cookies are handled securely (httpOnly, secure flags)
- [ ] Expired tokens are rejected, not silently ignored

---

## 3. Input Validation

- [ ] All user-supplied strings are validated for type, length, and format
- [ ] Numeric inputs are validated for range (min/max) and type
- [ ] File uploads validated for type, size, and content (if applicable)
- [ ] Enum/choice fields reject values outside the allowed set
- [ ] Date/time inputs validated for format and logical consistency

---

## 4. API Contract Compliance

- [ ] Response status codes match specification (200, 201, 400, 401, 403, 404, 422, 500)
- [ ] Response body schema matches documented structure
- [ ] Error response format is consistent across endpoints
- [ ] Pagination parameters work correctly (page, limit, cursor)
- [ ] Content-Type headers set correctly on requests and responses

---

## 5. Database & Persistence

- [ ] Created records can be read back with correct data
- [ ] Updated records reflect changes (no stale data)
- [ ] Deleted records are no longer accessible
- [ ] Soft deletes (if used) exclude deleted records from default queries
- [ ] Foreign key relationships maintained (no orphaned records)
- [ ] Indexes exist for fields used in common query patterns

---

## 6. Test Coverage Quality

- [ ] Tests exist for all acceptance criteria
- [ ] Each test has meaningful assertions (not just "no exception thrown")
- [ ] Error paths are tested, not only happy paths
- [ ] Test data is isolated (tests do not depend on each other's side effects)
- [ ] Mocks are used appropriately for external services
- [ ] Test names clearly describe the scenario being tested

---

## 7. SaaS Multi-Tenancy

- [ ] Data is scoped to the correct tenant/organization
- [ ] Cross-tenant data access is impossible through API manipulation
- [ ] Tenant identifier is validated server-side (not trusted from client)
- [ ] New records automatically associated with the correct tenant
- [ ] Admin operations scoped appropriately (super-admin vs. org admin)

---

## 8. Pagination & Large Datasets

- [ ] List endpoints paginate results (not returning unbounded collections)
- [ ] Pagination metadata returned (total count, next cursor, or has_next)
- [ ] Ordering is consistent and deterministic
- [ ] Filtering works correctly in combination with pagination
- [ ] Empty pages handled gracefully (no errors, correct empty response)

---

## 9. Email & Notifications (if applicable)

- [ ] Notification triggered at the correct point in the flow
- [ ] Notification content is accurate and complete
- [ ] Notification is sent to the correct recipient(s)
- [ ] Notification is not sent on rollback or error
- [ ] Test confirms notification was triggered (mock or stub)

---

## 10. Background Jobs & Async Operations (if applicable)

- [ ] Job is enqueued correctly on the triggering event
- [ ] Job executes the expected operation
- [ ] Job handles failure gracefully (retry logic, dead-letter queue)
- [ ] Job result is observable (status endpoint, notification, or log)
- [ ] Idempotency: re-running the job does not cause duplicate side effects

---

## 11. Performance Baseline

- [ ] Common read operations complete without full-table scans
- [ ] List endpoints do not execute N+1 queries
- [ ] Heavy operations are async (not blocking the request thread)
- [ ] Response times acceptable for expected data volumes

---

## 12. Definition of Done

- [ ] All story acceptance criteria have PASS verdict
- [ ] No FAIL or PARTIAL verdicts outstanding
- [ ] All tests pass
- [ ] No production TODOs or FIXMEs left in changed files
- [ ] File list in story matches actual changes
- [ ] No regressions in existing test suite
- [ ] Code review approved (if required by process)
- [ ] Documentation updated (API docs, README, changelog — as needed)
