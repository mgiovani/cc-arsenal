# Test framework patterns

Framework-specific patterns for test generation. Use these as reference when writing tests to match idiomatic patterns for each framework.

## Python: pytest

### File structure
```
project/
├── src/module/
│   ├── __init__.py
│   ├── service.py
│   └── models.py
└── tests/
    ├── conftest.py          # Shared fixtures
    ├── test_service.py      # Tests for service.py
    └── test_models.py       # Tests for models.py
```

### Naming convention
- Test files: `test_<module>.py`
- Test functions: `test_<function>_<scenario>_<expected>`
- Fixture files: `conftest.py` (auto-discovered by pytest)

### Patterns

**Basic unit test:**
```python
def test_create_user_with_valid_data_returns_user(user_factory):
    user = create_user(name="Alice", email="alice@example.com")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

**Parametrized tests:**
```python
@pytest.mark.parametrize("input_val,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("123", "123"),
    ("hello world", "HELLO WORLD"),
])
def test_uppercase_with_various_inputs(input_val, expected):
    assert uppercase(input_val) == expected
```

**Exception testing:**
```python
def test_create_user_with_empty_name_raises_validation_error():
    with pytest.raises(ValidationError, match="name cannot be empty"):
        create_user(name="", email="test@example.com")
```

**Fixtures (conftest.py):**
```python
@pytest.fixture
def db_session():
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_user(db_session):
    user = User(name="Test", email="test@example.com")
    db_session.add(user)
    db_session.flush()
    return user
```

**Mocking:**
```python
from unittest.mock import patch, MagicMock

def test_send_email_calls_smtp_client(mocker):
    mock_smtp = mocker.patch("module.email.smtp_client")
    send_email("to@example.com", "Subject", "Body")
    mock_smtp.send.assert_called_once()
```

**Async tests (pytest-asyncio):**
```python
@pytest.mark.asyncio
async def test_fetch_user_returns_user_data():
    result = await fetch_user(user_id=1)
    assert result["name"] == "Alice"
```

### Coverage command
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

---

## JavaScript/TypeScript: Vitest

### File structure
```
project/
├── src/
│   ├── services/
│   │   └── userService.ts
│   └── utils/
│       └── format.ts
└── tests/           # or __tests__/ or co-located .test.ts files
    ├── services/
    │   └── userService.test.ts
    └── utils/
        └── format.test.ts
```

### Naming convention
- Test files: `<module>.test.ts` or `<module>.spec.ts`
- Describe blocks: Module/class name
- It blocks: `should <expected behavior> when <condition>`

### Patterns

**Basic unit test:**
```typescript
import { describe, it, expect } from 'vitest';
import { createUser } from '../src/services/userService';

describe('createUser', () => {
  it('should return a user with the given name and email', () => {
    const user = createUser({ name: 'Alice', email: 'alice@example.com' });
    expect(user.name).toBe('Alice');
    expect(user.email).toBe('alice@example.com');
  });

  it('should throw when name is empty', () => {
    expect(() => createUser({ name: '', email: 'a@b.com' })).toThrow('name cannot be empty');
  });
});
```

**Parameterized tests (each):**
```typescript
describe('uppercase', () => {
  it.each([
    ['hello', 'HELLO'],
    ['', ''],
    ['hello world', 'HELLO WORLD'],
  ])('should convert "%s" to "%s"', (input, expected) => {
    expect(uppercase(input)).toBe(expected);
  });
});
```

**Async tests:**
```typescript
describe('fetchUser', () => {
  it('should return user data for valid id', async () => {
    const result = await fetchUser(1);
    expect(result.name).toBe('Alice');
  });
});
```

**Mocking:**
```typescript
import { vi } from 'vitest';

vi.mock('../src/services/emailService', () => ({
  sendEmail: vi.fn().mockResolvedValue(true),
}));

it('should call sendEmail on registration', async () => {
  const { sendEmail } = await import('../src/services/emailService');
  await registerUser({ name: 'Alice', email: 'a@b.com' });
  expect(sendEmail).toHaveBeenCalledOnce();
});
```

**Setup/teardown:**
```typescript
import { beforeEach, afterEach } from 'vitest';

describe('UserService', () => {
  let db: TestDB;

  beforeEach(async () => {
    db = await createTestDB();
  });

  afterEach(async () => {
    await db.cleanup();
  });
});
```

### Coverage command
```bash
vitest --coverage
# or
vitest run --coverage
```

---

## JavaScript: Jest

### File structure
Same as Vitest. Jest and Vitest share nearly identical API.

### Key differences from Vitest
- Import from `@jest/globals` or use globals
- Mock with `jest.mock()` instead of `vi.mock()`
- Use `jest.fn()` instead of `vi.fn()`
- Configuration in `jest.config.js` or `package.json`

### Patterns

**Mocking (Jest-specific):**
```typescript
jest.mock('../src/services/emailService');

import { sendEmail } from '../src/services/emailService';
const mockSendEmail = sendEmail as jest.MockedFunction<typeof sendEmail>;

beforeEach(() => {
  mockSendEmail.mockResolvedValue(true);
});
```

**Snapshot testing:**
```typescript
it('should render user profile correctly', () => {
  const result = renderUserProfile({ name: 'Alice' });
  expect(result).toMatchSnapshot();
});
```

### Coverage command
```bash
jest --coverage
# or
npx jest --coverage
```

---

## Go: testing

### File structure
```
project/
├── service/
│   ├── user.go
│   └── user_test.go    # Tests co-located with source
└── handler/
    ├── auth.go
    └── auth_test.go
```

### Naming convention
- Test files: `<source>_test.go` (co-located)
- Test functions: `Test<FunctionName>_<Scenario>`
- Table-driven: Standard Go pattern

### Patterns

**Basic test:**
```go
func TestCreateUser_ValidInput_ReturnsUser(t *testing.T) {
    user, err := CreateUser("Alice", "alice@example.com")
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if user.Name != "Alice" {
        t.Errorf("expected name Alice, got %s", user.Name)
    }
}
```

**Table-driven tests:**
```go
func TestUppercase(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"lowercase", "hello", "HELLO"},
        {"empty", "", ""},
        {"mixed", "Hello World", "HELLO WORLD"},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Uppercase(tt.input)
            if result != tt.expected {
                t.Errorf("Uppercase(%q) = %q, want %q", tt.input, result, tt.expected)
            }
        })
    }
}
```

**With testify:**
```go
import "github.com/stretchr/testify/assert"

func TestCreateUser_EmptyName_ReturnsError(t *testing.T) {
    _, err := CreateUser("", "test@example.com")
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "name cannot be empty")
}
```

### Coverage command
```bash
go test ./... -cover
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

---

## Rust: cargo test

### File structure
```
project/
├── src/
│   ├── lib.rs
│   └── services/
│       └── user.rs     # Tests in same file (mod tests)
└── tests/
    └── integration.rs  # Integration tests
```

### Patterns

**Unit tests (in-file):**
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_user_with_valid_data() {
        let user = create_user("Alice", "alice@example.com").unwrap();
        assert_eq!(user.name, "Alice");
        assert_eq!(user.email, "alice@example.com");
    }

    #[test]
    #[should_panic(expected = "name cannot be empty")]
    fn create_user_with_empty_name_panics() {
        create_user("", "test@example.com").unwrap();
    }
}
```

### Coverage command
```bash
cargo test
cargo tarpaulin --out Html  # Coverage with tarpaulin
```

---

## Common anti-Patterns to avoid

1. **Testing implementation details**: Test behavior, not internal state
2. **Overly broad tests**: One test checking 10 things, split into focused tests
3. **Flaky tests**: Tests depending on timing, network, or random data
4. **Test duplication**: Same scenario tested multiple ways without added value
5. **Missing edge cases**: Only testing happy path
6. **Brittle mocks**: Mocking too deeply into the dependency chain
7. **No assertion**: Tests that only check "does not throw"
8. **Shared mutable state**: Tests that depend on execution order

## Edge cases to always test

- **Empty inputs**: Empty strings, empty arrays, null/undefined/None
- **Boundary values**: 0, -1, MAX_INT, empty collections, single-element collections
- **Invalid inputs**: Wrong types, missing required fields, malformed data
- **Error conditions**: Network failures, file not found, permission denied
- **Concurrency**: Race conditions, deadlocks (when applicable)
- **Unicode**: Non-ASCII characters, emoji, RTL text
- **Large inputs**: Performance under load, memory limits
