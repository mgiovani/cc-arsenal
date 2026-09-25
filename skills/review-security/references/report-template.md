# Security review - report template

Use this template when generating the security report in Phase 5.

## Report format

```markdown
# Security Review Report

| Field | Value |
| --- | --- |
| Scope | [PR #123 \| Commit abc123 \| Entire Codebase] |
| Date | [YYYY-MM-DD] |
| Files Scanned | [N files] |
| Total Findings | [N vulnerabilities] |

## Executive summary

[2-3 sentence overview of security posture and critical issues]

## Severity breakdown

| Severity | Findings |
| --- | --- |
| Critical | N |
| High | N |
| Medium | N |
| Low | N |

## Findings by OWASP category

Give each OWASP category its own `### A0N: <category name> (N findings)` heading, in order (A01 through A10); omit a heading for any category with zero findings. Document every finding with this table, its code snippet, and a numbered fix list:

### A01: Broken access control (N findings)

#### Finding 1: [Vulnerability Title]

| Field | Value |
| --- | --- |
| Severity | Critical |
| File | `path/to/file.py:123-130` |
| Description | [What is vulnerable and why] |
| Explanation | [Why this is exploitable, reference CWE if applicable] |
| Attack scenario | [How an attacker could exploit this] |

```python
[Actual vulnerable code]
```

Recommended fixes:
1. Primary: [description with code example]
2. Fallback: [alternative approach with code example]
3. Fallback: [another alternative if applicable]

Add one block like this per finding. Repeat the same table + snippet + fix-list shape under each other in-scope `### A0N` heading: A02 Security Misconfiguration, A03 Software Supply Chain Failures, A04 Cryptographic Failures, A05 Injection Vulnerabilities, A06 Insecure Design, A07 Authentication Failures, A08 Data Integrity Failures, A09 Logging/Monitoring Failures, and A10 Exception Handling Issues.

## Bytecode security analysis

Cover Python bytecode, JavaScript/TypeScript compilation output, and Java bytecode findings here, each under its own `### <language> findings (if applicable)` heading, using the same finding table shape as above; omit a language with nothing to report.

## Recommendations by priority

### Immediate action required (Critical/High)
1. [Finding reference] - [Brief action item]
2. [...]

### Short-term improvements (Medium)
1. [Finding reference] - [Brief action item]
2. [...]

### Long-term enhancements (Low)
1. [Finding reference] - [Brief action item]
2. [...]

## Security tooling recommendations

Based on this analysis, consider adding:

| Category | Recommendation |
| --- | --- |
| SAST | [Tool recommendations based on tech stack] |
| Dependency scanning | [Tool recommendations] |
| Secret detection | [Tool recommendations] |
| Pre-commit hooks | [Specific hooks to add] |
| CI/CD security | [Pipeline improvements] |

## References

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [CWE Database](https://cwe.mitre.org/)
- [Relevant CVEs mentioned in findings]

---

Next steps: review findings, prioritize fixes, and implement recommended security controls.
```

## Example output

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
