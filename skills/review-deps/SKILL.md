---
name: review-deps
description: "Audit project dependencies for vulnerabilities, license compliance risks, and staleness. Runs native audit tools (npm audit, pip audit, cargo audit, etc.), queries Dependabot alerts, and dispatches parallel agents for CVE analysis, license risk, and upgrade complexity. This skill should be used when users want to review dependencies, check for vulnerable packages, audit licenses, plan upgrades, or assess supply chain risk."
disable-model-invocation: true
argument-hint: "[--scope vulnerabilities|licenses|staleness|all] [--severity critical|high|medium|low]"
allowed-tools: Read, Grep, Glob, Bash(npm *, npx *, pip *, pip-audit *, uv *, cargo *, go *, gh *, python *, composer *, bundle *, dotnet *, mvn *, gradle *), Task, TodoWrite, AskUserQuestion
context: fork
agent: general-purpose
---

# Dependency Review

Comprehensive dependency audit covering vulnerability scanning, license compliance, and staleness analysis. This skill performs **analysis only** — it identifies risks and recommends upgrades without modifying code or lock files.

## Anti-Hallucination Guidelines

**CRITICAL**: Dependency reviews must be based on ACTUAL tool output and VERIFIED data:
1. **Run before claiming** — Never report vulnerabilities without running the actual audit tool
2. **Evidence-based findings** — Every finding must reference specific package names and versions
3. **No invented CVEs** — Only reference CVE/GHSA identifiers returned by audit tools or Dependabot
4. **Tool output required** — Copy exact output from audit commands as evidence
5. **Quantifiable results** — Count actual issues from tool output, do not estimate
6. **No false positives** — Verify each finding against actual installed versions
7. **Version accuracy** — Report exact installed version and exact fix version from tool output

## Audit Workflow

### Phase 1: Detect Package Managers & Technology Stack

Discover all package managers present in the project:

```
Use Glob to check for the existence of these files:
- package.json / package-lock.json / yarn.lock / pnpm-lock.yaml  →  npm/yarn/pnpm (Node.js)
- pyproject.toml / requirements*.txt / Pipfile / setup.py         →  pip/uv/poetry (Python)
- Cargo.toml / Cargo.lock                                         →  cargo (Rust)
- go.mod / go.sum                                                  →  go modules (Go)
- composer.json / composer.lock                                    →  composer (PHP)
- Gemfile / Gemfile.lock                                           →  bundler (Ruby)
- *.csproj / packages.config / Directory.Packages.props            →  NuGet (.NET)
- pom.xml / build.gradle / build.gradle.kts                        →  Maven/Gradle (Java/Kotlin)
```

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
6. **Statistics**: Count total dependencies, vulnerable, license-risky, stale; calculate health score

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

## Usage

```bash
# Full dependency audit (all dimensions)
/review-deps
/review-deps --scope all

# Vulnerabilities only
/review-deps --scope vulnerabilities

# License compliance only
/review-deps --scope licenses

# Staleness and upgrade planning only
/review-deps --scope staleness

# Filter by minimum severity
/review-deps --severity critical
/review-deps --severity high

# Combined options
/review-deps --scope vulnerabilities --severity critical
```

## Scope Options

- `all` (default): Run all three analysis dimensions — vulnerabilities, licenses, staleness
- `vulnerabilities`: Focus on CVEs, GHSAs, and known security advisories
- `licenses`: Focus on license identification, copyleft risk, and commercial compliance
- `staleness`: Focus on version drift, maintenance health, and upgrade complexity

## Severity Filter

When `--severity` is specified, only report findings at or above the given level:
- `critical`: Only critical findings
- `high`: Critical + high findings
- `medium`: Critical + high + medium findings (default)
- `low`: All findings including informational

## What This Skill Does

- Detects all package managers in the project
- Runs native audit tools for each ecosystem
- Queries GitHub Dependabot alerts when available
- Analyzes vulnerabilities with CVE severity and exploitability context
- Identifies license compliance risks for commercial and open-source projects
- Assesses dependency staleness and upgrade complexity
- Provides a prioritized upgrade plan with breaking change warnings
- Generates a comprehensive markdown report with health score

## What This Skill Does NOT Do

- Does not modify any code, lock files, or manifests
- Does not automatically upgrade dependencies
- Does not install missing audit tools (reports them as unavailable)
- Does not perform runtime/dynamic vulnerability testing
- Does not guarantee 100% vulnerability detection
- Does not provide legal advice on license compliance

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
