---
name: docker-init
description: Generate Dockerfiles and docker-compose.yml with auto-detected services, health checks, security hardening, and resource limits.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[--services postgres,redis] [--prod] [--with-dockerfile]'
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(docker *)
- AskUserQuestion
---

# Docker Init

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

Generate production-ready `docker-compose.yml` and `Dockerfile` with auto-detected services, health checks, resource limits, and security hardening.

## Anti-Hallucination Guidelines

**CRITICAL**: Only generate compose configs based on what the codebase actually uses:
1. **Scan before generating** — Read `package.json`, `pyproject.toml`, `requirements.txt`, etc. before proposing services
2. **Check for existing files** — Read existing `docker-compose.yml` or `Dockerfile` before overwriting
3. **Validate images** — Only use well-known official images; do not invent image tags
4. **No secrets in files** — Never put secrets, passwords, or API keys in compose files; use `env_file`
5. **Check .dockerignore** — If it exists, read it before suggesting changes

## Workflow

### Phase 1: Scan Project

Detect the tech stack and dependencies from manifest files:

```bash
# Node.js
cat package.json 2>/dev/null | grep -E '"(pg|mysql|redis|mongodb|rabbitmq|kafka|meilisearch|elasticsearch|celery)"'

# Python
cat requirements.txt pyproject.toml 2>/dev/null | grep -iE "psycopg|pymysql|redis|pymongo|pika|kafka|celery"

# Ruby
cat Gemfile 2>/dev/null | grep -E "pg|mysql|redis|mongo|sidekiq"

# Go
cat go.mod 2>/dev/null | grep -E "postgres|mysql|redis|mongo"

# Rust
cat Cargo.toml 2>/dev/null | grep -E "postgres|mysql|redis|mongo"
```

Also scan:
- Source files for `DATABASE_URL`, `REDIS_URL`, `MONGODB_URI`, `RABBITMQ_URL` patterns
- Existing `.env.example` for service URLs
- `README.md` for setup instructions mentioning services

Check for existing Docker files:
```bash
ls docker-compose.yml docker-compose.yaml Dockerfile .dockerignore 2>/dev/null
```

If files exist, read them before proposing changes and ask user whether to update or create fresh.

### Phase 2: Propose Services

Map detected dependencies to Docker services. Show the proposal and let user confirm/modify:

**Dependency-to-service mapping**:

| Detected | Proposed Service | Default Image |
|----------|-----------------|---------------|
| `pg`, `psycopg`, `postgres` | PostgreSQL | `postgres:16-alpine` |
| `mysql`, `pymysql` | MySQL | `mysql:8.0` |
| `redis`, `ioredis` | Redis / Valkey | `redis:7-alpine` |
| `mongodb`, `pymongo` | MongoDB | `mongo:7` |
| `rabbitmq`, `pika`, `amqp` | RabbitMQ | `rabbitmq:3-management-alpine` |
| `kafka`, `confluent` | Kafka + Zookeeper | `confluentinc/cp-kafka:latest` |
| `meilisearch` | Meilisearch | `getmeili/meilisearch:latest` |
| `elasticsearch` | Elasticsearch | `elasticsearch:8.12.0` |
| `celery`, `sidekiq` | Redis (queue backend) | `redis:7-alpine` |
| `mailhog`, `smtp`, `mailer` | Mailhog | `mailhog/mailhog:latest` |
| `minio`, `s3` | MinIO | `minio/minio:latest` |

Always ask:
- "Should I include a service for your app itself? (requires Dockerfile)"
- "Should I add Mailhog for local email testing?"

### Phase 3: Generate docker-compose.yml

Generate `docker-compose.yml` (no `version:` field — modern standard) with:

**Every service must include**:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?required}
      POSTGRES_DB: ${POSTGRES_DB:-app_development}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    networks:
      - db
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

**Security defaults** (applied to every service):
```yaml
security_opt:
  - no-new-privileges:true
```

**Network segmentation** (create as needed):
```yaml
networks:
  frontend:    # App <-> reverse proxy
  backend:     # App <-> services
  db:          # Services <-> databases only
```

**Volumes** at the bottom:
```yaml
volumes:
  postgres_data:
  redis_data:
```

**Health check patterns per service**:

| Service | Health Check |
|---------|-------------|
| Postgres | `pg_isready -U ${USER}` |
| MySQL | `mysqladmin ping -h localhost` |
| Redis | `redis-cli ping` |
| MongoDB | `mongosh --eval "db.adminCommand('ping')"` |
| RabbitMQ | `rabbitmq-diagnostics -q ping` |
| MinIO | `mc ready local` |

### Phase 4: Generate Dockerfile (if `--with-dockerfile`)

Generate a multi-stage `Dockerfile` for the detected stack:

**Node.js example**:
```dockerfile
# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:22-alpine AS runtime
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .
USER appuser
EXPOSE 3000
CMD ["node", "src/index.js"]
```

**Python example**:
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
RUN useradd -m -u 1001 appuser
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY --chown=appuser . .
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "app"]
```

Also generate `.dockerignore`:
```
.git
.env
.env.*
node_modules
__pycache__
*.pyc
.pytest_cache
.coverage
dist/
build/
```

### Phase 5: Generate Production Overlay (if `--prod`)

Create `docker-compose.prod.yml` with production hardening:

```yaml
services:
  postgres:
    ports: []          # No direct port exposure
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### Phase 6: Validate

Run validation after generating:

```bash
docker compose config --quiet 2>&1 && echo "Valid" || echo "Errors found"
```

Check that `.dockerignore` exists (create minimal one if missing).
Remind user to add real secrets to `.env` (and verify `.env` is in `.gitignore`).

## Argument Parsing

- `--services <list>`: Comma-separated list of additional services (e.g., `--services postgres,redis,meilisearch`)
- `--prod`: Also generate `docker-compose.prod.yml` with production settings
- `--with-dockerfile`: Also generate `Dockerfile` and `.dockerignore`

## Important Notes

- **No `version:` field** in compose files — deprecated in modern Docker Compose
- **No hardcoded secrets** — Always use `${VAR}` references pointing to `.env`
- **Health checks are required** — Services without health checks cause unreliable startup ordering
- **Non-root users** — App containers must run as non-root; use `USER` in Dockerfile
- **Resource limits** — Always set `deploy.resources.limits` to prevent runaway containers
- **Multi-stage builds** — Required for production Dockerfiles to minimize image size

## Examples

```bash
# Auto-detect and generate docker-compose.yml
/docker-init

# Generate with specific services
/docker-init --services postgres,redis,meilisearch

# Generate compose + Dockerfile
/docker-init --with-dockerfile

# Full production setup
/docker-init --with-dockerfile --prod
```
