---
description: "Security review for PRs, commits, or entire codebase"
argument-hint: "[pr_number|commit_sha|--all] [--scope scope]"
allowed-tools: ["Read", "Grep", "Glob", "Bash(git *)", "Bash(gh *)", "Task", "TodoWrite", "AskUserQuestion"]
---

# Security Review Command

Comprehensive security analysis targeting OWASP Top 10 2025 vulnerabilities, common bytecode security issues, and language-specific security patterns. This command performs **analysis only** - it identifies vulnerabilities, explains findings, and suggests fix approaches without making code changes.

## Anti-Hallucination Guidelines

**CRITICAL**: Security reviews must be based on ACTUAL code analysis and VERIFIED patterns:
1. **Read before claiming** - Never report vulnerabilities in code you haven't read
2. **Evidence-based findings** - Every finding must reference specific file paths and line numbers
3. **Pattern matching** - Use Grep to find actual vulnerable patterns, not hypothetical ones
4. **No invented CVEs** - Only reference real vulnerabilities when providing context
5. **Quantifiable results** - Count actual instances, don't estimate
6. **No false positives** - Verify each finding matches documented vulnerability patterns
7. **Scope verification** - Only scan files within specified scope (PR/commit/all)

## Your Task

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

### Phase 1: Project Technology Discovery (Use Explore Agent)

**IMPORTANT**: Before scanning, understand the project's technology stack to target relevant vulnerabilities.

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

Use TodoWrite to track comprehensive scan progress:

```
TodoWrite:
## OWASP Top 10 2025 Vulnerabilities
- [ ] A01: Broken Access Control
- [ ] A02: Security Misconfiguration
- [ ] A03: Software Supply Chain Failures
- [ ] A04: Cryptographic Failures
- [ ] A05: Injection Vulnerabilities
- [ ] A06: Insecure Design
- [ ] A07: Authentication Failures
- [ ] A08: Data Integrity Failures
- [ ] A09: Logging/Monitoring Failures
- [ ] A10: Exception Handling Issues

## Bytecode Security Analysis
- [ ] Python bytecode (.pyc) security
- [ ] JavaScript compilation security
- [ ] Dependency vulnerabilities

## Report Generation
- [ ] Compile findings
- [ ] Generate fix recommendations
- [ ] Create severity summary
```

### Phase 3: Parallel Vulnerability Scanning (Use SubAgents)

Spawn parallel agents for comprehensive security analysis across different vulnerability categories:

#### Agent 1 - Access Control & Authentication (A01, A07)

```
Agent 1 - Access Control & Authentication Analysis:
- prompt: "Scan for OWASP A01 (Broken Access Control) and A07 (Authentication Failures) in [FILES_LIST]:

**A01 - Broken Access Control Patterns:**
Use Grep to search for:
- Direct object references: userId=, accountId=, ?id=
- Missing authorization: @GetMapping, @PostMapping, app.get, app.post without role checks
- JWT manipulation: jwt.decode with verify=False, verify: false
- Parameter tampering: request.getParameter, req.query, req.params
- Hardcoded admin paths: /admin/, /administrator/, /console/

**A07 - Authentication Failures Patterns:**
Use Grep to search for:
- Weak password policies: minLength < 8, no complexity requirements
- Insecure session cookies: httpOnly: false, secure: false, sameSite: 'none'
- Plain password storage: password == user.password, no hashing
- Session IDs in URLs: ?session=, ?token= in redirect/links
- Missing MFA: login functions without totp/2fa checks

For each finding:
1. Read the file to verify context
2. Extract exact code snippet (5-10 lines)
3. Explain why it's vulnerable
4. Provide CVE references if applicable (e.g., similar to CWE-639, CWE-287)

Return structured findings with:
- File path and line numbers
- Vulnerability type (A01 or A07)
- Severity (Critical/High/Medium/Low)
- Code snippet
- Explanation
- Fix recommendations (2-3 approaches)"
- subagent_type: "Explore"
```

#### Agent 2 - Configuration & Design (A02, A06)

```
Agent 2 - Security Misconfiguration & Insecure Design:
- prompt: "Scan for OWASP A02 (Security Misconfiguration) and A06 (Insecure Design) in [FILES_LIST]:

**A02 - Security Misconfiguration Patterns:**
Use Grep to search for:
- CORS misconfig: Access-Control-Allow-Origin: *, credentials: true with wildcard
- CSRF missing: @PostMapping without @CsrfToken, app.post without csrf
- Debug mode: DEBUG = True, APP_ENV = development in production files
- Default credentials: password = 'admin', username/password defaults
- Exposed secrets: hardcoded API keys, database passwords in code
- Missing security headers: No CSP, HSTS, X-Frame-Options

**A06 - Insecure Design Patterns:**
Use Grep to search for:
- No rate limiting: login, register, reset-password without limiter
- Missing step-up auth: transfer, delete, change-email without MFA
- Predictable tokens: Date.now(), timestamp, md5(user)
- Business logic flaws: negative quantities, discount > 100%

For each finding:
1. Read configuration files and environment variables
2. Verify the vulnerability in context
3. Check if it's a default or intentional setting

Return structured findings with remediation priority and multiple fix approaches."
- subagent_type: "Explore"
```

#### Agent 3 - Injection & Data Integrity (A05, A08)

```
Agent 3 - Injection & Data Integrity Analysis:
- prompt: "Scan for OWASP A05 (Injection) and A08 (Data Integrity Failures) in [FILES_LIST]:

**A05 - Injection Patterns:**
Use Grep to search for:

*SQL Injection:*
- execute('SELECT.*\\+', 'SELECT.*\\.format', 'SELECT.*%s', 'SELECT.*f\"'
- createQuery.*\\+, Statement.*executeQuery.*\\+
- User input in queries: request., req., params., body.

*NoSQL Injection:*
- db.collection.*find\\(req., {\\$where:, {\\$regex:
- Model.find.*req.query, req.body, req.params

*Command Injection:*
- exec\\(.*req., system\\(.*\\$_GET, shell_exec.*input
- Runtime.getRuntime\\(\\).exec\\(.*request
- subprocess.*shell=True.*user.*input

*XSS (Cross-Site Scripting):*
- innerHTML.*=.*req., .html\\(.*user, document.write\\(.*untrusted
- dangerouslySetInnerHTML.*user
- render_template_string\\(.*request

*LDAP/Template Injection:*
- LdapName\\(.*request, eval\\(.*req., Function\\(.*user

**A08 - Data Integrity Failures:**
Use Grep to search for:
- Insecure deserialization: pickle.loads, yaml.load (without Loader=), unserialize
- Missing integrity checks: <script src= without integrity=
- Unsigned updates: auto.*update without signature/checksum

For each pattern:
1. Grep for the pattern across all files in scope
2. Read each match to verify it's user-controllable input
3. Trace data flow if unclear
4. Classify severity based on exploitability

Return findings with:
- Attack vector explanation
- Example exploit payload
- Multiple remediation approaches (parameterized queries, input validation, escaping)"
- subagent_type: "Explore"
```

#### Agent 4 - Cryptography & Supply Chain (A04, A03)

```
Agent 4 - Cryptographic & Supply Chain Analysis:
- prompt: "Scan for OWASP A04 (Cryptographic Failures) and A03 (Software Supply Chain) in [FILES_LIST]:

**A04 - Cryptographic Failures:**
Use Grep to search for:

*Weak algorithms:*
- MD5, SHA1, SHA-1, DES, 3DES, RC4, Blowfish
- ECB.*mode, RSA.*512, RSA.*1024

*Weak random number generation:*
- Math.random\\(\\).*token|password|secret
- rand\\(\\).*(?!random_bytes)
- new Random\\(\\) (should be SecureRandom)

*Hardcoded secrets:*
- password\\s*=\\s*['\"][^'\"]+['\"]
- api_key\\s*=\\s*['\"], secret.*=.*['\"][A-Za-z0-9+/=]{20,}
- AWS_ACCESS_KEY, PRIVATE_KEY, DATABASE_URL in code

*Insecure TLS:*
- SSLv2, SSLv3, TLSv1.0, TLSv1.1
- ssl_verify.*False, verify:\\s*false, CERT_NONE

*Missing encryption:*
- http:// (non-localhost), ftp://, telnet://

**A03 - Software Supply Chain:**
Use Read to check:
- package.json: Outdated dependencies (lodash < 4.17, axios < 0.21)
- requirements.txt: Django < 3.2, Flask < 2.0
- pom.xml: Old versions, http:// repositories
- Missing SRI: <script src=CDN without integrity=
- Lock files: package-lock.json, Pipfile.lock, go.sum presence
- .github/workflows: pip install --trusted-host, npm config set strict-ssl false

For each finding:
1. Verify the vulnerability with Read
2. Check CVE databases for known vulnerabilities (mention CVE if applicable)
3. Assess data sensitivity (what could be exposed?)

Return findings with:
- Cryptographic best practices for replacement
- Dependency update recommendations with versions
- SRI hash generation instructions"
- subagent_type: "Explore"
```

#### Agent 5 - Bytecode & Compiled Code Security

```
Agent 5 - Bytecode Security Analysis:
- prompt: "Scan for bytecode and compiled code vulnerabilities in [FILES_LIST]:

**Python Bytecode Security:**
Use Glob and Read to check:
- Find all .pyc files: '**/*.pyc'
- Check for obfuscated bytecode (unusual patterns)
- Look for Pyarmor or other obfuscators
- Verify .pyc files have corresponding .py source

**JavaScript/TypeScript Compilation:**
Use Grep to search for:
- React Server Components deserialization patterns
- Angular DOM sanitization bypass: <svg><animate href=\"javascript:
- TypeScript type bypasses: any types in security-critical code
- Unsafe eval or Function constructor usage

**Java Bytecode (if applicable):**
Use Grep to search for:
- Deserialization: ObjectInputStream, readObject
- Bytecode verification disabled: -Xverify:none
- Unsafe reflection: Class.forName with user input

For each finding:
1. Explain the bytecode-level risk
2. Reference recent CVEs if applicable (e.g., CVE-2025-55182 for React)
3. Suggest static analysis tools (Pycdc, SpotBugs, etc.)

Return findings focusing on detection evasion risks and compilation-level vulnerabilities."
- subagent_type: "Explore"
```

#### Agent 6 - Logging, Monitoring & Exception Handling (A09, A10)

```
Agent 6 - Logging & Exception Handling Analysis:
- prompt: "Scan for OWASP A09 (Logging/Monitoring Failures) and A10 (Exception Handling) in [FILES_LIST]:

**A09 - Logging/Monitoring Failures:**
Use Grep to search for:
- Missing logging: login, transfer, delete, admin.*action without log/audit
- Sensitive data in logs: log.*password, log.*token, log.*secret, print.*api_key
- No alerting: failed.*login, error.* without alert/notify mechanisms

**A10 - Exception Handling Issues:**
Use Grep to search for:
- Generic exception catching: except:, except Exception:, catch \\(Exception
- Empty catch blocks: catch.*\\{\\s*\\}, except.*pass
- Stack trace exposure: printStackTrace, print.*exc_info, return.*error.*stack
- Unchecked nulls: .get\\(.*\\) without null checks, undefined access

For each pattern:
1. Read the code to assess security impact
2. Determine if errors could leak sensitive information
3. Check if exceptions could bypass security controls

Return findings with:
- Specific logging additions needed
- Exception handling best practices
- Monitoring/alerting recommendations"
- subagent_type: "Explore"
```

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. **Collect all findings** from the 6 parallel agents
2. **Deduplicate** - Remove duplicate findings across agents
3. **Prioritize by severity**:
   - **Critical**: RCE, SQLi, Authentication bypass, Hardcoded secrets
   - **High**: XSS, CSRF, Broken access control, Weak crypto
   - **Medium**: Information disclosure, Missing logging, Insecure design
   - **Low**: Code quality issues with minor security impact

4. **Categorize by OWASP Top 10 2025**:
   - Group findings under A01-A10 categories
   - Add bytecode-specific findings as separate category

5. **Statistics**:
   - Count total vulnerabilities found
   - Count by severity (Critical/High/Medium/Low)
   - Count by OWASP category
   - Files scanned vs files with issues

### Phase 5: Generate Security Report

Create comprehensive markdown report with:

```markdown
# Security Review Report

**Scope**: [PR #123 | Commit abc123 | Entire Codebase]
**Date**: [YYYY-MM-DD]
**Files Scanned**: [N files]
**Total Findings**: [N vulnerabilities]

## Executive Summary

[2-3 sentence overview of security posture and critical issues]

## Severity Breakdown

- 🔴 **Critical**: N findings
- 🟠 **High**: N findings
- 🟡 **Medium**: N findings
- 🟢 **Low**: N findings

## Findings by OWASP Category

### A01: Broken Access Control (N findings)

#### Finding 1: [Vulnerability Title]
- **Severity**: Critical
- **File**: `path/to/file.py:123-130`
- **Description**: [What is vulnerable and why]
- **Code Snippet**:
  ```python
  [Actual vulnerable code]
  ```
- **Explanation**: [Why this is exploitable, reference CWE if applicable]
- **Attack Scenario**: [How an attacker could exploit this]
- **Recommended Fixes**:
  1. **Approach 1**: [Description with code example]
  2. **Approach 2**: [Alternative approach with code example]
  3. **Approach 3**: [Another alternative if applicable]

[Repeat for each finding...]

### A02: Security Misconfiguration (N findings)
[...]

### A03: Software Supply Chain Failures (N findings)
[...]

### A04: Cryptographic Failures (N findings)
[...]

### A05: Injection Vulnerabilities (N findings)
[...]

### A06: Insecure Design (N findings)
[...]

### A07: Authentication Failures (N findings)
[...]

### A08: Data Integrity Failures (N findings)
[...]

### A09: Logging/Monitoring Failures (N findings)
[...]

### A10: Exception Handling Issues (N findings)
[...]

## Bytecode Security Analysis

### Python Bytecode Findings (if applicable)
[...]

### JavaScript/TypeScript Compilation Findings (if applicable)
[...]

### Java Bytecode Findings (if applicable)
[...]

## Recommendations by Priority

### Immediate Action Required (Critical/High)
1. [Finding reference] - [Brief action item]
2. [...]

### Short-term Improvements (Medium)
1. [Finding reference] - [Brief action item]
2. [...]

### Long-term Enhancements (Low)
1. [Finding reference] - [Brief action item]
2. [...]

## Security Tooling Recommendations

Based on this analysis, consider adding:

- **SAST**: [Tool recommendations based on tech stack]
- **Dependency Scanning**: [Tool recommendations]
- **Secret Detection**: [Tool recommendations]
- **Pre-commit Hooks**: [Specific hooks to add]
- **CI/CD Security**: [Pipeline improvements]

## References

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [CWE Database](https://cwe.mitre.org/)
- [Relevant CVEs mentioned in findings]

---

**Next Steps**: Review findings, prioritize fixes, and implement recommended security controls.
```

### Phase 6: Verification & Quality Check

Before presenting report, verify:

```
Quality Checklist:
1. ✅ Every finding has file path and line numbers
2. ✅ Every finding has actual code snippet (not placeholder)
3. ✅ Every finding has clear explanation of vulnerability
4. ✅ Every finding has 2-3 fix approaches with examples
5. ✅ Statistics are accurate (counted, not estimated)
6. ✅ No duplicate findings
7. ✅ Severity ratings are justified
8. ✅ Only scanned files within specified scope
9. ✅ No invented vulnerabilities or false positives
10. ✅ References to CWEs/CVEs are accurate
```

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

If no scope specified, performs comprehensive scan across all categories.

## Important Notes

### What This Command Does
- ✅ Identifies security vulnerabilities based on OWASP Top 10 2025
- ✅ Analyzes bytecode and compiled code security
- ✅ Provides detailed explanations of each finding
- ✅ Suggests multiple fix approaches with code examples
- ✅ Generates comprehensive markdown report
- ✅ Prioritizes findings by severity

### What This Command Does NOT Do
- ❌ Does not modify any code
- ❌ Does not automatically fix vulnerabilities
- ❌ Does not commit changes
- ❌ Does not run dynamic security testing (DAST)
- ❌ Does not perform penetration testing
- ❌ Does not guarantee 100% vulnerability detection

### Limitations
- **Static analysis only**: Cannot detect runtime-only vulnerabilities
- **Pattern-based**: May miss context-specific security issues
- **No dynamic testing**: Cannot test actual exploitability
- **False positives possible**: Some findings may not be exploitable in context
- **Requires manual review**: Expert review recommended for critical systems

### Recommended Follow-up
1. **Manual review**: Security expert should review all Critical/High findings
2. **Dynamic testing**: Use DAST tools (OWASP ZAP, Burp Suite) for runtime testing
3. **Penetration testing**: Professional pentest for production systems
4. **Security tools**: Integrate SAST/SCA tools into CI/CD pipeline
5. **Training**: Educate developers on secure coding practices

## Security Review Best Practices

### For Developers
1. **Run before PR**: Check your code before creating pull requests
2. **Fix Critical/High first**: Prioritize based on severity
3. **Understand, don't copy-paste**: Learn why the vulnerability exists
4. **Test fixes**: Verify fixes don't break functionality
5. **Add tests**: Write security tests to prevent regressions

### For Security Teams
1. **Validate findings**: Verify each finding is a real vulnerability
2. **Assess risk**: Consider exploitability in your specific context
3. **Prioritize**: Not all findings need immediate fixes
4. **Track metrics**: Monitor security trends over time
5. **Provide training**: Use findings as teaching opportunities

### For DevOps/SRE
1. **Automate**: Integrate security scanning into CI/CD
2. **Gate deployments**: Block deployments with Critical vulnerabilities
3. **Monitor**: Set up alerts for new vulnerabilities
4. **Rotate secrets**: Immediately rotate any exposed credentials
5. **Incident response**: Have a plan for security incidents

## Example Output

```
🔍 Security Review Report

**Scope**: PR #123 (5 files changed)
**Files Scanned**: 5 files
**Total Findings**: 12 vulnerabilities

Severity Breakdown:
- 🔴 Critical: 2 findings
- 🟠 High: 4 findings
- 🟡 Medium: 5 findings
- 🟢 Low: 1 finding

Top Critical Finding:
📍 SQL Injection in user_service.py:45
   Raw SQL query with unsanitized user input

[Full detailed report follows...]
```

---

**OWASP References**:
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)

**Tool Recommendations**:
- **Python**: Bandit, Safety, pip-audit, Semgrep
- **JavaScript**: ESLint Security, npm audit, Snyk
- **Java**: SpotBugs + FindSecBugs, OWASP Dependency-Check
- **Multi-language**: SonarQube, Semgrep, CodeQL
