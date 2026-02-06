# FastAPI Best Practices Reference

This document contains the complete FastAPI best practices content to be injected into CLAUDE.md files. Based on [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices).

## Full Content Template

Use this template when injecting FastAPI documentation:

---

## FastAPI Best Practices

### Project Structure

**Use domain-driven organization** (by feature), not file-type organization.

```
src/
├── auth/
│   ├── router.py          # API endpoints
│   ├── schemas.py         # Pydantic request/response models
│   ├── models.py          # Database models (SQLAlchemy)
│   ├── service.py         # Business logic
│   ├── dependencies.py    # Route-level dependencies
│   ├── constants.py       # Domain constants
│   ├── config.py          # Domain configuration
│   ├── exceptions.py      # Domain-specific exceptions
│   └── utils.py           # Utility functions
├── posts/
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── service.py
│   └── ...
├── users/
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── service.py
│   └── ...
├── config.py              # Global settings (split by domain)
└── main.py                # App initialization
```

**Benefits**:
- Each domain is self-contained and independently testable
- Scales better than monolithic file-type organization
- Clear boundaries reduce coupling between domains

### Async Patterns

**Critical async rules**:
- ✅ Use `async def` for non-blocking I/O (database queries, HTTP calls, file operations)
- ✅ Use `def` for blocking operations (FastAPI automatically runs in threadpool)
- ✅ Use `await asyncio.sleep()` for delays
- ✅ Prefer async database drivers (SQLAlchemy 2.0+ with asyncio support)
- ❌ **NEVER** use `time.sleep()` in async functions (blocks entire event loop)
- ❌ CPU-intensive work requires multiprocessing or Celery (not threads due to GIL)

**Example**:
```python
# ✅ Good - non-blocking
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ✅ Good - blocking operation in def
@router.get("/compute")
def heavy_computation():
    # FastAPI runs this in threadpool automatically
    return expensive_cpu_work()

# ❌ Bad - blocks event loop
@router.get("/bad")
async def bad_endpoint():
    time.sleep(5)  # NEVER DO THIS
    return {"status": "done"}
```

### Import Discipline

**Use explicit imports with module names** to avoid hidden coupling:

```python
# ✅ Good - explicit and clear
from src.auth import constants as auth_constants
from src.auth import service as auth_service
from src.posts import service as posts_service

# ❌ Bad - creates hidden coupling
from src.auth.constants import *
from src.auth.service import authenticate_user
```

**Benefits**:
- Clear dependencies between modules
- Easier to refactor and maintain
- Prevents naming conflicts
- Critical when importing services or dependencies from other packages

### Validation & Dependencies

**Leverage Pydantic's rich built-in validation**:

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Annotated

class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')]
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=120)]

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v
```

**Use dependencies for business logic validation**:

```python
# Dependencies are not just for injection - use for validation too
async def verify_user_exists(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/{user_id}/posts")
async def get_user_posts(
    user: User = Depends(verify_user_exists),  # Validates existence
    db: AsyncSession = Depends(get_db)
):
    # user is guaranteed to exist here
    return await posts_service.get_by_user(db, user.id)
```

**Remember**: Dependencies cache within request scope - chain them to avoid redundant computations:

```python
# ✅ Good - get_current_user calls get_token, both cached
async def get_token(authorization: str = Header(...)) -> str:
    return authorization.replace("Bearer ", "")

async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Expensive DB lookup, but cached for this request
    return await auth_service.verify_token(db, token)

# ❌ Bad - repeating logic
async def endpoint1(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    user = await auth_service.verify_token(db, token)
    ...

async def endpoint2(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    token = authorization.replace("Bearer ", "")  # Duplicated logic
    user = await auth_service.verify_token(db, token)
    ...
```

### Response Serialization

**Always use `response_model` parameter** for type safety and OpenAPI documentation:

```python
from typing import List

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(User))
    return users.scalars().all()  # Auto-serialized to UserResponse
```

**Create custom encoders for special types**:

```python
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class CustomModel(BaseModel):
    id: UUID
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
```

### Error Handling

**Define module-specific exception classes**:

```python
# src/auth/exceptions.py
class AuthException(Exception):
    """Base exception for auth module"""
    pass

class InvalidCredentials(AuthException):
    """Raised when credentials are invalid"""
    pass

class TokenExpired(AuthException):
    """Raised when token has expired"""
    pass

# src/auth/service.py
def authenticate_user(username: str, password: str) -> User:
    user = get_user_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Username or password is incorrect")
    return user

# src/main.py - register exception handlers
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(InvalidCredentials)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentials):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )
```

**Use correct HTTP status codes**:
- 400 Bad Request - Client error (validation failed)
- 401 Unauthorized - Authentication required
- 403 Forbidden - Authenticated but not authorized
- 404 Not Found - Resource doesn't exist
- 422 Unprocessable Entity - Validation error (FastAPI default for Pydantic validation)
- 500 Internal Server Error - Server error (unexpected)

### Database Integration

**SQL-first design approach**:

1. **Design schema first**, then create models
2. **Enforce naming conventions at database level** (snake_case for tables/columns)
3. **Use Alembic for migrations** from day one
4. **Prefer async drivers** for scalability

**Example with SQLAlchemy 2.0+ (async)**:

```python
# src/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# src/auth/models.py
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# src/auth/service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()
```

**Migration workflow** (Alembic):

```bash
# Generate migration
alembic revision --autogenerate -m "Add users table"

# Review migration file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

**Use async test clients from day one**:

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.main import app
from src.database import Base, get_db

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/test_db"

@pytest.fixture
async def async_client():
    # Set up test database
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Override dependency
    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# tests/test_users.py
import pytest

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    response = await async_client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
```

**Test at multiple levels**:
- **Unit tests**: Test service layer logic in isolation
- **Integration tests**: Test router + service + database
- **End-to-end tests**: Test full request/response cycle with real dependencies

### Code Quality

**Use Ruff** for linting and formatting (Python-focused, extremely fast):

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

**Always include type hints** for OpenAPI generation:

```python
# ✅ Good - fully typed
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    ...

# ❌ Bad - no type hints, breaks OpenAPI docs
async def create_user(user_data, db=Depends(get_db)):
    ...
```

**Enforce strict type checking** with mypy or pyright:

```toml
# pyproject.toml
[tool.pyright]
include = ["src"]
exclude = ["**/node_modules", "**/__pycache__"]
typeCheckingMode = "strict"
reportMissingTypeStubs = false

# Or with mypy
[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

**Use pre-commit hooks** for quality gates:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]
```

### REST Conventions

**Use correct HTTP methods**:

| Method | Use Case | Idempotent | Safe |
|--------|----------|------------|------|
| GET | Read/retrieve resources | ✅ | ✅ |
| POST | Create new resources | ❌ | ❌ |
| PUT | Update/replace entire resource | ✅ | ❌ |
| PATCH | Partial update | ❌ | ❌ |
| DELETE | Remove resource | ✅ | ❌ |

**Example**:

```python
# ✅ Good - follows REST conventions
@router.get("/users")              # List users
@router.post("/users")             # Create user
@router.get("/users/{user_id}")    # Get specific user
@router.put("/users/{user_id}")    # Replace entire user
@router.patch("/users/{user_id}")  # Update specific fields
@router.delete("/users/{user_id}") # Delete user

# ❌ Bad - violates REST conventions
@router.post("/get-users")         # Should be GET
@router.get("/delete-user/{id}")   # Should be DELETE
```

**Add docstrings for OpenAPI documentation**:

```python
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user.

    - **username**: Unique username (3-50 alphanumeric characters)
    - **email**: Valid email address
    - **password**: Password (min 8 characters)

    Returns the created user with ID.
    """
    return await user_service.create(db, user_data)
```

**Leverage FastAPI's auto-generated `/docs`** as primary API documentation (OpenAPI/Swagger UI).

### Configuration Management

**Decouple BaseSettings by domain** (not monolithic):

```python
# ✅ Good - domain-specific config classes
# src/auth/config.py
from pydantic_settings import BaseSettings

class AuthConfig(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_prefix = "AUTH_"

# src/database.py
class DatabaseConfig(BaseSettings):
    url: str
    pool_size: int = 5
    max_overflow: int = 10

    class Config:
        env_prefix = "DATABASE_"

# ❌ Bad - monolithic settings
class Settings(BaseSettings):
    # Everything in one giant class
    secret_key: str
    database_url: str
    redis_url: str
    smtp_host: str
    # ... 50 more fields
```

### Summary Checklist

When building FastAPI applications:

- [ ] Use domain-driven project structure (not file-type organization)
- [ ] Use explicit imports with module names
- [ ] Use `async def` for I/O, `def` for CPU-bound operations
- [ ] Never use `time.sleep()` in async functions
- [ ] Leverage Pydantic's built-in validation features
- [ ] Use dependencies for business logic validation and caching
- [ ] Always specify `response_model` on endpoints
- [ ] Define module-specific exception classes
- [ ] SQL-first design with Alembic migrations
- [ ] Use async database drivers (SQLAlchemy 2.0+)
- [ ] Write async tests with proper fixtures
- [ ] Use Ruff for linting and formatting
- [ ] Enforce type hints for OpenAPI generation
- [ ] Follow REST conventions for HTTP methods
- [ ] Add docstrings to endpoints for documentation
- [ ] Decouple settings by domain
- [ ] Set up pre-commit hooks for quality gates

---

**Reference**: [FastAPI Best Practices by zhanymkanov](https://github.com/zhanymkanov/fastapi-best-practices)

**Version**: Based on production-ready patterns (applicable to FastAPI 0.100+)
