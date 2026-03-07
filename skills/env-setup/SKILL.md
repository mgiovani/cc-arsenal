---
name: env-setup
description: Scan codebase for environment variables, generate .env.example, validate .env completeness, and detect leaked secrets.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[scan|validate|sync] [--check-secrets]'
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(git *)
- AskUserQuestion
---

# Env Setup

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

Scan the codebase for environment variable usage, generate or update `.env.example`, validate `.env` completeness, and detect leaked secrets.

## Anti-Hallucination Guidelines

**CRITICAL**: Only report variables that are actually found in the code:
1. **Grep before reporting** — Never invent variable names; only list what grep actually returns
2. **Read .env.example before writing** — Preserve existing entries; only add/update what changed
3. **No actual secrets** — `.env.example` must only contain placeholder values (e.g., `your_api_key_here`)
4. **Verify .gitignore** — Actually read the file before claiming `.env` is ignored

## Workflow

### Phase 1: Scan Codebase

Grep for environment variable patterns per language/framework:

**Node.js / TypeScript**:
```bash
grep -rE "process\.env\.([A-Z_][A-Z0-9_]*)" --include="*.ts" --include="*.js" --include="*.mjs" -h . \
  | grep -oE "process\.env\.[A-Z_][A-Z0-9_]*" | sort -u
```

**Python**:
```bash
grep -rE 'os\.environ\[["'"'"']([A-Z_][A-Z0-9_]*)["'"'"']\]|os\.getenv\(["'"'"']([A-Z_][A-Z0-9_]*)["'"'"']' \
  --include="*.py" -h . | grep -oE '[A-Z_][A-Z0-9_]+' | sort -u
```

**Ruby**:
```bash
grep -rE 'ENV\[["'"'"']([A-Z_][A-Z0-9_]*)["'"'"']\]' --include="*.rb" -h . \
  | grep -oE 'ENV\["[^"]*"\]' | grep -oE '"[^"]+"' | tr -d '"' | sort -u
```

**Rust**:
```bash
grep -rE 'env::var\("([A-Z_][A-Z0-9_]*)"\)' --include="*.rs" -h . \
  | grep -oE '"[A-Z_][A-Z0-9_]*"' | tr -d '"' | sort -u
```

**Java / Kotlin**:
```bash
grep -rE 'System\.getenv\("([A-Z_][A-Z0-9_]*)"\)' --include="*.java" --include="*.kt" -h . \
  | grep -oE '"[A-Z_][A-Z0-9_]*"' | tr -d '"' | sort -u
```

**Framework-specific prefixes** (scan for these in config files):
- `NEXT_PUBLIC_*` — Next.js client-exposed variables
- `VITE_*` — Vite client-exposed variables
- `REACT_APP_*` — Create React App client-exposed variables
- `NUXT_PUBLIC_*` — Nuxt.js public variables

**Docker Compose**:
```bash
grep -rE "^\s+- [A-Z_][A-Z0-9_]*=" docker-compose.yml docker-compose.*.yml 2>/dev/null \
  | grep -oE "[A-Z_][A-Z0-9_]*=" | tr -d "=" | sort -u
```

Also scan:
- `.env.example` (existing entries to preserve)
- `config/` directory for config files referencing env vars
- Framework config files (`next.config.js`, `vite.config.ts`, etc.)

### Phase 2: Categorize Variables

Group discovered variables by prefix/service:

```
Database:    DATABASE_URL, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
Cache:       REDIS_URL, REDIS_HOST, REDIS_PORT
Auth:        JWT_SECRET, AUTH_SECRET, NEXTAUTH_SECRET, SESSION_SECRET
OAuth:       GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GITHUB_CLIENT_ID
Stripe:      STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET
AWS:         AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET
Email:       SMTP_HOST, SMTP_PORT, SENDGRID_API_KEY, RESEND_API_KEY
App config:  NODE_ENV, PORT, BASE_URL, APP_URL
Client vars: NEXT_PUBLIC_*, VITE_*, REACT_APP_*
```

Classify each variable:
- **Required vs Optional** (required if no default/fallback in code)
- **Secret vs Config** (secret if it contains key/secret/password/token in name)
- **Client-exposed** (`NEXT_PUBLIC_*`, `VITE_*` — flag if contains secrets)

### Phase 3: Compare with .env.example

Read existing `.env.example` (if it exists):

```bash
# Variables in code but NOT in .env.example (missing)
# Variables in .env.example but NOT in code (undocumented/stale)
# Variables in both (up to date)
```

Report:
- Missing vars (need to be added to `.env.example`)
- Stale vars (in `.env.example` but no longer used)
- Up-to-date vars

### Phase 4: Generate / Update .env.example

**For `scan` or `sync` operations**:

Generate `.env.example` with:
- SCREAMING_SNAKE_CASE variable names
- Grouped by service (with section comments)
- Placeholder values for secrets, real defaults for config
- Type and description comments

Example output format:
```bash
# =============================================================================
# Database
# =============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/app_development
DB_HOST=localhost
DB_PORT=5432

# =============================================================================
# Authentication
# =============================================================================
# Generate with: openssl rand -hex 32
JWT_SECRET=your_jwt_secret_here
NEXTAUTH_SECRET=your_nextauth_secret_here

# =============================================================================
# Stripe (https://dashboard.stripe.com/apikeys)
# =============================================================================
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# =============================================================================
# App Config
# =============================================================================
NODE_ENV=development
PORT=3000
BASE_URL=http://localhost:3000
```

**Rules**:
- Never include real values from `.env` — only placeholders
- Preserve existing comments and groupings in `.env.example`
- When updating, only add missing variables; do not reorder existing ones

### Phase 5: Validate .env (if `validate` subcommand or `.env` exists)

Read `.env` and check:

1. **Missing required variables**: Every variable in code without a default/fallback must be set
2. **Empty values**: `VAR=` with no value is suspicious for required vars
3. **Stale variables**: Present in `.env` but not found in codebase scan
4. **`.gitignore` check**: Verify `.env` (and `.env.local`) are in `.gitignore`

```bash
grep -E "^\.env" .gitignore 2>/dev/null
```

Warn clearly if `.env` is NOT in `.gitignore`.

### Phase 6: Secret Detection (if `--check-secrets`)

**Scan `.env` for high-entropy strings and known secret patterns**:

```bash
# Check for common secret patterns
grep -iE "(password|secret|api_key|private_key|token|auth_key)\s*=\s*['\"]?[a-zA-Z0-9+/]{20,}" .env 2>/dev/null
```

**Check git history for leaked secrets**:
```bash
git log --all --full-history --diff-filter=A -p -- .env 2>/dev/null | grep -iE "(password|secret|key)\s*=" | head -20
```

**Flag client-exposed secrets**:
- Check `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*` variables
- If any contain "secret", "key", "password", "token" in the name — warn loudly

**Recommend pre-commit tools**:
- `detect-secrets` (Python): `pip install detect-secrets && detect-secrets scan > .secrets.baseline`
- `gitleaks`: `gitleaks detect --source=.`

## Argument Parsing

- `scan` (default): Scan codebase, generate/update `.env.example`
- `validate`: Validate `.env` against discovered variables
- `sync`: Sync `.env.example` to match current codebase (add missing, mark stale)
- `--check-secrets`: Enable secret detection in `.env` and git history

## Important Notes

- **NEVER include real secrets** in `.env.example` — only placeholder values
- **Client-exposed vars** (`NEXT_PUBLIC_*`, `VITE_*`) are bundled into the frontend — never put secrets there
- **`.env` must be gitignored** — always verify and warn if not
- **Historical leaks matter** — even if `.env` is gitignored now, it may have been committed in the past
- **Stale variables** in `.env` can be security risks — document and remove unused ones

## Examples

```bash
# Scan codebase and generate .env.example
/env-setup

# Scan with explicit subcommand
/env-setup scan

# Validate existing .env completeness
/env-setup validate

# Sync .env.example with current codebase
/env-setup sync

# Full scan + secret detection
/env-setup scan --check-secrets
```
