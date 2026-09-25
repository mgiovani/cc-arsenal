# Dependency Review - Report Template

Use this template when generating the dependency report in Phase 5.

## Report Format

```markdown
# Dependency Review Report

| Field | Value |
| --- | --- |
| Project | [project name] |
| Date | [YYYY-MM-DD] |
| Package Managers | [npm, pip, cargo, ...] |
| Total Dependencies | [N direct + N transitive] |
| Critical Issues Found | [Yes (N critical) / No] |

## Executive Summary

[2-3 sentence overview of dependency health posture, critical issues, and recommended priority actions]

## Severity Summary

| Severity | Vulnerabilities | License Risks | Staleness |
|----------|----------------|---------------|-----------|
| Critical | N | N | N |
| High | N | N | N |
| Medium | N | N | N |
| Low | N | N | N |
| Total | N | N | N |

---

## 1. Vulnerability Findings

Group findings under a `#### <Severity> Vulnerabilities` heading per severity level that has at least one finding (Critical, High, Medium, Low, in that order); skip the heading for any severity with none. Document each finding with this table:

| Field | Value |
| --- | --- |
| ID | VULN-001 |
| Package | `package-name@1.2.3` → fix: `@1.2.5` |
| Advisory | [CVE-YYYY-NNNNN](https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNNN) / [GHSA-xxxx](https://github.com/advisories/GHSA-xxxx) |
| CVSS | 9.8 (Critical) |
| Dependency type | Direct / Transitive (via `parent-package`) |
| Exploitability | Active exploitation / Public exploit / Theoretical |
| CISA KEV | Yes/No |
| Description | [What the vulnerability allows] |
| Breaking change | No (patch version bump) |
| Remediation | `npm install package-name@1.2.5` |

[Repeat the table for each vulnerability in this severity level.]

---

## 2. License Compliance Findings

| Field | Value |
| --- | --- |
| Project license | [MIT / Proprietary / etc.] |
| Distribution model | [SaaS / Desktop / Library / Internal] |

Group findings under a `#### <Severity> License Risks` heading per severity level that has at least one finding (Critical, High, Medium); skip the heading for any severity with none. Document each finding with this table:

| Field | Value |
| --- | --- |
| ID | LIC-001 |
| Package | `package-name@1.0.0` |
| License | GPL-3.0 |
| Risk | Strong copyleft: may require releasing derivative work as GPL |
| Context | [Why this is a problem for this specific project] |
| Recommendation | Replace with `alternative-package` (MIT licensed) |

[Repeat the table for each license finding in this severity level.]

### Packages Without License

| Package | Version | Risk |
|---------|---------|------|
| `package-a` | 1.0.0 | No license declared, defaults to All Rights Reserved |

---

## 3. Staleness & Upgrade Planning

Group findings under a `#### <Severity> Staleness` heading per severity level that has at least one finding (Critical: immediate action, High: plan upgrade, Medium: schedule upgrade); skip the heading for any severity with none. Document each finding with this table:

| Field | Value |
| --- | --- |
| ID | STALE-001 |
| Package | `old-package@1.0.0` |
| Latest | `4.0.0` (3 major versions behind) |
| Last release | [date] |
| Status | Deprecated / Archived / Unmaintained |
| Upgrade complexity | Complex |
| Breaking changes | [Summary of major changes] |
| Recommended path | Replace with `new-package@2.0.0` (actively maintained fork), or upgrade to `old-package@4.0.0` following the [migration guide](url) |
| Co-upgrades required | `peer-dep-a@3.0.0`, `peer-dep-b@2.0.0` |

[Repeat the table for each staleness finding in this severity level.]

### Easy Updates Available (Non-breaking)

| Package | Current | Latest | Type | Command |
|---------|---------|--------|------|---------|
| `pkg-a` | 1.2.3 | 1.2.5 | patch | `npm install pkg-a@1.2.5` |
| `pkg-b` | 2.1.0 | 2.3.0 | minor | `npm install pkg-b@2.3.0` |

---

## 4. Prioritized Action Plan

### Immediate (This Sprint)
1. [VULN-001] Patch `package-name` to `1.2.5`: critical RCE, non-breaking
2. [VULN-002] Update `other-package` to `3.1.0`: high severity, public exploit
3. Apply all non-breaking security patches (see Easy Updates table)

### Short-term (Next 2 Sprints)
1. [LIC-001] Replace `gpl-package` with MIT alternative
2. [STALE-001] Plan migration from `deprecated-package` to `replacement`
3. [VULN-003] Major upgrade for `framework@2.0` → `framework@4.0`

### Medium-term (This Quarter)
1. [STALE-002] Upgrade across major versions with breaking changes
2. [LIC-002] Seek legal review for LGPL dependencies
3. Configure automated dependency updates (Dependabot/Renovate)

### Long-term (Ongoing)
1. Monitor CISA KEV for newly exploited vulnerabilities
2. Review licenses when adding new dependencies
3. Set up CI checks for license compliance
4. Regular quarterly dependency review cadence

---

## 5. Ecosystem-Specific Notes

Notes for the detected package manager(s):
- Lock file health and workspace/monorepo configuration
- Peer dependency conflicts identified
- Registry configuration concerns

---

## Tooling Recommendations

Based on this analysis, consider adding the following, matched to the gap it closes:

| Category | Options |
| --- | --- |
| Dependency updates | Dependabot, Renovate, or Snyk automated PRs |
| Vulnerability scanning | Integrate `npm audit` / `pip-audit` in the CI pipeline |
| License checking | FOSSA, license-checker, or pip-licenses in CI |
| Supply chain security | Socket.dev, Sigstore, or npm provenance |
| Scorecard | OpenSSF Scorecard for critical dependencies |

## Audit Tool Output Summary

| Tool | Status | Findings |
|------|--------|----------|
| npm audit | Ran successfully | N vulnerabilities |
| pip-audit | Not installed | N/A |
| Dependabot | N alerts | N open, N dismissed |
| [etc.] | | |

---

Next steps: apply immediate patches, plan short-term upgrades, and configure automated dependency monitoring.
```
