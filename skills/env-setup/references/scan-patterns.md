# Per-Language Env Var Scan Patterns

Run only the pattern(s) matching the project's detected stack (check for `package.json`, `requirements.txt`/`pyproject.toml`, `Gemfile`, `Cargo.toml`, `pom.xml`/`build.gradle`).

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
