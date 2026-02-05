---
name: review-security
description: "Perform comprehensive security review targeting OWASP Top 10 2025 vulnerabilities for PRs, commits, or entire codebases. This skill should be used when a user wants to audit code security, scan for vulnerabilities, review security posture, or check for OWASP compliance. Analysis only - identifies vulnerabilities without modifying code."
disable-model-invocation: true
argument-hint: "[pr_number|commit_sha|--all] [--scope scope]"
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Task, TodoWrite, AskUserQuestion
context: fork
agent: general-purpose
---

# Security Review

Comprehensive security analysis targeting OWASP Top 10 2025 vulnerabilities, common bytecode security issues, and language-specific security patterns. This skill performs **analysis only** - it identifies vulnerabilities, explains findings, and suggests fix approaches without making code changes.

## Anti-Hallucination Guidelines

**CRITICAL**: Security reviews must be based on ACTUAL code analysis and VERIFIED patterns:
1. **Read before claiming** - Never report vulnerabilities in code that has not been read
2. **Evidence-based findings** - Every finding must reference specific file paths and line numbers
3. **Pattern matching** - Use Grep to find actual vulnerable patterns, not hypothetical ones
4. **No invented CVEs** - Only reference real vulnerabilities when providing context
5. **Quantifiable results** - Count actual instances, do not estimate
6. **No false positives** - Verify each finding matches documented vulnerability patterns
7. **Scope verification** - Only scan files within specified scope (PR/commit/all)

## Scan Workflow

### Phase 0: Determine Scan Scope

Parse arguments to determine what to scan:

```
Arguments:
- <pr_number>: Scan only files changed in PR (e.g., "123", "#123")
- <commit_sha>: Scan only files changed in commit (e.g., "abc123")
- "--all" or no args: Scan entire codebase
- "--scope [web|api|mobile|backend|frontend]": Focus on specific vulnerability categories
```

If PR or commit specified, use Bash to get changed files:
```bash
# For PR
gh pr view <pr_number> --json files --jq '.files[].path'

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
```

### Phase 1: Project Technology Discovery

Use an Explore agent to understand the project technology stack:

```
Use Task tool with Explore agent:
- prompt: "Discover the project's technology stack and security tooling:
    1. Read package.json, pyproject.toml, pom.xml, go.mod to identify languages/frameworks
    2. Check for existing security tools: .pre-commit-config.yaml, .github/workflows for SAST
    3. Identify web frameworks: React/Next.js, Django/Flask, Spring Boot, Express.js
    4. Check database usage: SQL, NoSQL, ORM patterns
    5. Look for authentication patterns: JWT, OAuth, session management
    6. Note any existing SECURITY.md or security policies
    Return: Technology stack summary with relevant vulnerability categories to prioritize."
- subagent_type: "Explore"
```

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track comprehensive scan progress across all OWASP categories (A01-A10), bytecode security, and report generation.

### Phase 3: Parallel Vulnerability Scanning

Spawn parallel Explore agents for comprehensive security analysis. Each agent targets specific OWASP categories using Grep patterns to find actual vulnerable code.

For detailed agent prompts and grep patterns for each vulnerability category, see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1**: Access Control & Authentication (A01, A07)
- **Agent 2**: Configuration & Design (A02, A06)
- **Agent 3**: Injection & Data Integrity (A05, A08)
- **Agent 4**: Cryptography & Supply Chain (A04, A03)
- **Agent 5**: Bytecode & Compiled Code Security
- **Agent 6**: Logging, Monitoring & Exception Handling (A09, A10)

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
2. **Deduplicate** - Remove duplicate findings across agents
3. **Prioritize by severity**:
   - **Critical**: RCE, SQLi, Authentication bypass, Hardcoded secrets
   - **High**: XSS, CSRF, Broken access control, Weak crypto
   - **Medium**: Information disclosure, Missing logging, Insecure design
   - **Low**: Code quality issues with minor security impact
4. **Categorize by OWASP Top 10 2025**: Group findings under A01-A10 categories
5. **Statistics**: Count total vulnerabilities, by severity, by category, files scanned vs files with issues

### Phase 5: Generate Security Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

### Phase 6: Verification & Quality Check

Before presenting report, verify:
1. Every finding has file path and line numbers
2. Every finding has actual code snippet (not placeholder)
3. Every finding has clear explanation of vulnerability
4. Every finding has 2-3 fix approaches with examples
5. Statistics are accurate (counted, not estimated)
6. No duplicate findings
7. Severity ratings are justified
8. Only scanned files within specified scope
9. No invented vulnerabilities or false positives
10. References to CWEs/CVEs are accurate

## Usage

```bash
# Scan specific PR
/review-security 123
/review-security #456

# Scan specific commit
/review-security abc123def

# Scan entire codebase
/review-security --all
/review-security

# Focus on specific scope
/review-security --all --scope web
/review-security 123 --scope api
```

## Scope Options

- `web`: Focus on XSS, CSRF, CORS, injection (A02, A05)
- `api`: Focus on authentication, authorization, rate limiting (A01, A07, A06)
- `mobile`: Focus on insecure storage, crypto, data leakage (A04, A08)
- `backend`: Focus on injection, deserialization, business logic (A05, A06, A08)
- `frontend`: Focus on XSS, CSP, SRI, client-side security (A02, A05, A08)

If no scope specified, perform comprehensive scan across all categories.

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md) - Detailed grep patterns and agent prompts for each OWASP category
- [references/report-template.md](references/report-template.md) - Full markdown report template with all sections

## What This Skill Does

- Identifies security vulnerabilities based on OWASP Top 10 2025
- Analyzes bytecode and compiled code security
- Provides detailed explanations of each finding
- Suggests multiple fix approaches with code examples
- Generates comprehensive markdown report
- Prioritizes findings by severity

## What This Skill Does NOT Do

- Does not modify any code
- Does not automatically fix vulnerabilities
- Does not commit changes
- Does not run dynamic security testing (DAST)
- Does not perform penetration testing
- Does not guarantee 100% vulnerability detection

## Limitations

- **Static analysis only**: Cannot detect runtime-only vulnerabilities
- **Pattern-based**: May miss context-specific security issues
- **No dynamic testing**: Cannot test actual exploitability
- **False positives possible**: Some findings may not be exploitable in context
- **Requires manual review**: Expert review recommended for critical systems

## OWASP References

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)
