# CLAUDE.md - personal development environment

This file provides guidance to Claude Code (claude.ai/code) for my personal development workflow and preferences.

## Development preferences

### Code style
- **Language**: Prefer TypeScript over JavaScript, Python 3.12+ with type hints
- **Formatting**: Use Prettier for JS/TS, Black for Python, with 100 character line length
- **Architecture**: Favor functional programming patterns, clean architecture, and SOLID principles
- **Testing**: Write comprehensive tests with >90% coverage using Jest/Vitest for JS/TS, pytest for Python

### Technology stack preferences

#### Frontend
- **Framework**: React 18+ with TypeScript, Next.js for full-stack apps
- **Styling**: Tailwind CSS with component libraries (shadcn/ui, Radix UI)
- **State Management**: Zustand for client state, TanStack Query for server state
- **Build Tools**: Vite for SPAs, Next.js for full-stack

#### Backend
- **Languages**: TypeScript (Node.js), Python (FastAPI), Go for performance-critical services
- **Frameworks**: Express.js/Fastify for Node.js, FastAPI for Python
- **Databases**: PostgreSQL with Prisma/SQLAlchemy, Redis for caching
- **API Design**: RESTful APIs with OpenAPI documentation, GraphQL for complex queries

#### DevOps & infrastructure
- **Containerization**: Docker with multi-stage builds
- **Deployment**: Vercel for frontend, Railway/Fly.io for backend services
- **CI/CD**: GitHub Actions with automated testing and deployment
- **Monitoring**: Sentry for error tracking, Vercel Analytics for performance

## Common commands

### Project initialization
```bash
# Node.js/TypeScript project
npm create vite@latest . -- --template react-ts
npm install && npm run dev

# Python project with FastAPI
uv init --name my-project --python 3.12
uv add fastapi uvicorn
uv run uvicorn main:app --reload

# Next.js full-stack app
npx create-next-app@latest . --typescript --tailwind --app --src-dir
npm run dev
```

### Development workflow
```bash
# Install dependencies
npm install  # or: uv sync

# Run development server
npm run dev  # or: uv run uvicorn main:app --reload

# Run tests
npm test     # or: uv run pytest

# Code quality checks
npm run lint && npm run type-check  # or: uv run ruff check . && uv run mypy .
npm run format  # or: uv run black .

# Build for production
npm run build  # or: uv run python -m build
```

### Database operations
```bash
# Prisma (Node.js)
npx prisma generate
npx prisma db push
npx prisma studio

# Alembic (Python)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Project structure patterns

### Frontend (React/Next.js)
```
src/
├── components/         # Reusable UI components
│   ├── ui/            # Base UI components (shadcn/ui)
│   └── features/      # Feature-specific components
├── pages/             # Route components (if using file-based routing)
├── hooks/             # Custom React hooks
├── store/             # State management (Zustand stores)
├── lib/               # Utility functions and configurations
├── types/             # TypeScript type definitions
└── styles/            # Global styles and Tailwind config
```

### Backend (FastAPI)
```
src/
├── api/               # API route handlers
│   ├── v1/           # API version 1 routes
│   └── dependencies/ # Dependency injection
├── core/              # Core application logic
│   ├── config.py     # Configuration management
│   └── security.py   # Authentication & authorization
├── models/            # Database models (SQLAlchemy)
├── schemas/           # Pydantic schemas for validation
├── services/          # Business logic layer
└── tests/             # Test suite
```

## Development principles

### Code quality
- Always use TypeScript for new JavaScript projects
- Write self-documenting code with clear variable names
- Prefer composition over inheritance
- Follow the principle of least surprise
- Use meaningful commit messages (Conventional Commits)

### Performance
- Optimize for Core Web Vitals in frontend applications
- Use lazy loading and code splitting where appropriate
- Implement proper caching strategies (browser, CDN, database)
- Monitor performance with appropriate tooling

### Security
- Always validate user input
- Use environment variables for secrets
- Implement proper authentication and authorization
- Follow OWASP security guidelines
- Regular dependency updates and security audits

### Collaboration
- Use conventional commit messages
- Write comprehensive PR descriptions
- Include tests for all new features and bug fixes
- Document complex business logic and architectural decisions
