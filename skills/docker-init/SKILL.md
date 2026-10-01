---
name: docker-init
description: Generates production-ready docker-compose.yml and Dockerfile(s) for a project by scanning its manifest files (package.json, pyproject.toml, Gemfile, go.mod, Cargo.toml) and source code for service dependencies (Postgres, MySQL, Redis, MongoDB, RabbitMQ, Kafka, Elasticsearch, MinIO, Mailhog, etc.), then emitting compose services with health checks, security hardening, resource limits, and non-root Dockerfiles. Use when the user asks to dockerize or containerize a project, add docker-compose, generate a Dockerfile, or set up local dev services in containers. Not for CI/CD pipeline configs (use ci-generate), database schema migrations (use db-migrate), or scanning/syncing environment variables and secrets (use env-setup).
metadata:
  summary: "Generate Dockerfiles and docker-compose.yml with auto-detected services and security hardening"
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: '[--services postgres,redis] [--prod] [--with-dockerfile]'
---

# Docker Init

Generate production-ready `docker-compose.yml` and `Dockerfile` with auto-detected services, health checks, resource limits, and security hardening.

## Guardrails

Only generate configs based on what the codebase actually uses:
1. Scan before generating: read `package.json`, `pyproject.toml`, `requirements.txt`, etc. before proposing services.
2. Read existing files first: if `docker-compose.yml` or `Dockerfile` already exist, read them fully before proposing any change, and ask the user whether to update in place or regenerate. Never overwrite an existing service definition you haven't read.
3. Only well-known official images: do not invent image names or tags.
4. No secrets in files: never put secrets, passwords, or API keys in compose files, use `${VAR}` references pointing at `.env` instead.
5. Read `.dockerignore` before changing it, if it exists.

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

Map detected dependencies to Docker services and show the proposal for the user to confirm/modify. See `references/service-catalog.md` for the full dependency-to-image mapping, load it whenever the scan surfaces a dependency not already covered by the examples in this file.

Only ask about services the scan didn't already resolve:
- If no Dockerfile exists and the scan found no app service in an existing compose file, ask whether to include one (requires `--with-dockerfile`).
- If the mapping surfaced a mail-related dependency (`mailhog`, `smtp`, `mailer`), ask whether to add Mailhog, don't ask otherwise.

### Phase 3: Generate docker-compose.yml

Generate `docker-compose.yml` with no `version:` key (deprecated in modern Compose). Every service must meet these goals:

- Official image with a pinned tag (see `references/service-catalog.md`), alpine/slim variant when one exists.
- A `healthcheck` with `interval`, `timeout`, `retries` and a `start_period` sized to the service's boot time; commands are in the catalog. Dependents wait with `depends_on: condition: service_healthy`.
- `security_opt: [no-new-privileges:true]`, on every service.
- `deploy.resources.limits` for `cpus` and `memory`.
- `restart: unless-stopped`.
- Credentials as `${VAR}` references to `.env`, with `${VAR:?required}` for passwords and `${VAR:-default}` for harmless values such as user and database name.
- Data in named volumes declared at the bottom of the file.
- Networks only as needed for segmentation: for example `frontend` (app and reverse proxy), `backend` (app and services), `db` (services and databases only).

**Kafka defaults to KRaft mode, not Zookeeper.** A Zookeeper-backed Kafka is legacy topology and adds a second container for no benefit in a dev/prod compose file. Use the single-node KRaft form unless the user explicitly asks for a Zookeeper-based cluster:

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

Write a `Dockerfile` for the detected stack that meets these goals:

- Multi-stage: dependencies and build tooling in a build stage, only runtime dependencies and build output in the final stage (no compilers, dev dependencies or package-manager caches).
- Slim or alpine base image pinned to a specific version tag, the same major version the project declares (`.nvmrc`, `engines`, `requires-python`, `go.mod`).
- Dependency manifests copied and installed before the source, so the dependency layer caches; installs use the lockfile (`npm ci`, `uv sync --frozen`, `bundle config set deployment true`).
- A dedicated non-root user created in the final stage and activated with `USER` before `CMD`.
- No secrets in any layer: no `COPY .env`, no secrets in `ARG`/`ENV`; use BuildKit `--mount=type=secret` when a build needs one.
- A `HEALTHCHECK` when the app serves HTTP or another probeable port; skip it for workers and CLIs.
- `EXPOSE` for the real port, and exec-form `CMD`.

Also write a `.dockerignore` that excludes VCS data, `.env*`, dependency directories, caches and build output, and the `Dockerfile` and compose files themselves.

### Phase 5: Generate Production Overlay (if `--prod`)

Create `docker-compose.prod.yml` as an overlay that only holds the differences from the base file:

- No host port publishing for backing services (`ports: []`).
- `restart: always`.
- Tighter `deploy.resources.limits` than the dev defaults.
- Bounded `json-file` logs (`max-size`, `max-file`).

### Phase 6: Validate

Copy this checklist and tick each step:

```
- [ ] hadolint Dockerfile   (skip if no Dockerfile)
- [ ] docker build -t <project>-check .   (skip if no Dockerfile)
- [ ] docker compose config --quiet   (add -f docker-compose.yml -f docker-compose.prod.yml if --prod)
- [ ] .dockerignore exists and .env is in .gitignore
```

hadolint install: `brew install hadolint`, or without installing, `docker run --rm -i hadolint/hadolint < Dockerfile`.

Fix every finding, then re-run the failed step and the ones after it. Stop after 3 rounds and report what still fails. Don't suppress a hadolint rule to get green unless the reason is stated to the user.

If a tool is unavailable (no `docker`, no `hadolint`), skip its steps and tell the user which checks were skipped and the commands to run once the tool is available. Never claim a check passed that was not run.

Remind the user to add real secrets to `.env`.

## Argument Parsing

- `--services <list>`: Comma-separated list of additional services (e.g., `--services postgres,redis,meilisearch`)
- `--prod`: Also generate `docker-compose.prod.yml` with production settings
- `--with-dockerfile`: Also generate `Dockerfile` and `.dockerignore`

## Important Notes

- No `version:` field in compose files: deprecated in modern Docker Compose.
- No hardcoded secrets: always use `${VAR}` references pointing to `.env`.
- Every service needs a health check; without one, startup ordering between dependent services is unreliable.
- App containers run as non-root: create the user in the Dockerfile and switch with `USER`.
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
