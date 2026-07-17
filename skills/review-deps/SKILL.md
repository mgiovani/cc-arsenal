---
name: review-deps
description: Audit project dependencies for vulnerabilities, license compliance risks,
  and staleness by running native audit tools (npm audit, pip-audit, cargo audit, etc.),
  querying Dependabot alerts, and dispatching parallel agents for CVE analysis, license
  risk, and upgrade complexity. Use when the user wants to check for vulnerable packages,
  audit licenses, plan dependency upgrades, assess supply chain risk, or asks "are our
  dependencies safe/up to date/license-compliant". Analysis only, no code or lock-file
  changes. Not for app-code vulnerability scanning (use review-security) or auto-applying
  upgrades (this skill only recommends, never runs installs).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
---

# Dependency Review

Comprehensive dependency audit covering vulnerability scanning, license compliance, and staleness analysis. This skill performs **analysis only** — it never modifies code, lock files, or manifests, and never auto-installs upgrades or missing audit tools (it reports them as unavailable instead).

Cite exact package names/versions/CVE IDs from actual tool output — never estimate or invent them.

## Audit Workflow

### Phase 1: Detect Package Managers & Technology Stack

Discover all package managers present in the project:

```
Use Glob to check for the existence of these files:
- package.json / package-lock.json / yarn.lock / pnpm-lock.yaml → npm/yarn/pnpm (Node.js)
- pyproject.toml / requirements*.txt / Pipfile / setup.py → pip/uv/poetry (Python)
- Cargo.toml / Cargo.lock → cargo (Rust)
- go.mod / go.sum → go modules (Go)
- composer.json / composer.lock → composer (PHP)
- Gemfile / Gemfile.lock → bundler (Ruby)
- *.csproj / packages.config / Directory.Packages.props → NuGet (.NET)
- pom.xml / build.gradle / build.gradle.kts → Maven/Gradle (Java/Kotlin)
Read each detected manifest to understand:
- Total number of direct dependencies
- Total number of dev dependencies
- Whether lock files are present and committed
- Workspace/monorepo structure (multiple package.json, Cargo.toml workspaces, etc.)

### Phase 2: Run Native Audit Commands

Execute the appropriate audit commands for each detected package manager. Run independent commands in parallel.

**Node.js (npm/yarn/pnpm):**
```bash
# npm
npm audit --json 2>/dev/null || npm audit 2>&1

# yarn (classic)
yarn audit --json 2>/dev/null || yarn audit 2>&1

# pnpm
pnpm audit --json 2>/dev/null || pnpm audit 2>&1
**Python (pip/uv):**
```bash
# pip-audit (preferred — install if missing)
pip-audit --format=json 2>/dev/null || pip-audit 2>&1

# If pip-audit unavailable, use pip
pip audit 2>&1 || python -m pip_audit 2>&1

# uv
uv pip audit 2>&1
**Rust:**
```bash
cargo audit 2>&1
**Go:**
```bash
go list -m -json all 2>&1
govulncheck ./... 2>&1
**PHP:**
```bash
composer audit --format=json 2>/dev/null || composer audit 2>&1
**Ruby:**
```bash
bundle audit check 2>&1
**.NET:**
```bash
dotnet list package --vulnerable --include-transitive 2>&1
**Java (Maven/Gradle):**
```bash
mvn dependency-check:check 2>&1 || echo "OWASP dependency-check plugin not configured"
**GitHub Dependabot (always attempt if in a git repo):**
```bash
# Get repository owner/name from git remote
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[] | {package: .security_advisory.summary, severity: .security_advisory.severity, state: .state, package_name: .dependency.package.name, ecosystem: .dependency.package.ecosystem}' 2>&1
Save all raw output for agent analysis in Phase 3.

### Phase 3: Parallel Specialist Analysis

Spawn 3 parallel Explore agents, each focused on a different risk dimension. Pass the raw audit output from Phase 2 and the manifest files to each agent.

For detailed agent prompts and analysis patterns, see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1 — Vulnerability Analysis**: CVE/GHSA triage, severity assessment, exploitability, fix availability
- **Agent 2 — License Compliance**: License identification, copyleft risk, commercial compatibility, policy violations
- **Agent 3 — Staleness & Upgrade Complexity**: Version drift, maintenance health, breaking change assessment, upgrade paths

Each agent must:
1. Analyze the raw audit output and manifest files
2. Read lock files for transitive dependency details when needed
3. Provide structured findings with evidence from actual tool output
4. Classify risk level (Critical/High/Medium/Low)
5. Recommend specific actions with exact target versions

### Phase 4: Risk Assessment & Prioritization

After all agents complete:

1. **Collect all findings** from the 3 parallel agents
2. **Deduplicate** — Remove findings reported by multiple agents
3. **Cross-reference** — Combine vulnerability + license + staleness data per package
4. **Prioritize by composite risk**:
 - **Critical**: Known exploited CVEs (CISA KEV), RCE vulnerabilities, packages with no maintained fork
 - **High**: High-severity CVEs with public exploits, copyleft license in proprietary project, packages 3+ major versions behind
 - **Medium**: Medium-severity CVEs without public exploit, permissive-but-unusual licenses, packages 1-2 major versions behind
 - **Low**: Low-severity CVEs, informational license notes, minor version drift
5. **Group by action type**: Security patches (non-breaking) vs. major upgrades (breaking) vs. replacements (abandoned packages)
6. **Statistics**: Count total dependencies, vulnerable, license-risky, stale

### Phase 5: Generate Dependency Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

### Phase 6: Verification & Quality Check

Before presenting the report, verify:
1. Every vulnerability finding has a CVE/GHSA ID or audit tool reference
2. Every finding references the exact installed version and fix version
3. License findings reference the actual license field from the package manifest
4. Staleness findings include current version, latest version, and release date
5. Statistics are accurate (counted from actual tool output, not estimated)
6. No duplicate findings across categories
7. Risk ratings are justified with evidence
8. Upgrade recommendations include breaking change warnings where applicable
9. No invented CVEs, license types, or version numbers
10. Dependabot alerts are reconciled with local audit results

## Scoping

By default, run all three dimensions (vulnerabilities, licenses, staleness) at medium severity and above. If the user asks to scope to just one dimension (e.g. "just check for vulnerabilities" or "license risk only"), run only that phase. If they ask to filter by severity (e.g. "critical only"), filter the report to that level and above.

## Limitations

- **Static analysis only**: Cannot detect runtime-only vulnerabilities
- **Tool dependent**: Accuracy depends on the installed audit tools and their databases
- **License heuristic**: License detection relies on package metadata which may be incomplete
- **No private registry support**: May not detect vulnerabilities in packages from private registries
- **Transitive depth**: Some ecosystems have limited transitive vulnerability data
- **Advisory lag**: New CVEs may not be in audit databases for 24-48 hours after disclosure

## References

- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [GitHub Advisory Database](https://github.com/advisories)
- [CISA Known Exploited Vulnerabilities](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [SPDX License List](https://spdx.org/licenses/)
- [OSI Approved Licenses](https://opensource.org/licenses/)
- [OpenSSF Scorecard](https://securityscorecards.dev/)
