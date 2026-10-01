# Scan patterns and variable categories

## Per-language scan patterns

Every pattern uses `-o`, so a line's hardcoded default (e.g. `os.getenv("KEY", "sk_live_...")`) is never printed; keep `-o` on the first grep when adapting them. Run only the pattern(s) matching the project's detected stack (check for `package.json`, `requirements.txt`/`pyproject.toml`, `Gemfile`, `Cargo.toml`, `pom.xml`/`build.gradle`).

Node.js / TypeScript:
```bash
grep -rhoE "process\.env\.[A-Z_][A-Z0-9_]*" --include="*.ts" --include="*.js" --include="*.mjs" . \
  | grep -oE "process\.env\.[A-Z_][A-Z0-9_]*" | sort -u
```

Python:
```bash
grep -rhoE 'os\.environ\[["'"'"'][A-Z_][A-Z0-9_]*|os\.getenv\(["'"'"'][A-Z_][A-Z0-9_]*' \
  --include="*.py" . | grep -oE '[A-Z_][A-Z0-9_]*$' | sort -u
```

Ruby:
```bash
grep -rhoE 'ENV\[["'"'"'][A-Z_][A-Z0-9_]*["'"'"']\]' --include="*.rb" . \
  | grep -oE 'ENV\["[^"]*"\]' | grep -oE '"[^"]+"' | tr -d '"' | sort -u
```

Rust:
```bash
grep -rhoE 'env::var\("[A-Z_][A-Z0-9_]*"\)' --include="*.rs" . \
  | grep -oE '"[A-Z_][A-Z0-9_]*"' | tr -d '"' | sort -u
```

Java / Kotlin:
```bash
grep -rhoE 'System\.getenv\("[A-Z_][A-Z0-9_]*"\)' --include="*.java" --include="*.kt" . \
  | grep -oE '"[A-Z_][A-Z0-9_]*"' | tr -d '"' | sort -u
```

Framework-specific prefixes (scan for these in config files):
- `NEXT_PUBLIC_*`: Next.js client-exposed variables
- `VITE_*`: Vite client-exposed variables
- `REACT_APP_*`: Create React App client-exposed variables
- `NUXT_PUBLIC_*`: Nuxt.js public variables

Docker Compose:
```bash
grep -rhoE "^\s+- [A-Z_][A-Z0-9_]*=" docker-compose.yml docker-compose.*.yml 2>/dev/null \
  | grep -oE "[A-Z_][A-Z0-9_]*=" | tr -d "=" | sort -u
```

## Service prefix groups

Group discovered variables by prefix/service for reporting and for `.env.example` section headers:

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
