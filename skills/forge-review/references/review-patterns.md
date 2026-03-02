# Code Patterns and Their Quality Implications

Reference guide for common code patterns encountered during code review, with notes on when they are acceptable, when they are problematic, and what to look for.

---

## 1. God Objects / God Functions

**Pattern**: A class or function that does too many things.

**Signs**:
- Class over 300 lines
- Function over 40 lines
- Constructor with 10+ parameters
- Method name includes "and", "or", "with" connecting unrelated concepts

**Quality implication**: Hard to test in isolation, changes ripple unpredictably, multiple developers conflict when editing.

**What to look for**: Classes named `Manager`, `Handler`, `Helper`, `Service` that span multiple unrelated domains. Functions with large if/else trees handling fundamentally different logic paths.

**Acceptable exception**: Entry-point orchestrators in clean architecture (e.g., an application service that coordinates domain objects) can be longer if each step delegates to focused units.

---

## 2. Primitive Obsession

**Pattern**: Using primitive types (string, int, bool) where a domain object would be more appropriate.

**Signs**:
- `userId: string` passed everywhere without validation
- Email address stored as bare `string` without format enforcement
- Status represented as `string` instead of enum
- Configuration passed as a dictionary instead of typed config object

**Quality implication**: No compile-time safety, validation scattered across codebase, implicit assumptions about format.

**What to look for**: Functions with 5+ string parameters, raw strings used as identifiers or codes.

---

## 3. Shotgun Surgery

**Pattern**: A single conceptual change requires edits in many unrelated files.

**Signs**:
- Adding a new field requires changes in 6+ files
- Every feature addition touches the same 3 utility files
- Constants duplicated across modules

**Quality implication**: High coupling, error-prone changes, difficult to keep in sync.

**What to look for**: Multiple files importing the same set of utilities, duplicated constant definitions, repeated validation logic.

---

## 4. Feature Envy

**Pattern**: A method uses more methods/fields from another class than its own.

**Signs**:
- `processOrder(order)` accesses `order.customer.address.city`, `order.customer.account.balance`, etc.
- Method would naturally belong to the class it's most interested in

**Quality implication**: Poor cohesion, logic in the wrong place, harder to find relevant code.

**What to look for**: Methods with long chains of property access on a single object.

---

## 5. Inappropriate Intimacy

**Pattern**: Classes that are too tightly coupled, accessing each other's internals.

**Signs**:
- Class A directly sets private fields of class B
- Module imports internal utilities not intended for external use
- Direct database table access bypassing the responsible repository

**Quality implication**: Hidden dependencies, changes in one class break the other unexpectedly.

---

## 6. Magic Numbers and Strings

**Pattern**: Unexplained literal values in business logic.

**Signs**:
- `if (attempts > 5)` — what is 5? Why 5?
- `status = "PENDING_REVIEW"` inline in multiple places
- `timeout = 30000` without explanation

**Quality implication**: Meaning is lost, changes require finding all occurrences, inconsistency risks.

**Acceptable exception**: `0`, `1`, `-1`, `""` in obvious arithmetic or string operations.

---

## 7. Nested Conditionals (Arrow Anti-Pattern)

**Pattern**: Deep nesting of if/else creating a rightward drift.

**Signs**:
```
if (user) {
  if (user.isActive) {
    if (user.hasPermission) {
      if (data) {
        // actual logic 4 levels deep
      }
    }
  }
}
```

**Quality implication**: Hard to read, easy to miss edge cases, high cyclomatic complexity.

**Better pattern**: Early returns / guard clauses, extract to smaller functions, use null objects.

---

## 8. Callback Hell / Promise Chains

**Pattern**: Deep nesting of async operations.

**Signs**:
- Callbacks nested 3+ levels deep
- `.then().then().then()` chains without error handling at each step
- Mix of async/await and `.then()` in the same function

**Quality implication**: Hard to read, error handling often incomplete, ordering bugs common.

---

## 9. Temporal Coupling

**Pattern**: Methods that must be called in a specific order but the order is not enforced.

**Signs**:
- `init()` must be called before `process()`
- Object methods that fail if called before another method
- Setup methods that mutate shared state

**Quality implication**: Silent failures when order is wrong, hard to test, fragile.

---

## 10. Test Antipatterns

### Over-Mocking
**Signs**: Tests mock every dependency, including simple value objects. Tests break when implementation changes, not when behavior changes.

### Testing Implementation Not Behavior
**Signs**: Tests assert on private methods, internal state, or exact call counts rather than observable outputs.

### Shared Mutable Test State
**Signs**: Test class has shared state mutated across test methods. Tests pass/fail depending on run order.

### Weak Assertions
**Signs**: `expect(result).toBeDefined()` instead of `expect(result).toEqual({id: 1, name: "Alice"})`. Tests that would pass even if the function returned garbage.

### Giant Test Functions
**Signs**: Single test function with 50+ lines, testing multiple scenarios, requiring scrolling to understand what's being verified.

---

## 11. Repository Pattern Violations

**Pattern**: Database queries scattered throughout the codebase instead of centralized.

**Signs**:
- SQL or ORM queries in controller/handler files
- Business logic files importing database connection directly
- Same query duplicated in multiple services

**Quality implication**: Hard to optimize, hard to change database, testing requires real database.

---

## 12. Error Swallowing

**Pattern**: Catching exceptions without meaningful handling.

**Signs**:
```python
try:
    process_payment(data)
except Exception:
    pass  # or just: logger.error("failed")
```

**Quality implication**: Silent failures, impossible to debug, users get no feedback.

**Acceptable exception**: Intentional no-op where failure is truly inconsequential AND this is documented in a comment.

---

## 13. Clever Code

**Pattern**: Code that is clever/compact but hard to understand.

**Signs**:
- One-liners with multiple nested ternaries
- Operator overloading used non-intuitively
- Lambda functions with complex business logic
- Bit manipulation without comments explaining intent

**Quality implication**: Very hard to maintain, next developer (or yourself in 6 months) cannot understand intent.

**Principle**: Code is read 10x more than it is written. Optimize for reading.

---

## 14. Configuration in Code

**Pattern**: Environment-specific values or secrets in source code.

**Signs**:
- Hardcoded API URLs, database connection strings
- Feature flags as code constants instead of configuration
- Environment names like `"production"` compared in application logic

**Quality implication**: Requires code changes for environment changes, security risk for secrets.
