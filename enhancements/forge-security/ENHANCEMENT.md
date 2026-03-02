---
# Enhancement for: forge-security
disable-model-invocation: false
argument-hint: "[--all|path/to/file_or_dir]"
allowed-tools: "Read, Write, Edit, Bash(git *), Bash(npm audit*), Bash(pip-audit*), Bash(safety *), Bash(bandit *), Grep, Glob, Task, TaskCreate, TaskUpdate, WebSearch"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify security audit is complete before stopping:

        1. Check that docs/security-report.md exists and is non-empty
        2. Verify the report contains:
           - Overall Risk rating (CRITICAL / HIGH / MEDIUM / LOW / CLEAN)
           - All 10 OWASP categories checked (A01 through A10) — each must appear
           - Executive Summary
           - Remediation Priority section
        3. CRITICAL GATE: If Overall Risk is CRITICAL or HIGH:
           - Verify findings are listed with specific file paths and line numbers
           - Verify remediation steps are concrete and actionable
           - Return decision: block — the code has critical/high security issues that MUST be resolved
        4. If Overall Risk is MEDIUM / LOW / CLEAN: allow stopping

        Block if: report is incomplete, OWASP categories are missing, or CRITICAL/HIGH findings exist without remediation steps.
      timeout: 90
---

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
