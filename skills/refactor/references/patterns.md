# Refactoring Patterns & Safety Practices

## Refactoring Catalog

### Extract Method

**When to use**: A code fragment can be grouped together and given a meaningful name, or a method is doing too many things.

**Step sequence**:
1. Identify the code to extract
2. Create a new method with the extracted code — determine parameters from variables used in the fragment
3. Run tests
4. Replace the original code with a call to the new method
5. Run tests
6. Clean up — remove any intermediate variables no longer needed
7. Run tests

**Risks**:
- Variables modified inside the fragment need to be returned or passed by reference
- Side effects (I/O, mutations) must be preserved in the exact same order
- Exception handling scope may change

**Example (Python)**:
```python
# Before
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Invalid total")
    # calculate discount
    discount = 0
    if order.total > 100:
        discount = order.total * 0.1
    order.total -= discount
    # save
    db.save(order)

# After - Step 1: Create validate_order
def validate_order(order):
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Invalid total")

# After - Step 2: Create apply_discount
def apply_discount(order):
    discount = 0
    if order.total > 100:
        discount = order.total * 0.1
    order.total -= discount

# After - Step 3: Simplified process_order
def process_order(order):
    validate_order(order)
    apply_discount(order)
    db.save(order)
```

### Extract Class

**When to use**: A class has responsibilities that could be split into separate concerns.

**Step sequence**:
1. Identify the cohesive subset of fields and methods to extract
2. Create the new class with the subset of fields and methods
3. Run tests
4. Add a reference from the old class to the new class
5. Delegate method calls from old class to new class
6. Run tests
7. Update external callers to use the new class directly (if needed)
8. Run tests
9. Remove delegating methods from old class (if all callers updated)
10. Run tests

**Risks**:
- Shared mutable state between old and new class
- Serialization/deserialization may break
- Inheritance hierarchies may be affected

### Rename (Variable, Method, Class)

**When to use**: A name does not clearly communicate purpose.

**Step sequence**:
1. If the language supports it, use IDE/tool rename refactoring
2. Otherwise: add the new name alongside the old (alias, wrapper, re-export)
3. Run tests
4. Update all callers to use the new name (one file at a time, testing between each)
5. Run tests after each file
6. Remove the old name
7. Run tests

**Risks**:
- Dynamic references (strings, reflection) won't be caught by search
- External consumers may depend on the old name
- Serialized data may contain the old name

### Move Function/Class

**When to use**: A function/class is in the wrong module — it belongs closer to its primary consumers or related code.

**Step sequence**:
1. Copy the function/class to the target module
2. Add a re-export from the source module (preserves backward compatibility)
3. Run tests
4. Update callers one at a time to import from the new location
5. Run tests after each caller update
6. Once all callers are updated, remove the re-export from the source
7. Run tests

**Risks**:
- Circular import/dependency issues
- Path-dependent code (logging, error messages with module names)
- Build system or bundler configuration may need updates

### Simplify Conditional

**When to use**: Complex conditional logic is hard to understand.

**Step sequence**:
1. Extract the condition into a well-named boolean variable or method
2. Run tests
3. Simplify the logic (De Morgan's laws, guard clauses, early returns)
4. Run tests
5. If nested conditionals remain, repeat from step 1

**Common simplifications**:
- Replace nested if/else with guard clauses (early return)
- Replace complex boolean expressions with named methods
- Replace conditional with polymorphism (when appropriate)
- Consolidate duplicate conditional fragments

### Remove Duplication

**When to use**: The same or very similar code exists in multiple places.

**Step sequence**:
1. Identify the duplicated pattern across all locations
2. Determine the minimal abstraction that captures the shared behavior
3. Create the shared function/method/class
4. Run tests
5. Replace the FIRST occurrence with a call to the shared code
6. Run tests
7. Replace the NEXT occurrence
8. Run tests
9. Repeat for remaining occurrences, testing after each

**Risks**:
- Apparent duplication may actually have subtle differences
- Premature abstraction — ensure there are truly 3+ occurrences before abstracting
- The shared abstraction may need parameterization for slight variations

### Inline Method/Variable

**When to use**: A method body or variable is just as clear as its name, or indirection adds no value.

**Step sequence**:
1. Verify the method/variable is not overridden in subclasses
2. Replace one call site with the method body / variable value
3. Run tests
4. Repeat for remaining call sites
5. Run tests
6. Remove the method/variable declaration
7. Run tests

### Replace Magic Numbers/Strings with Constants

**When to use**: Literal values appear in code without explanation.

**Step sequence**:
1. Create a named constant with the value
2. Run tests
3. Replace one occurrence with the constant reference
4. Run tests
5. Repeat for remaining occurrences
6. Run tests

### Decompose Large Function

**When to use**: A function exceeds ~50 lines or has multiple levels of abstraction.

**Step sequence**:
1. Identify logical sections within the function (often separated by comments)
2. Apply "Extract Method" to the first section
3. Run tests
4. Apply "Extract Method" to the next section
5. Run tests
6. Repeat until the original function reads as a high-level summary
7. Run tests

## Safety Practices

### The Golden Rule

**Every refactoring step must end with passing tests.** If tests fail after a change, that change introduced a behavioral difference. Either:
1. Revert the change and find a smaller step
2. Fix the test ONLY if it was testing implementation details (not behavior)

### Pre-Refactoring Checklist

- [ ] Read and understand ALL the target code
- [ ] Identify ALL callers and dependents
- [ ] Run full test suite — record baseline results
- [ ] Assess test coverage — add characterization tests for gaps
- [ ] Plan incremental steps — each independently verifiable
- [ ] Get approval if scope is large (>5 files, public API changes)

### When to Write Characterization Tests

Write characterization tests when:
- The target code has no existing tests
- Existing tests only cover the happy path
- Error handling or edge cases are untested
- Side effects (file I/O, database, network) are untested
- Complex conditional logic has untested branches

Skip characterization tests when:
- Existing tests thoroughly cover the target code
- The refactoring is trivially safe (rename with search-and-replace)
- The change is confined to a single, well-tested function

### Characterization Test Naming

Use a consistent prefix to distinguish characterization tests:
- Python: `test_char_<behavior_description>`
- JavaScript: `describe('characterization: <module>')` or `it('char: <behavior>')`
- Go: `TestChar_<BehaviorDescription>`

### When to Abort a Refactoring

Stop and reassess if:
- Tests keep failing and the cause is unclear
- The change cascades to far more files than expected
- Circular dependencies emerge that require architectural changes
- The "refactoring" is actually a redesign (changes behavior)
- External consumers would be affected in unknown ways

### Red Flags During Refactoring

- **Test needs changing to pass**: Likely a behavioral change, not a refactoring
- **New test needed for new behavior**: Definitely not a refactoring — stop
- **"While I'm here" changes**: Scope creep — resist fixing unrelated issues
- **Performance assumptions changing**: Verify benchmarks if performance-critical

## Language-Specific Notes

### Python
- Use `pytest --tb=short` for quick feedback during incremental changes
- `ruff check --fix` can handle import reordering after moves
- Watch for `__all__` exports when moving public API
- Decorators may mask the actual function signature

### JavaScript/TypeScript
- Use named exports to make rename refactoring safer
- Watch for `default` exports — harder to track callers
- Bundle tree-shaking may be affected by code reorganization
- TypeScript interfaces provide safety during structural changes

### Go
- Exported vs unexported (capitalization) makes API surface explicit
- `go vet` and `staticcheck` catch many refactoring errors
- Interface satisfaction is implicit — moving methods may break interface compliance

### Java/Kotlin
- IDE refactoring tools are mature — prefer them when available
- Watch for reflection-based access (Spring annotations, serialization)
- Sealed classes/interfaces limit the impact of hierarchy changes

## Commit Message Examples

```
refactor: extract validation logic from OrderProcessor

Moved order validation into dedicated OrderValidator class to improve
separation of concerns. OrderProcessor now delegates to OrderValidator
for all input validation.

- Extracted 3 validation methods into OrderValidator
- Updated 5 callers to use OrderValidator directly
- Added characterization tests for edge cases

No behavioral changes.
```

```
refactor(auth): simplify token refresh conditional logic

Replaced nested if/else chain with guard clauses and extracted
isTokenExpired() helper. Reduces cyclomatic complexity from 8 to 3.

No behavioral changes.
```

```
refactor: consolidate duplicate email formatting across modules

Extracted shared formatEmailAddress() from UserService, NotificationService,
and ReportGenerator. All three modules now use the shared utility.

- Created email_utils.py with formatEmailAddress()
- Added characterization tests for all formatting edge cases
- Updated imports in 3 modules

No behavioral changes.
```
