# CLAUDE.md - FastAPI Project

This file provides guidance to Claude Code (claude.ai/code) when working with this FastAPI project.

## Project Architecture

This is a **FastAPI application** with a clean architecture pattern, using modern Python development practices and tools.

### Project Structure
```
project/
├── src/
│   ├── api/                 # API routes and endpoints
│   │   ├── v1/             # API version 1
│   │   │   ├── endpoints/  # Individual route modules
│   │   │   └── api.py      # API router aggregation
│   │   └── dependencies/   # Dependency injection
│   ├── core/               # Core application configuration
│   │   ├── config.py      # Settings and environment variables
│   │   ├── security.py    # Authentication and security
│   │   └── database.py    # Database configuration
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic models for validation
│   ├── services/          # Business logic layer
│   ├── utils/             # Utility functions
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── alembic/              # Database migrations
├── requirements/         # Requirements files
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── pyproject.toml       # Project configuration
```

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync

# Install development dependencies
uv sync --dev
```

### Development Server
```bash
# Run development server with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Alternative with Gunicorn (production-like)
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Database Operations
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
alembic downgrade base && alembic upgrade head
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_users.py

# Run tests with specific marker
pytest -m "not slow"
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/
mypy src/

# Run all quality checks
black --check src/ tests/ && isort --check src/ tests/ && ruff check src/ tests/ && mypy src/
```

## Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool

### Database
- **PostgreSQL**: Primary database (asyncpg driver)
- **Redis**: Caching and session storage
- **SQLModel**: SQLAlchemy models with Pydantic validation

### Authentication & Security
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **python-multipart**: Form data parsing

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatter
- **isort**: Import sorter
- **ruff**: Fast Python linter
- **mypy**: Static type checker

## API Conventions

### Response Format
```python
# Success response
{
    "success": True,
    "data": {...},
    "message": "Operation successful"
}

# Error response
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {...}
    }
}
```

### Route Organization
- Use APIRouter for organizing routes
- Group related endpoints in modules
- Use dependency injection for common functionality
- Implement proper HTTP status codes

### Example Route Structure
```python
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user
from src.schemas.user import UserCreate, UserResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends()
):
    return await user_service.create_user(user_data)
```

## Common Patterns

### Database Session Management
```python
# src/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Service Layer Pattern
```python
# src/services/base.py
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

class BaseService(ABC):
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def commit(self):
        await self.db.commit()
        
    async def rollback(self):
        await self.db.rollback()
```

### Error Handling
```python
# src/core/exceptions.py
from fastapi import HTTPException

class NotFoundError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} not found"
        )

class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=422,
            detail=message
        )
```

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=development
DEBUG=True
API_V1_STR=/api/v1
```

### Settings Management
```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Deployment

### Docker
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```