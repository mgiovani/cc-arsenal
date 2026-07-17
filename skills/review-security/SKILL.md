---
name: review-security
description: Perform an OWASP Top 10:2025-focused static security review of a PR, commit,
  or entire codebase, spawning parallel Explore agents to grep for vulnerable patterns
  (injection, broken access control, crypto failures, insecure deserialization, etc.)
  and producing a severity-ranked markdown report with file:line evidence. Use when a
  user wants to audit code security, scan for vulnerabilities, review security posture,
  or check OWASP compliance. Analysis only - never modifies code. For general code
  quality/error-handling review use review-code; for dependency/license/supply-chain
  auditing use review-deps.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: '[pr_number|commit_sha|--all] [--scope scope]'
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Task, TodoWrite, AskUserQuestion
context: fork
agent: general-purpose
---

# Security Review

Comprehensive static security analysis targeting OWASP Top 10:2025 vulnerabilities, common bytecode security issues, and language-specific security patterns. Analysis only - identifies vulnerabilities, explains findings, and suggests fix approaches without making code changes.

## Anti-Hallucination Guidelines

Security reviews must be based on actual code analysis and verified patterns, not guesses:
1. **Read before claiming** - never report a vulnerability in code that hasn't been read
2. **Evidence-based findings** - every finding references a specific file path and line number
3. **Pattern matching** - use Grep to find actual vulnerable patterns, not hypothetical ones
4. **No invented CVEs** - only reference real vulnerabilities when providing context
5. **Quantifiable results** - count actual instances, don't estimate
6. **No false positives** - verify each finding matches a documented vulnerability pattern
7. **Scope verification** - only scan files within the specified scope (PR/commit/all)

## Scan Workflow

### Phase 0: Determine Scan Scope

Parse arguments to determine what to scan:

- `<pr_number>`: scan only files changed in PR (e.g. "123", "#123")
- `<commit_sha>`: scan only files changed in commit (e.g. "abc123")
- `--all` or no args: scan entire codebase
- `--scope [web|api|mobile|backend|frontend]`: focus on specific vulnerability categories

If a PR or commit is specified, use Bash to get changed files:

```bash
# For PR
gh pr view <pr_number> --json files --jq '.files[].path'

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
```

### Phase 1: Project Technology Discovery

Use an Explore agent to understand the project's technology stack:

```
Use Task tool:
- subagent_type: "Explore"
- model: "haiku"
- prompt: "Discover the project's technology stack and security tooling:
    1. Read package.json, pyproject.toml, pom.xml, go.mod to identify languages/frameworks
    2. Check for existing security tools: .pre-commit-config.yaml, .github/workflows for SAST
    3. Identify web frameworks: React/Next.js, Django/Flask, Spring Boot, Express.js
    4. Check database usage: SQL, NoSQL, ORM patterns
    5. Look for authentication patterns: JWT, OAuth, session management
    6. Note any existing SECURITY.md or security policies
    Return: Technology stack summary with relevant vulnerability categories to prioritize."
```

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track scan progress across all OWASP categories (A01-A10), bytecode security, and report generation.

### Phase 3: Parallel Vulnerability Scanning

Spawn parallel Explore agents (model: haiku), each targeting specific OWASP categories with Grep patterns for actual vulnerable code. For detailed agent prompts and grep patterns, see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1**: Access Control & Authentication (A01, A07)
- **Agent 2**: Configuration & Design (A02, A06)
- **Agent 3**: Injection & Data Integrity (A05, A08)
- **Agent 4**: Cryptography & Supply Chain (A04, A03)
- **Agent 5**: Bytecode & Compiled Code Security
- **Agent 6**: Logging, Monitoring & Exception Handling (A09, A10)

Spawn only the agent(s) matching `--scope`; spawn all 6 only for `--all` or no scope given.

**Scope → agents:**
- `web` → Agent 2 (Config & Design) + Agent 3 (Injection & Data Integrity)
- `api` → Agent 1 (Access Control & Authentication) + Agent 2 (Config & Design)
- `mobile` → Agent 4 (Cryptography & Supply Chain) + Agent 3 (Injection & Data Integrity)
- `backend` → Agent 3 (Injection & Data Integrity) + Agent 2 (Config & Design)
- `frontend` → Agent 2 (Config & Design) + Agent 3 (Injection & Data Integrity)

Each agent must:
1. Grep for vulnerability patterns across files in scope
2. Read each match to verify context
3. Extract exact code snippets (5-10 lines)
4. Explain why the code is vulnerable
5. Classify severity (Critical/High/Medium/Low)
6. Provide fix recommendations (2-3 approaches)

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. **Collect all findings** from the 6 parallel agents
2. **Deduplicate** - remove duplicate findings across agents
3. **Prioritize by severity**:
   - **Critical**: RCE, SQLi, authentication bypass, hardcoded secrets
   - **High**: XSS, CSRF, broken access control, weak crypto
   - **Medium**: information disclosure, missing logging, insecure design
   - **Low**: code quality issues with minor security impact
4. **Categorize by OWASP Top 10:2025**: group findings under A01-A10 categories
5. **Statistics**: total vulnerabilities, counts by severity/category, files scanned vs. files with issues

### Phase 5: Generate Security Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

### Phase 6: Verification & Quality Check

Before presenting the report, verify:
1. Every finding has a file path and line numbers
2. Every finding has an actual code snippet (not a placeholder)
3. Every finding has a clear explanation of the vulnerability
4. Every finding has 2-3 fix approaches with examples
5. Statistics are accurate (counted, not estimated)
6. No duplicate findings
7. Severity ratings are justified
8. Only scanned files within the specified scope
9. No invented vulnerabilities or false positives
10. References to CWEs/CVEs are accurate

## Usage

```bash
# Scan specific PR
review-security 123
review-security #456

# Scan specific commit
review-security abc123def

# Scan entire codebase
review-security --all
review-security

# Focus on specific scope
review-security --all --scope web
review-security 123 --scope api
```

## Scope Options

- `web`: focus on XSS, CSRF, CORS, injection (A02, A05)
- `api`: focus on authentication, authorization, rate limiting (A01, A07, A06)
- `mobile`: focus on insecure storage, crypto, data leakage (A04, A08)
- `backend`: focus on injection, deserialization, business logic (A05, A06, A08)
- `frontend`: focus on XSS, CSP, SRI, client-side security (A02, A05, A08)

If no scope is specified, perform a comprehensive scan across all categories.

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md) - Detailed grep patterns and agent prompts for each OWASP category
- [references/report-template.md](references/report-template.md) - Full markdown report template with all sections

## What This Skill Does NOT Do

- Does not modify any code, automatically fix vulnerabilities, or commit changes
- Does not run dynamic security testing (DAST) or penetration testing
- Does not guarantee 100% vulnerability detection (static, pattern-based analysis)

## OWASP References

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)
