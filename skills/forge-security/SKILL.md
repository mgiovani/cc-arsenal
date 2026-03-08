---
name: forge-security
description: OWASP Top 10 security audit identifying authentication, injection, and data exposure risks.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[--all|path/to/file_or_dir]'
allowed-tools: Read, Write, Edit, Bash(git *), Bash(npm audit*), Bash(pip-audit*),
  Bash(safety *), Bash(bandit *), Grep, Glob, Task, TaskCreate, TaskUpdate, WebSearch
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify security audit is complete before stopping:\n\n1. Check that\
        \ docs/security-report.md exists and is non-empty\n2. Verify the report contains:\n\
        \   - Overall Risk rating (CRITICAL / HIGH / MEDIUM / LOW / CLEAN)\n   - All\
        \ 10 OWASP categories checked (A01 through A10) \u2014 each must appear\n\
        \   - Executive Summary\n   - Remediation Priority section\n3. CRITICAL GATE:\
        \ If Overall Risk is CRITICAL or HIGH:\n   - Verify findings are listed with\
        \ specific file paths and line numbers\n   - Verify remediation steps are\
        \ concrete and actionable\n   - Return decision: block \u2014 the code has\
        \ critical/high security issues that MUST be resolved\n4. If Overall Risk\
        \ is MEDIUM / LOW / CLEAN: allow stopping\n\nBlock if: report is incomplete,\
        \ OWASP categories are missing, or CRITICAL/HIGH findings exist without remediation\
        \ steps.\n"
      timeout: 90
---

# Forge Security

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Security Audit

OWASP Top 10 2021 focused security audit for SaaS applications. This skill is **security-centric** — it evaluates code for vulnerabilities, misconfigurations, and security anti-patterns, independent of functional correctness or code style.

This skill performs **analysis only** — it identifies vulnerabilities, explains their impact, and recommends remediation without modifying code.

**BLOCKING RULE**: If any CRITICAL or HIGH severity findings are identified, the implementation is not complete and must not be approved until these are resolved.

## Anti-Hallucination Guidelines

**CRITICAL**: Security findings must be grounded in actual code evidence:
1. **Read before reporting** — Never report a vulnerability in code you have not read
2. **Exact references** — Every finding must include `file:line` and a code excerpt
3. **No invented CVEs** — Only reference real vulnerabilities when citing external context
4. **Verify patterns** — Confirm the vulnerable pattern actually exists in context before reporting
5. **No theoretical risks** — Report actual code patterns, not "could be vulnerable if..."
6. **False positives harm trust** — When uncertain, note the uncertainty rather than report as confirmed
7. **Scope discipline** — Only audit files within the specified scope

## Role

You are a **Security Auditor** with expertise in application security and OWASP methodology. Your goal is to find real security vulnerabilities before they reach production, with emphasis on the risks most common in SaaS applications.

## OWASP Top 10 2021 Checklist

### A01: Broken Access Control

**What to look for:**
- Missing authorization checks before data access or modification
- Direct object references without ownership verification (IDOR)
- Privilege escalation paths (regular user accessing admin functions)
- CORS configured to allow all origins (`*`) on sensitive endpoints
- JWT or session tokens not validated on the server side
- Mass assignment vulnerabilities (accepting all request body fields)

**Common code patterns to check:**
- Database queries that use user-supplied IDs without checking ownership
- Admin endpoints missing role/permission guards
- File download endpoints that accept arbitrary paths

### A02: Cryptographic Failures

**What to look for:**
- Sensitive data (passwords, tokens, PII) stored or transmitted unencrypted
- Weak hashing algorithms: MD5, SHA-1 for passwords (use bcrypt/argon2/scrypt)
- Hardcoded cryptographic keys or initialization vectors
- HTTP used instead of HTTPS for sensitive operations
- Encryption keys stored in source code or version control
- Predictable random number generation for security-sensitive values

**Common code patterns to check:**
- Password storage without proper hashing
- Secret keys defined as string constants
- HTTP URLs for API calls involving credentials

### A03: Injection

**What to look for:**
- SQL injection: string concatenation in queries instead of parameterized queries
- NoSQL injection: user input passed directly into MongoDB/similar query objects
- Command injection: user input passed to shell execution functions
- LDAP injection: user input in LDAP filter strings
- Template injection: user input rendered in server-side template engines
- XPath injection: user input in XPath expressions

**Common code patterns to check:**
- `query("SELECT ... WHERE id = " + userId)`
- `exec(command + userInput)`
- Template rendering with unsanitized user input

### A04: Insecure Design

**What to look for:**
- Missing rate limiting on authentication, registration, or resource-intensive endpoints
- No account lockout after repeated failed login attempts
- Business logic flaws: negative quantities, price tampering opportunities
- Lack of multi-factor authentication on sensitive operations
- Insecure password reset flows (predictable tokens, no expiry, no single-use)
- Unvalidated redirects and forwards

### A05: Security Misconfiguration

**What to look for:**
- Default credentials or sample accounts left enabled
- Verbose error messages exposing stack traces or system information to end users
- Debug mode or development settings enabled in production configuration
- Unnecessary features enabled (unused ports, services, pages)
- Missing security headers: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`
- Directory listing enabled
- Overly permissive file permissions

### A06: Vulnerable & Outdated Components

**What to look for:**
- Dependencies with known CVEs (check `package.json`, `requirements.txt`, `Gemfile.lock`)
- Very old versions of critical dependencies (authentication libraries, crypto libraries)
- Packages that have been deprecated or abandoned
- Pinned versions that haven't been reviewed recently
- Direct use of `eval()` or `exec()` with external input

### A07: Identification & Authentication Failures

**What to look for:**
- Weak password policy enforcement (minimum length, complexity)
- Missing brute-force protection on login endpoints
- Session tokens not invalidated on logout
- Session fixation vulnerabilities
- Insecure "remember me" implementations
- Token leakage in URLs, logs, or referrer headers
- JWT: algorithm set to `none`, weak secret, no expiry validation

### A08: Software & Data Integrity Failures

**What to look for:**
- Deserialization of untrusted data without validation
- Auto-update mechanisms without signature verification
- CI/CD pipeline steps that pull from external sources without pinned versions
- Subresource integrity (SRI) missing for CDN-hosted scripts
- Webhooks processed without signature verification
- Object deserialization from user-controlled input

### A09: Security Logging & Monitoring Failures

**What to look for:**
- Authentication events (login, logout, failed attempts) not logged
- Authorization failures not logged
- High-value transaction events not logged
- Logs containing sensitive data (passwords, full credit card numbers, PII)
- No structured logging format that supports alerting
- Log data stored only locally without centralized collection

### A10: Server-Side Request Forgery (SSRF)

**What to look for:**
- HTTP requests made to URLs derived from user input
- Webhooks or integrations that fetch remote resources based on user-specified URLs
- File import features that accept URLs
- Image/media upload features that accept remote URLs
- DNS rebinding vulnerabilities in URL validation
- Missing allowlist validation for external request targets

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Audit Scope

$ARGUMENTS

If no argument provided, audit the entire project (current directory).
If a path is provided, audit only that file or directory.

## CRITICAL BLOCKING RULE

**If ANY CRITICAL or HIGH severity finding is open, the audit CANNOT be marked complete.**

The Stop hook will block completion until either:
- The findings are resolved (re-run audit to verify fix), OR
- The user explicitly acknowledges and accepts the risk (use AskUserQuestion)

This is intentional — security audits must drive remediation, not just documentation.

## Progress Tracking

Use TaskCreate to track audit phases:

```
TaskCreate: "Identify tech stack and entry points" → scope analysis
TaskCreate: "OWASP A01-A05 review" → access control, crypto, injection, design, config
TaskCreate: "OWASP A06-A10 review" → deps, auth, integrity, logging, SSRF
TaskCreate: "Dependency vulnerability scan" → run npm audit / pip-audit
TaskCreate: "Write security report" → produce docs/security-report.md
```

## Automated Scanning

Run automated tools alongside manual review:

```bash
# Node.js projects
npm audit --json 2>/dev/null

# Python projects
pip-audit 2>/dev/null || safety check 2>/dev/null
bandit -r . -f json 2>/dev/null
```

Include automated scan results in the report.

## Parallel OWASP Review

For thorough coverage, spawn parallel audit agents:

```
Task Agent 1: A01 (Access Control) + A02 (Crypto) + A03 (Injection)
  - Check auth middleware, password hashing, SQL query construction

Task Agent 2: A04 (Design) + A05 (Config) + A06 (Components)
  - Check threat modeling, env vars exposure, dependency versions

Task Agent 3: A07 (Auth Failures) + A08 (Integrity) + A09 (Logging) + A10 (SSRF)
  - Check session management, CSP, audit logs, URL validation

Merge findings into docs/security-report.md
```

## Secrets Detection

Always search for hardcoded secrets:

```
Grep: pattern="(api_key|secret|password|token)\s*=\s*['\"][^'\"]{8,}"
Grep: pattern="sk-[a-zA-Z0-9]{20,}"
Grep: pattern="AKIA[0-9A-Z]{16}"
```

Report any hardcoded credentials as CRITICAL severity.

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- `docs/security-report.md` exists with all OWASP categories
- No CRITICAL or HIGH findings left unaddressed
- Overall Risk rating is set

**Blocked example (CRITICAL found):**
```
⚠️ SECURITY AUDIT BLOCKED:
Overall Risk: CRITICAL

Critical findings must be resolved before marking audit complete:
- A03 Injection: SQL injection at src/api/users.ts:47 (CRITICAL)
- A02 Crypto: Plaintext passwords stored at src/auth/handler.py:23 (CRITICAL)

Fix these issues and re-run /forge-security to verify.
```

**Blocked example (incomplete):**
```
⚠️ Security report incomplete:
- Missing OWASP categories: A04, A05, A09
Cannot complete until all 10 OWASP categories are checked.
```
