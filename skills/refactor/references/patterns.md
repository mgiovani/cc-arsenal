# Refactoring patterns & safety practices

## Refactoring catalog

### Extract method

Reach for this when a code fragment can be grouped together and given a meaningful name, or when a method has grown to do too many things.

1. Identify the code to extract
2. Create a new method with the extracted code, choosing parameters from the variables the fragment actually uses
3. Run tests
4. Replace the original code with a call to the new method
5. Run tests again
6. Clean up: remove any intermediate variables no longer needed
7. Confirm the suite still passes

Watch for: variables modified inside the fragment need to come back out, either returned or passed by reference; side effects (I/O, mutations) have to happen in the exact same order as before; and exception-handling scope can shift once code moves into its own method.

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

### Extract class

Use this when a class has taken on responsibilities that really belong to separate concerns.

1. Identify the cohesive subset of fields and methods to pull out
2. Create the new class around that subset
3. Run tests
4. Add a reference from the old class to the new one
5. Delegate method calls from the old class to the new class
6. Run tests
7. Update external callers to use the new class directly, if that's warranted
8. Run tests
9. Once every caller has moved, remove the now-unneeded delegating methods from the old class
10. Run the suite one more time

Watch out for shared mutable state carried over between the old and new class. Serialization or deserialization paths may quietly break, and inheritance hierarchies could be affected by the split too.

### Rename (variable, method, class)

Do this when a name no longer communicates what the thing actually does.

1. If the language and tooling support it, use IDE/tool rename refactoring
2. Otherwise, add the new name alongside the old one (an alias or wrapper works, so does a re-export)
3. Run tests
4. Update callers to the new name one file at a time, testing between each
5. Run tests after each file
6. Remove the old name
7. Run tests one last time

Dynamic references (strings, reflection) won't show up in a search, so double-check for those. External consumers may still depend on the old name, and serialized data can have the old name baked into it.

### Move function/class

Applies when a function or class sits in the wrong module: it really belongs closer to its primary consumers or related code.

1. Copy the function/class to the target module
2. Add a re-export from the source module, which keeps backward compatibility intact
3. Run tests
4. Update callers one at a time to import from the new location
5. Run tests after each caller update
6. Once every caller has switched over, remove the re-export from the source
7. Run tests

Risks here include circular import or dependency issues, path-dependent code such as logging or error messages that embed module names, and build system or bundler configuration that may need updating.

### Simplify conditional

Worth doing whenever conditional logic has become hard to follow.

1. Extract the condition into a well-named boolean variable or method
2. Run tests
3. Simplify the logic itself: apply De Morgan's laws, reach for guard clauses, or return early
4. Run tests
5. If nested conditionals remain, go back to step 1

Common simplifications: replacing nested if/else with guard clauses (early return), replacing complex boolean expressions with named methods, swapping a conditional for polymorphism where that fits, and consolidating duplicate conditional fragments.

### Remove duplication

Applies when the same or very similar code shows up in multiple places.

1. Identify the duplicated pattern across every location it appears
2. Work out the minimal abstraction that captures the shared behavior
3. Create the shared function or method (a class, if that fits better)
4. Run tests
5. Point the first occurrence at the shared code
6. Run tests
7. Do the same for the next occurrence
8. Run tests
9. Repeat until every occurrence is converted, testing after each one

Apparent duplication can turn out to hide subtle differences, so verify before abstracting. Guard against premature abstraction: make sure there are truly three or more occurrences first. The shared abstraction may also need parameterizing to absorb slight variations between call sites.

### Inline method/variable

Fits when a method body or variable adds no clarity beyond its own name, or when the indirection isn't earning its keep.

1. Verify the method/variable isn't overridden in any subclass
2. Replace one call site with the method body or variable value
3. Run tests
4. Repeat for the remaining call sites
5. Run tests
6. Remove the method/variable declaration
7. Run tests

### Replace magic numbers/strings with constants

Use when literal values show up in code with no explanation of what they mean.

1. Create a named constant with the value
2. Run tests
3. Replace one occurrence with the constant reference
4. Run tests
5. Repeat for the remaining occurrences
6. Run tests

### Decompose large function

Reach for this when a function has grown past roughly 50 lines or mixes multiple levels of abstraction.

1. Identify the logical sections within the function, often already marked off by comments
2. Apply "Extract method" to the first section
3. Run tests
4. Apply "Extract method" to the next section
5. Run tests
6. Keep going until the original function reads as a high-level summary
7. Run tests

## Safety practices

### The golden rule

Every refactoring step must end with passing tests. If tests fail after a change, that change introduced a behavioral difference. Either revert and find a smaller step, or, only if the test was checking an implementation detail rather than behavior, fix the test itself.

### Pre-refactoring checklist

- [ ] Read and understand all the target code
- [ ] Identify all callers and dependents
- [ ] Run the full test suite and record the baseline
- [ ] Assess test coverage, adding characterization tests for any gaps
- [ ] Plan incremental steps that are each independently verifiable
- [ ] Get approval first if the scope is large (more than 5 files, or public API changes)

### When to write characterization tests

Write them when the target code has no existing tests, when existing tests only cover the happy path, or when error handling and edge cases go untested. The same goes for uncovered side effects (file I/O, database access, network calls) and for complex conditional logic with untested branches.

Skip them when existing tests already cover the target code thoroughly, the refactoring is trivially safe (a plain rename via search-and-replace), or the change is confined to a single function that's already well tested.

### Characterization test naming

Use a consistent prefix so these tests stand out from the rest of the suite:
- Python: `test_char_<behavior_description>`
- JavaScript: `describe('characterization: <module>')` or `it('char: <behavior>')`
- Go: `TestChar_<BehaviorDescription>`

### When to abort a refactoring

Stop and reassess if tests keep failing for reasons that aren't clear, or if the change cascades to far more files than expected. The same applies when circular dependencies surface that would require architectural changes, when the "refactoring" has quietly turned into a redesign that changes behavior, or when external consumers would be affected in ways you can't fully predict.

### Red flags during refactoring

| Signal | What it means |
|--------|----------------|
| A test needs changing to pass | Likely a behavioral change, not a refactoring |
| A new test is needed for new behavior | Definitely not a refactoring: stop |
| "While I'm here" changes creep in | Scope creep; resist fixing unrelated issues |
| Performance assumptions are shifting | Verify benchmarks if the code is performance-critical |

## Language-specific notes

### Python
- Use `pytest --tb=short` for quick feedback during incremental changes
- `ruff check --fix` can handle import reordering after moves
- Watch for `__all__` exports when moving public API
- Decorators may mask the actual function signature

### JavaScript/TypeScript
- Use named exports to make rename refactoring safer
- Watch for `default` exports (harder to track callers)
- Bundle tree-shaking may be affected by code reorganization
- TypeScript interfaces provide safety during structural changes

### Go
- Exported vs unexported (capitalization) makes API surface explicit
- `go vet` and `staticcheck` catch many refactoring errors
- Interface satisfaction is implicit: moving methods may break interface compliance

### Java/Kotlin
- IDE refactoring tools are mature, prefer them when available
- Watch for reflection-based access (Spring annotations, serialization)
- Sealed classes/interfaces limit the impact of hierarchy changes

## Commit message examples

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
