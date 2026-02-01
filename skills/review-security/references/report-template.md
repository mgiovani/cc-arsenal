# Security Review - Report Template

Use this template when generating the security report in Phase 5.

## Report Format

```markdown
# Security Review Report

**Scope**: [PR #123 | Commit abc123 | Entire Codebase]
**Date**: [YYYY-MM-DD]
**Files Scanned**: [N files]
**Total Findings**: [N vulnerabilities]

## Executive Summary

[2-3 sentence overview of security posture and critical issues]

## Severity Breakdown

- **Critical**: N findings
- **High**: N findings
- **Medium**: N findings
- **Low**: N findings

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

## Example Output

```
Security Review Report

**Scope**: PR #123 (5 files changed)
**Files Scanned**: 5 files
**Total Findings**: 12 vulnerabilities

Severity Breakdown:
- Critical: 2 findings
- High: 4 findings
- Medium: 5 findings
- Low: 1 finding

Top Critical Finding:
SQL Injection in user_service.py:45
  Raw SQL query with unsanitized user input

[Full detailed report follows...]
```
