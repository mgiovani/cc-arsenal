---
name: env-setup
description: Scans a codebase for environment variable usage to generate or sync .env.example, validate .env completeness against what the code actually reads, and detect leaked secrets in .env or git history. Use for "/env-setup", "update .env.example", "sync .env.example with the codebase", "check if .env has everything it needs", "is .env in .gitignore", or "scan for leaked secrets in .env". Not a full security audit (use review-security for OWASP-level scanning) and not a generic secret-rotation or CI-secrets-injection tool.
metadata:
  summary: "Scan a codebase for env var usage, sync .env.example, and detect leaked secrets"
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: '[scan|validate|sync] [--check-secrets]'
---

# Env Setup

Scan the codebase for environment variable usage, generate or update `.env.example`, validate `.env` completeness, and detect leaked secrets.

## Anti-hallucination guidelines

Only report variables that are actually found in the code:
1. Grep before reporting: never invent variable names, only list what grep actually returns.
2. Read `.env.example` before writing: preserve existing entries, only add/update what changed.
3. No actual secrets: `.env.example` must only contain placeholder values (e.g., `your_api_key_here`).
4. Verify `.gitignore`: actually read the file before claiming `.env` is ignored.
5. Never echo a found secret value: when Phase 6 flags a leaked secret, report the variable name and `file:line` only. Never print, quote, or write the actual value into chat output, a report file, or anywhere else: the scan's job is to locate leaks, not to create a second one.

## Workflow

### Phase 1: Scan Codebase

Grep for environment variable usage matching the project's actual language/framework: see `references/scan-patterns.md` for the ready-to-run pattern per language (Node/TS, Python, Ruby, Rust, Java/Kotlin, Docker Compose, client-exposed prefixes). Only run the pattern(s) for stacks present in the repo.

Also scan:
- `.env.example` (existing entries to preserve)
- `config/` directory for config files referencing env vars
- Framework config files (`next.config.js`, `vite.config.ts`, etc.)

### Phase 2: Categorize Variables

Group discovered variables by prefix/service: see the service prefix table in
`references/scan-patterns.md` for the standard groupings (Database, Cache, Auth, OAuth,
Stripe, AWS, Email, App config, Client vars).

Classify each variable:
- Required vs optional: required if no default/fallback in code.
- Secret vs config: secret if it contains key/secret/password/token in the name.
- Client-exposed: `NEXT_PUBLIC_*`, `VITE_*`; flag if it contains secrets.

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

For `scan` or `sync` operations:

Generate `.env.example` with:
- SCREAMING_SNAKE_CASE variable names
- Grouped by service (with section comments)
- Placeholder values for secrets, real defaults for config
- Type and description comments

```bash
# =============================================================================
# Database
# =============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/app_development
JWT_SECRET=your_jwt_secret_here  # openssl rand -hex 32
```

Full section-header style and rules (preserve existing entries, only add what's missing,
never a real value), see `references/env-example-template.md`, load it when writing the
actual file.

### Phase 5: Validate .env (if `validate` subcommand or `.env` exists)

Read `.env` by key name only, never with `Read` or `cat` (they print values): `grep -nE '^(export )?[A-Za-z_][A-Za-z0-9_]*=' .env | cut -d= -f1`, and `grep -nE '=\s*$' .env | cut -d= -f1` for empty values. Check:

1. Missing required variables: every variable in code without a default/fallback must be set.
2. Empty values: `VAR=` with no value is suspicious for required vars.
3. Stale variables: present in `.env` but not found in codebase scan.
4. `.gitignore` check: verify `.env` (and `.env.local`) are in `.gitignore`.

```bash
grep -E "^\.env" .gitignore 2>/dev/null
```

Warn clearly if `.env` is NOT in `.gitignore`.

### Phase 6: Secret Detection (if `--check-secrets`)

Scan `.env`, git history and source for secrets. Every command below emits only variable names and `file:line`, never a value. Do not swap in a plain `grep` (or `Read`) that prints matching lines.

Requires `gitleaks` (`brew install gitleaks`); if `command -v gitleaks` finds nothing, skip to the grep checks.

```bash
gitleaks detect --source=. --redact --no-banner -v
```

Grep checks, which also work without gitleaks:

```bash
# Secret-looking assignments in .env: line:NAME
grep -inE "(password|secret|api_key|private_key|token|auth_key)\s*=\s*['\"]?[A-Za-z0-9+/_.=-]{16,}" .env 2>/dev/null | cut -d= -f1

# Known key formats hardcoded in files: file:line
grep -rnIE "(AKIA[0-9A-Z]{16}|sk_live_[A-Za-z0-9]+|xox[abp]-[A-Za-z0-9-]+|gh[pousr]_[A-Za-z0-9]{36})" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null | cut -d: -f1,2

# Commits that added .env to history
git log --all --full-history --diff-filter=A --format=%h -- .env 2>/dev/null

# Secret-looking names that appeared in .env history
git log --all --full-history -p --format= -- .env 2>/dev/null | grep -iE "^\+.*(password|secret|key)\s*=" | cut -d= -f1 | sort -u
```

The character class includes `_`, `-`, `.` alongside base64's `+/=`: most real key formats
(`sk_live_...`, `xoxb-...`, `AKIA...`) contain underscores or hyphens, and a base64-only class
silently misses them.

Report each hit as a commit + `file:line` reference plus the variable name (e.g. `.env:12 STRIPE_SECRET_KEY`),
never paste the matched value itself into the report.

Flag client-exposed secrets:
- Check `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*` variables
- If any contain "secret", "key", "password", "token" in the name, warn loudly, by variable name only

Recommend pre-commit tools:
- `detect-secrets` (Python): `pip install detect-secrets && detect-secrets scan > .secrets.baseline`
- `gitleaks`: `gitleaks detect --source=. --redact --no-banner -v`

## Argument Parsing

- `scan` (default): Scan codebase, generate/update `.env.example`
- `validate`: Validate `.env` against discovered variables
- `sync`: Sync `.env.example` to match current codebase (add missing, mark stale)
- `--check-secrets`: Enable secret detection in `.env` and git history

## Important Notes

| Note | Detail |
|---|---|
| Never include real secrets | `.env.example` holds only placeholder values |
| Never echo a found secret's value | report variable name + `file:line` only, whether the finding goes to chat or a report file |
| Client-exposed vars | `NEXT_PUBLIC_*`, `VITE_*` are bundled into the frontend; flag if their name suggests a secret |
| `.env` must be gitignored | verify and warn if not |
| Historical leaks matter | even if `.env` is gitignored now, it may have been committed in the past |
| Stale variables | unused entries in `.env` can be security risks; document and remove them |
