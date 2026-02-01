# Security Review - Agent Prompts & OWASP Patterns

Detailed grep patterns and agent prompts for each OWASP vulnerability category. Load this reference when running Phase 3 parallel vulnerability scanning.

## Agent 1 - Access Control & Authentication (A01, A07)

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

## Agent 2 - Configuration & Design (A02, A06)

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

## Agent 3 - Injection & Data Integrity (A05, A08)

```
Agent 3 - Injection & Data Integrity Analysis:
- prompt: "Scan for OWASP A05 (Injection) and A08 (Data Integrity Failures) in [FILES_LIST]:

**A05 - Injection Patterns:**
Use Grep to search for:

*SQL Injection:*
- execute('SELECT.*\+', 'SELECT.*\.format', 'SELECT.*%s', 'SELECT.*f"'
- createQuery.*\+, Statement.*executeQuery.*\+
- User input in queries: request., req., params., body.

*NoSQL Injection:*
- db.collection.*find\(req., {\$where:, {\$regex:
- Model.find.*req.query, req.body, req.params

*Command Injection:*
- exec\(.*req., system\(.*\$_GET, shell_exec.*input
- Runtime.getRuntime\(\).exec\(.*request
- subprocess.*shell=True.*user.*input

*XSS (Cross-Site Scripting):*
- innerHTML.*=.*req., .html\(.*user, document.write\(.*untrusted
- dangerouslySetInnerHTML.*user
- render_template_string\(.*request

*LDAP/Template Injection:*
- LdapName\(.*request, eval\(.*req., Function\(.*user

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

## Agent 4 - Cryptography & Supply Chain (A04, A03)

```
Agent 4 - Cryptographic & Supply Chain Analysis:
- prompt: "Scan for OWASP A04 (Cryptographic Failures) and A03 (Software Supply Chain) in [FILES_LIST]:

**A04 - Cryptographic Failures:**
Use Grep to search for:

*Weak algorithms:*
- MD5, SHA1, SHA-1, DES, 3DES, RC4, Blowfish
- ECB.*mode, RSA.*512, RSA.*1024

*Weak random number generation:*
- Math.random\(\).*token|password|secret
- rand\(\).*(?!random_bytes)
- new Random\(\) (should be SecureRandom)

*Hardcoded secrets:*
- password\s*=\s*['"][^'"]+['"]
- api_key\s*=\s*['"], secret.*=.*['"][A-Za-z0-9+/=]{20,}
- AWS_ACCESS_KEY, PRIVATE_KEY, DATABASE_URL in code

*Insecure TLS:*
- SSLv2, SSLv3, TLSv1.0, TLSv1.1
- ssl_verify.*False, verify:\s*false, CERT_NONE

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

## Agent 5 - Bytecode & Compiled Code Security

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
- Angular DOM sanitization bypass: <svg><animate href="javascript:
- TypeScript type bypasses: any types in security-critical code
- Unsafe eval or Function constructor usage

**Java Bytecode (if applicable):**
Use Grep to search for:
- Deserialization: ObjectInputStream, readObject
- Bytecode verification disabled: -Xverify:none
- Unsafe reflection: Class.forName with user input

For each finding:
1. Explain the bytecode-level risk
2. Reference recent CVEs if applicable
3. Suggest static analysis tools (Pycdc, SpotBugs, etc.)

Return findings focusing on detection evasion risks and compilation-level vulnerabilities."
- subagent_type: "Explore"
```

## Agent 6 - Logging, Monitoring & Exception Handling (A09, A10)

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
- Generic exception catching: except:, except Exception:, catch \(Exception
- Empty catch blocks: catch.*\{\s*\}, except.*pass
- Stack trace exposure: printStackTrace, print.*exc_info, return.*error.*stack
- Unchecked nulls: .get\(.*\) without null checks, undefined access

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

## Security Best Practices by Role

### For Developers
1. **Run before PR**: Check code before creating pull requests
2. **Fix Critical/High first**: Prioritize based on severity
3. **Understand, don't copy-paste**: Learn why the vulnerability exists
4. **Test fixes**: Verify fixes do not break functionality
5. **Add tests**: Write security tests to prevent regressions

### For Security Teams
1. **Validate findings**: Verify each finding is a real vulnerability
2. **Assess risk**: Consider exploitability in the specific context
3. **Prioritize**: Not all findings need immediate fixes
4. **Track metrics**: Monitor security trends over time
5. **Provide training**: Use findings as teaching opportunities

### For DevOps/SRE
1. **Automate**: Integrate security scanning into CI/CD
2. **Gate deployments**: Block deployments with Critical vulnerabilities
3. **Monitor**: Set up alerts for new vulnerabilities
4. **Rotate secrets**: Immediately rotate any exposed credentials
5. **Incident response**: Have a plan for security incidents

## Recommended Follow-up

1. **Manual review**: Security expert should review all Critical/High findings
2. **Dynamic testing**: Use DAST tools (OWASP ZAP, Burp Suite) for runtime testing
3. **Penetration testing**: Professional pentest for production systems
4. **Security tools**: Integrate SAST/SCA tools into CI/CD pipeline
5. **Training**: Educate developers on secure coding practices

## Tool Recommendations

- **Python**: Bandit, Safety, pip-audit, Semgrep
- **JavaScript**: ESLint Security, npm audit, Snyk
- **Java**: SpotBugs + FindSecBugs, OWASP Dependency-Check
- **Multi-language**: SonarQube, Semgrep, CodeQL
