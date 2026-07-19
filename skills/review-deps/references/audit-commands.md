# Dependency Review - Audit Command Reference

Load this when running Phase 2. Run the command(s) for each package manager detected in Phase 1. Prefer JSON output when available (easier to parse in Phase 3); fall back to plain text if the JSON flag errors.

**Node.js (npm/yarn/pnpm):**
```bash
# npm
npm audit --json 2>/dev/null || npm audit 2>&1

# yarn (classic)
yarn audit --json 2>/dev/null || yarn audit 2>&1

# pnpm
pnpm audit --json 2>/dev/null || pnpm audit 2>&1
```

**Python (pip/uv):**
```bash
# pip-audit (preferred — install if missing)
pip-audit --format=json 2>/dev/null || pip-audit 2>&1

# If pip-audit unavailable, use pip
pip audit 2>&1 || python -m pip_audit 2>&1

# uv
uv pip audit 2>&1
```

**Rust:**
```bash
cargo audit 2>&1
```

**Go:**
```bash
go list -m -json all 2>&1
govulncheck ./... 2>&1
```

**PHP:**
```bash
composer audit --format=json 2>/dev/null || composer audit 2>&1
```

**Ruby:**
```bash
bundle audit check 2>&1
```

**.NET:**
```bash
dotnet list package --vulnerable --include-transitive 2>&1
```

**Java (Maven/Gradle):**
```bash
mvn dependency-check:check 2>&1 || echo "OWASP dependency-check plugin not configured"
```

**GitHub Dependabot (always attempt if in a git repo):**
```bash
# Get repository owner/name from git remote
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[] | {package: .security_advisory.summary, severity: .security_advisory.severity, state: .state, package_name: .dependency.package.name, ecosystem: .dependency.package.ecosystem}' 2>&1
```

## Quick Reference Table

| Ecosystem | Audit Command | JSON Output | Install |
|-----------|--------------|-------------|---------|
| npm | `npm audit` | `--json` | Built-in |
| yarn | `yarn audit` | `--json` | Built-in |
| pnpm | `pnpm audit` | `--json` | Built-in |
| pip | `pip-audit` | `--format=json` | `pip install pip-audit` |
| uv | `uv pip audit` | — | Built-in with uv |
| cargo | `cargo audit` | `--json` | `cargo install cargo-audit` |
| go | `govulncheck ./...` | `--json` | `go install golang.org/x/vuln/cmd/govulncheck@latest` |
| composer | `composer audit` | `--format=json` | Built-in (2.4+) |
| bundler | `bundle audit check` | — | `gem install bundler-audit` |
| .NET | `dotnet list package --vulnerable` | — | Built-in |
| Maven | OWASP dependency-check plugin | — | Plugin config required |
| Dependabot | `gh api repos/{owner}/{repo}/dependabot/alerts` | Native JSON | GitHub CLI |

Save all raw output (including "tool not installed" errors) — Phase 3 needs to know what actually ran vs. what's unavailable, and the final report must state which tools didn't run rather than silently omitting that ecosystem.
