---
name: docker-init
description: Generates production-ready docker-compose.yml and Dockerfile(s) for a project by scanning its manifest files (package.json, pyproject.toml, Gemfile, go.mod, Cargo.toml) and source code for service dependencies (Postgres, MySQL, Redis, MongoDB, RabbitMQ, Kafka, Elasticsearch, MinIO, Mailhog, etc.), then emitting compose services with health checks, security hardening, resource limits, and non-root Dockerfiles. Use when the user asks to dockerize or containerize a project, add docker-compose, generate a Dockerfile, or set up local dev services in containers. Not for CI/CD pipeline configs (use ci-generate), database schema migrations (use db-migrate), or scanning/syncing environment variables and secrets (use env-setup).
metadata:
  author: mgiovani
  version: 1.1.0
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

Generate production-ready `docker-compose.yml` and `Dockerfile` with auto-detected services, health checks, resource limits, and security hardening.

## Guardrails

Only generate configs based on what the codebase actually uses:
1. **Scan before generating** — read `package.json`, `pyproject.toml`, `requirements.txt`, etc. before proposing services.
2. **Read existing files first** — if `docker-compose.yml` or `Dockerfile` already exist, read them fully before proposing any change, and ask the user whether to update in place or regenerate. Never overwrite an existing service definition you haven't read.
3. **Only well-known official images** — do not invent image names or tags.
4. **No secrets in files** — never put secrets, passwords, or API keys in compose files; use `${VAR}` references pointing at `.env`.
5. **Read `.dockerignore` before changing it**, if it exists.

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

### Phase 2: Propose Services

Map detected dependencies to Docker services and show the proposal for the user to confirm/modify. See `references/service-catalog.md` for the full dependency-to-image mapping — load it whenever the scan surfaces a dependency not already covered by the examples in this file.

Only ask about services the scan didn't already resolve:
- If no Dockerfile exists and the scan found no app service in an existing compose file, ask whether to include one (requires `--with-dockerfile`).
- If the mapping surfaced a mail-related dependency (`mailhog`, `smtp`, `mailer`), ask whether to add Mailhog — don't ask otherwise.

### Phase 3: Generate docker-compose.yml

Generate `docker-compose.yml` with no `version:` key (deprecated in modern Compose). Every service needs a health check, security hardening, and resource limits:

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
    security_opt:
      - no-new-privileges:true
    networks:
      - db
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

`security_opt: [no-new-privileges:true]` applies to every service, not just Postgres.

**Networks** (create as needed for segmentation):
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

**Kafka defaults to KRaft mode, not Zookeeper.** A Zookeeper-backed Kafka is legacy topology and adds a second container for no benefit in a dev/prod compose file — use the single-node KRaft form unless the user explicitly asks for a Zookeeper-based cluster:

```yaml
services:
  kafka:
    image: apache/kafka:latest   # pin to a specific tag (e.g. 3.8.0) before deploying to prod
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions.sh --bootstrap-server localhost:9092"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
```

Health check commands for other services (Postgres, MySQL, Redis, MongoDB, RabbitMQ, MinIO) are in `references/service-catalog.md`.

### Phase 4: Generate Dockerfile (if `--with-dockerfile`)

Generate a multi-stage `Dockerfile` for the detected stack. The runtime stage must create and switch to a non-root user:

**Node.js**:
```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:22-alpine AS runtime
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .
USER appuser
EXPOSE 3000
CMD ["node", "src/index.js"]
```

**Python**:
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

Create `docker-compose.prod.yml` with production hardening — no direct port exposure, `restart: always`, tighter resource limits, bounded log files:

```yaml
services:
  postgres:
    ports: []
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

```bash
docker compose config --quiet 2>&1 && echo "Valid" || echo "Errors found"
```

If `docker` isn't installed or the command isn't found, skip this step and tell the user to run it themselves once Docker is available — don't claim the config was validated when it wasn't.

Check that `.dockerignore` exists (create a minimal one if missing). Remind the user to add real secrets to `.env` and verify `.env` is in `.gitignore`.

## Argument Parsing

- `--services <list>`: Comma-separated list of additional services (e.g., `--services postgres,redis,meilisearch`)
- `--prod`: Also generate `docker-compose.prod.yml` with production settings
- `--with-dockerfile`: Also generate `Dockerfile` and `.dockerignore`

## Important Notes

- No `version:` field in compose files — deprecated in modern Docker Compose.
- No hardcoded secrets — always use `${VAR}` references pointing to `.env`.
- Every service needs a health check; without one, startup ordering between dependent services is unreliable.
- App containers run as non-root — create the user in the Dockerfile and switch with `USER`.
- Set `deploy.resources.limits` on every service to prevent a runaway container from starving the host.
- Production Dockerfiles use multi-stage builds to keep the final image small.

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
