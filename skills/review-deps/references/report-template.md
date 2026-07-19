# Dependency Review - Report Template

Use this template when generating the dependency report in Phase 5.

## Report Format

```markdown
# Dependency Review Report

**Project**: [project name]
**Date**: [YYYY-MM-DD]
**Package Managers**: [npm, pip, cargo, ...]
**Total Dependencies**: [N direct + N transitive]
**Critical Issues Found**: [Yes — N critical / No]

## Executive Summary

[2-3 sentence overview of dependency health posture, critical issues, and recommended priority actions]

## Severity Summary

| Severity | Vulnerabilities | License Risks | Staleness |
|----------|----------------|---------------|-----------|
| Critical | N | N | N |
| High | N | N | N |
| Medium | N | N | N |
| Low | N | N | N |
| **Total** | **N** | **N** | **N** |

---

## 1. Vulnerability Findings

### Critical Vulnerabilities

#### VULN-001: [Advisory Title]
- **Package**: `package-name@1.2.3` → fix: `@1.2.5`
- **Advisory**: [CVE-YYYY-NNNNN](https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNNN) / [GHSA-xxxx](https://github.com/advisories/GHSA-xxxx)
- **CVSS**: 9.8 (Critical)
- **Dependency Type**: Direct / Transitive (via `parent-package`)
- **Exploitability**: Active exploitation / Public exploit / Theoretical
- **CISA KEV**: Yes/No
- **Description**: [What the vulnerability allows]
- **Breaking Change**: No (patch version bump)
- **Remediation**:
  ```bash
  npm install package-name@1.2.5
  ```

[Repeat for each vulnerability...]

### High Vulnerabilities
[...]

### Medium Vulnerabilities
[...]

### Low Vulnerabilities
[...]

---

## 2. License Compliance Findings

### Project License Context
- **Project License**: [MIT / Proprietary / etc.]
- **Distribution Model**: [SaaS / Desktop / Library / Internal]

### Critical License Risks

#### LIC-001: [Package with problematic license]
- **Package**: `package-name@1.0.0`
- **License**: GPL-3.0
- **Risk**: Strong copyleft — may require releasing derivative work as GPL
- **Context**: [Why this is a problem for this specific project]
- **Recommendation**: Replace with `alternative-package` (MIT licensed)

[Repeat for each license finding...]

### High License Risks
[...]

### Medium License Risks
[...]

### Packages Without License
| Package | Version | Risk |
|---------|---------|------|
| `package-a` | 1.0.0 | No license declared — defaults to All Rights Reserved |

---

## 3. Staleness & Upgrade Planning

### Critical Staleness (Immediate Action)

#### STALE-001: [Deprecated/abandoned package]
- **Package**: `old-package@1.0.0`
- **Latest**: `4.0.0` (3 major versions behind)
- **Last Release**: [date]
- **Status**: Deprecated / Archived / Unmaintained
- **Upgrade Complexity**: Complex
- **Breaking Changes**: [Summary of major changes]
- **Recommended Path**:
  1. Replace with `new-package@2.0.0` (actively maintained fork)
  2. Or: Upgrade to `old-package@4.0.0` following [migration guide](url)
- **Co-upgrades Required**: `peer-dep-a@3.0.0`, `peer-dep-b@2.0.0`

[Repeat for each staleness finding...]

### High Staleness (Plan Upgrade)
[...]

### Medium Staleness (Schedule Upgrade)
[...]

### Easy Updates Available (Non-breaking)

| Package | Current | Latest | Type | Command |
|---------|---------|--------|------|---------|
| `pkg-a` | 1.2.3 | 1.2.5 | patch | `npm install pkg-a@1.2.5` |
| `pkg-b` | 2.1.0 | 2.3.0 | minor | `npm install pkg-b@2.3.0` |

---

## 4. Prioritized Action Plan

### Immediate (This Sprint)
1. **[VULN-001]** Patch `package-name` to `1.2.5` — critical RCE, non-breaking
2. **[VULN-002]** Update `other-package` to `3.1.0` — high severity, public exploit
3. Apply all non-breaking security patches (see Easy Updates table)

### Short-term (Next 2 Sprints)
1. **[LIC-001]** Replace `gpl-package` with MIT alternative
2. **[STALE-001]** Plan migration from `deprecated-package` to `replacement`
3. **[VULN-003]** Major upgrade for `framework@2.0` → `framework@4.0`

### Medium-term (This Quarter)
1. **[STALE-002]** Upgrade across major versions with breaking changes
2. **[LIC-002]** Seek legal review for LGPL dependencies
3. Configure automated dependency updates (Dependabot/Renovate)

### Long-term (Ongoing)
1. Monitor CISA KEV for newly exploited vulnerabilities
2. Review licenses when adding new dependencies
3. Set up CI checks for license compliance
4. Regular quarterly dependency review cadence

---

## 5. Ecosystem-Specific Notes

### [Package Manager] Specific Observations
- [Notes about lock file health, workspace configuration, etc.]
- [Peer dependency conflicts identified]
- [Registry configuration concerns]

---

## Tooling Recommendations

Based on this analysis, consider adding:

- **Dependency Updates**: Dependabot, Renovate, or Snyk automated PRs
- **Vulnerability Scanning**: Integrate `npm audit` / `pip-audit` in CI pipeline
- **License Checking**: FOSSA, license-checker, or pip-licenses in CI
- **Supply Chain Security**: Socket.dev, Sigstore, or npm provenance
- **Scorecard**: OpenSSF Scorecard for critical dependencies

## Audit Tool Output Summary

| Tool | Status | Findings |
|------|--------|----------|
| npm audit | Ran successfully | N vulnerabilities |
| pip-audit | Not installed | — |
| Dependabot | N alerts | N open, N dismissed |
| [etc.] | | |

---

**Next Steps**: Apply immediate patches, plan short-term upgrades, and configure automated dependency monitoring.
```
