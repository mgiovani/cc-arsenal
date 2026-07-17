# Dependency Review - Analysis Patterns

Detailed analysis steps for the three dependency-review dimensions used in Phase 3: vulnerabilities, licenses, staleness. Load this reference before starting Phase 3.

Each section below is written as a self-contained prompt. Use it two ways:
- **Default (single pass)**: work through all three sections yourself, in order, against the Phase 2 output already in context.
- **Large-output fan-out**: when the audit output is too large to reason about in one pass (e.g. a multi-ecosystem monorepo), spawn one `Explore` agent per section, pasting that section's prompt verbatim plus the relevant Phase 2 output.

## Dimension 1 — Vulnerability Analysis (CVE/GHSA Triage)

```
Agent 1 - Vulnerability Analysis:
- prompt: "Analyze dependency vulnerabilities from the audit output and Dependabot alerts.

**Input**: Raw audit output from Phase 2 and the project manifest files.

**Analysis Steps:**

1. Parse the audit output for each package manager:
   - Extract: package name, installed version, vulnerable version range, fix version, advisory ID
   - Note: severity rating from the tool (critical/high/medium/low)

2. For each vulnerability found:
   - Read the advisory details (CVE/GHSA ID, description)
   - Determine if a fix version is available
   - Check if the vulnerability is in a direct or transitive dependency
   - Assess exploitability context:
     * Is this a runtime dependency or dev-only?
     * Is the vulnerable code path likely reachable in this project?
     * Is there a known public exploit?
   - Check CISA KEV status: Is this a Known Exploited Vulnerability?

3. Cross-reference Dependabot alerts with local audit results:
   - Identify alerts not caught by local tools (and vice versa)
   - Note dismissed alerts and their reasons

4. For each finding, provide:
   - Package name and ecosystem
   - Installed version → fix version
   - CVE/GHSA identifier
   - Severity (Critical/High/Medium/Low)
   - CVSS score if available
   - Whether it affects direct or transitive dependency
   - Exploitability assessment (Active exploitation / Public exploit / Theoretical)
   - Whether fix is breaking (major version change) or non-breaking (patch/minor)
   - Specific remediation command (e.g., 'npm install package@version')

Return findings sorted by severity (Critical first), then by exploitability."
- subagent_type: "Explore" (only used when fanning out; skip this line when running inline)
```

## Dimension 2 — License Compliance Analysis

```
Agent 2 - License Compliance Analysis:
- prompt: "Analyze dependency licenses for compliance risks.

**Input**: Project manifest files (package.json, pyproject.toml, Cargo.toml, etc.) and lock files.

**Analysis Steps:**

1. Identify the project's own license:
   - Read LICENSE, LICENSE.md, or license field in manifest
   - Determine if the project is proprietary, permissive OSS, or copyleft

2. For each direct dependency, determine its license:
   - Read the license/licenses field from the manifest
   - Use Grep to search lock files for license metadata
   - For Node.js: check 'license' field in package.json of each dependency
   - For Python: check 'License' classifier or license field in pyproject.toml/setup.py
   - For Rust: check 'license' field in Cargo.toml

3. Classify each license into risk categories:

   **No Risk (Permissive)**:
   - MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, Unlicense, CC0-1.0, 0BSD

   **Low Risk (Permissive with conditions)**:
   - Apache-2.0 (patent clause), MPL-2.0 (file-level copyleft), Artistic-2.0

   **Medium Risk (Weak Copyleft)**:
   - LGPL-2.1, LGPL-3.0, EPL-1.0, EPL-2.0, CDDL-1.0
   - Risk: May require source disclosure of modifications to the library itself

   **High Risk (Strong Copyleft — problematic for proprietary projects)**:
   - GPL-2.0, GPL-3.0, AGPL-3.0, SSPL-1.0, EUPL-1.2
   - Risk: May require releasing entire derivative work under same license

   **Critical Risk (Problematic)**:
   - No license specified (defaults to All Rights Reserved)
   - Custom/unknown license text
   - License mismatch between declared and actual
   - Dual-licensed with incompatible options

4. Flag specific compliance issues:
   - Copyleft dependency in a proprietary project
   - AGPL dependency in a SaaS/cloud application
   - Missing license field (legally risky)
   - License incompatibility between dependencies
   - Dependencies with license changes between versions

5. For each finding, provide:
   - Package name and version
   - Detected license (SPDX identifier)
   - Risk level (Critical/High/Medium/Low/None)
   - Why it's a risk in this project's context
   - Recommended action (accept, replace, seek legal review)
   - Alternative packages with more permissive licenses (if replacement needed)

Return findings sorted by risk level, grouped by license category."
- subagent_type: "Explore" (only used when fanning out; skip this line when running inline)
```

## Dimension 3 — Staleness & Upgrade Complexity Analysis

```
Agent 3 - Staleness & Upgrade Complexity Analysis:
- prompt: "Analyze dependency staleness and assess upgrade complexity.

**Input**: Project manifest files, lock files, and audit output from Phase 2.

**Analysis Steps:**

1. For each direct dependency, determine version drift:
   - Current installed version (from lock file or manifest)
   - Latest available version (from audit output or manifest metadata)
   - Number of major/minor/patch versions behind
   - Time since last update (if available from lock file metadata)

2. Classify staleness levels:

   **Critical Staleness (3+ major versions behind or unmaintained)**:
   - Package is 3+ major versions behind latest
   - Package has been deprecated or archived
   - No commits/releases in 2+ years
   - Maintainer has announced end-of-life
   - Known security issues with no planned fix

   **High Staleness (2 major versions behind)**:
   - Package is 2 major versions behind
   - Current major version is no longer receiving security patches
   - Significant API changes between current and latest

   **Medium Staleness (1 major version behind)**:
   - Package is 1 major version behind
   - Current version still receiving security patches
   - Migration guide available for upgrade

   **Low Staleness (minor/patch versions behind)**:
   - Only minor or patch versions behind
   - Non-breaking updates available
   - No known issues with current version

3. Assess upgrade complexity for stale packages:

   **Easy Upgrade (patch/minor, non-breaking)**:
   - Patch or minor version bump
   - No breaking changes documented
   - Drop-in replacement expected
   - Estimated command: 'npm update package' or equivalent

   **Moderate Upgrade (major version, documented migration)**:
   - Major version bump with published migration guide
   - Limited API surface changes
   - Automated codemods available
   - May require test updates

   **Complex Upgrade (major version, significant changes)**:
   - Multiple major version jumps needed
   - Extensive API changes
   - Dependencies on other packages that also need upgrading
   - May require architectural changes

   **Replacement Recommended (deprecated/abandoned)**:
   - Package is deprecated with recommended replacement
   - Package is unmaintained with active forks available
   - Better alternatives exist in the ecosystem

4. Identify upgrade chains:
   - Dependencies that must be upgraded together
   - Peer dependency constraints that block upgrades
   - Packages blocking other upgrades (find the domino effect)

5. For each finding, provide:
   - Package name
   - Current version → latest version
   - Versions behind (major.minor.patch)
   - Staleness level (Critical/High/Medium/Low)
   - Upgrade complexity (Easy/Moderate/Complex/Replacement)
   - Breaking changes summary (if major upgrade)
   - Recommended upgrade path (step-by-step if complex)
   - Packages that must be co-upgraded
   - Alternative packages (if replacement recommended)

Return findings sorted by staleness level, then by number of dependents (most impactful first)."
- subagent_type: "Explore" (only used when fanning out; skip this line when running inline)
```

Audit commands per ecosystem live in [audit-commands.md](audit-commands.md) (loaded in Phase 2, not needed again here).

## Recommended Follow-up

After reviewing the dependency report:

1. **Immediate**: Apply non-breaking security patches (patch/minor version bumps)
2. **Short-term**: Address high-severity CVEs requiring major upgrades
3. **Medium-term**: Resolve license compliance issues
4. **Long-term**: Replace deprecated/abandoned dependencies
5. **Ongoing**: Configure Dependabot/Renovate for automated dependency updates
