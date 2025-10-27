---
description: "Validate documentation freshness, completeness, and quality"
argument-hint: "[focus]"
allowed-tools: ["Read", "Grep", "Glob", "Bash(git *, find *)"]
---

# Check Documentation Quality

Validate documentation freshness, completeness, and quality against current codebase state.

## Your Task

1. **Parse Arguments**:
   - Extract optional focus area from `$ARGUMENTS`
   - Focus areas: `core`, `data`, `infrastructure`, `all`
   - Default: check all documentation

2. **Scan Documentation**:
   - Find all documentation files in `docs/`
   - Identify documentation types present
   - Check for ADRs and RFCs

3. **Analyze Project** (determine what docs should exist):
   - Technology stack detection
   - Database presence
   - Deployment configurations
   - Project type (library, app, service)

4. **Perform Validation Checks**:

   **A. Relevance Check**:
   - Determine which docs are relevant to this project
   - Identify missing documentation for detected technologies
   - Example: If database models found, should have data-model.md

   **B. Freshness Check**:
   - Compare doc last-modified dates with related code changes
   - Use git to check recent changes:
   ```bash
   # Check when files were last modified
   !`git log -1 --format="%ai" -- docs/architecture.md 2>/dev/null`

   # Check recent changes to codebase
   !`git log --since="7 days ago" --oneline --name-only | head -50`
   ```
   - Flag docs that haven't been updated after significant code changes

   **C. Completeness Check**:
   - Verify all required sections are present
   - Check for unreplaced placeholders: `{{PLACEHOLDER}}`
   - Ensure diagrams exist where expected
   - Verify ADRs have all sections (Status, Context, Decision)
   - Verify RFCs have all sections (Summary, Motivation, Proposal)

   **D. Quality Check**:
   - Validate Mermaid diagram syntax
   - Check for broken internal links (references to non-existent files)
   - Verify markdown formatting
   - Check for empty sections

5. **Calculate Scores**:

   **Freshness Scoring** (per document):
   - Fresh (90-100): Updated within last 7 days or no related code changes
   - Good (70-89): Minor code changes since last update
   - Stale (50-69): Significant code changes since last update
   - Outdated (<50): Major code changes or very old

   **Completeness Scoring** (per document):
   - Complete (90-100): All sections present, no placeholders
   - Good (70-89): Most sections present, minor gaps
   - Incomplete (50-69): Several missing sections
   - Poor (<50): Major sections missing

   **Quality Scoring** (per document):
   - Excellent (90-100): No issues, all diagrams valid
   - Good (70-89): Minor formatting issues
   - Fair (50-69): Several issues
   - Poor (<50): Major problems, broken diagrams

   **Overall Score**:
   - Average of all document scores
   - Weight by importance (core docs > others)

6. **Generate Report**:
   - Status summary with overall score
   - List of documents by status (Good, Needs Attention, Missing)
   - Quality issues with specific locations
   - Actionable recommendations

## Validation Checks Detail

### Missing Documentation
```bash
# Check for expected docs
!`ls -1 docs/ 2>/dev/null | grep -E "architecture|onboarding|data-model|deployment"`

# Check for ADRs
!`ls -1 docs/adr/*.md 2>/dev/null | wc -l`

# Check for RFCs
!`ls -1 docs/rfc/*.md 2>/dev/null | wc -l`
```

### Stale Documentation
```bash
# Get last modification date of docs
!`find docs -name "*.md" -exec stat -f "%Sm %N" -t "%Y-%m-%d" {} \; 2>/dev/null || find docs -name "*.md" -exec stat -c "%y %n" {} \;`

# Get recent code changes
!`git log --since="30 days ago" --name-only --pretty=format: | sort -u | grep -v "^$" | head -30`
```

### Placeholder Check
```bash
# Find unreplaced placeholders
!`grep -r "{{.*}}" docs/ --include="*.md" 2>/dev/null`
```

### Broken Links
```bash
# Find markdown links
!`grep -r "\[.*\](" docs/ --include="*.md" -h | grep -o "\[.*\](.*)" | head -20`
```

## Usage

Check all documentation:
```
/docs:check
```

With specific focus:
```
/docs:check core
/docs:check data
/docs:check focus on database documentation
```

Quick check:
```
/docs:check quick
```

## Output Format

### Status Summary
```
Documentation Health Report

Overall Score: 85/100

✅ Good (3 docs):
  • docs/architecture.md (Score: 95/100)
    - Last updated: 2 days ago
    - All sections complete
    - Diagrams valid

  • docs/onboarding.md (Score: 92/100)
    - Last updated: 1 week ago
    - Comprehensive and current

  • docs/adr/ (5 records, Score: 88/100)
    - All ADRs properly formatted
    - Recent decisions documented

⚠️ Needs Attention (2 docs):
  • docs/data-model.md (Score: 65/100)
    - Outdated: Models changed 5 days ago (docs/data-model.md:1)
    - Missing ER diagram
    → Recommendation: Run /docs:diagram er

  • docs/deployment.md (Score: 58/100)
    - Missing deployment steps for new services
    - Placeholder not replaced: {{DEPLOYMENT_STEPS}} (line 42)
    → Recommendation: Run /docs:update deployment

❌ Missing (2 docs):
  • docs/security.md
    - Security middleware detected but not documented
    → Recommendation: Run /docs:init or /docs:diagram security

  • docs/api-documentation.md
    - 15 API endpoints found but not documented
    → Recommendation: Run /docs:init

🔧 Quality Issues:
  • docs/data-model.md:42 - Invalid Mermaid syntax
  • docs/architecture.md:15 - Broken link to [non-existent.md]
  • docs/deployment.md:23 - Unreplaced placeholder {{DEPLOYMENT_STEPS}}
```

### Detailed Report

For each documentation file:
- **Filename and path**
- **Score breakdown** (Freshness + Completeness + Quality)
- **Last Updated**: Timestamp
- **Specific Issues**: With line numbers
- **Recommendations**: Actionable next steps with commands

## Recommendations Format

Based on findings, suggest specific actions:

```
Priority Recommendations:

1. HIGH: Update data model documentation
   Command: /docs:diagram er
   Reason: Schema changed 5 days ago, ER diagram missing

2. MEDIUM: Fix deployment documentation placeholders
   Command: /docs:update deployment
   Reason: Contains unreplaced placeholders

3. LOW: Add security documentation
   Command: /docs:diagram security
   Reason: Good practice for complete documentation
```

## Important Notes

- **Non-destructive**: Only reads, never modifies documentation
- **Git-aware**: Uses git history to assess freshness
- **Context-aware**: Understands project type and relevant docs
- **Actionable**: Provides specific commands to fix issues
- **Incremental**: Can be run frequently

## Example Checks

### Core Documentation
- architecture.md exists and current?
- onboarding.md exists and comprehensive?
- ADRs directory exists with properly formatted ADRs?

### Data Documentation
- data-model.md exists if database detected?
- ER diagrams present and valid?
- Schema matches current models?

### Infrastructure Documentation
- deployment.md exists if Docker/K8s detected?
- Security.md exists?
- Dependencies documented?

## When to Run

Run this command:
- Before onboarding new team members
- During documentation reviews
- After major refactoring
- As part of pre-release checklist
- When documentation feels stale
- Regularly (weekly or bi-weekly)

## Best Practices

- **Run regularly**: Make it part of your workflow
- **Address issues**: Don't let documentation debt accumulate
- **Automate**: Consider running in CI for documentation PRs
- **Prioritize**: Fix high-impact issues first
- **Track scores**: Monitor documentation health over time

---

**Dependencies**: Requires git for freshness checking
**Output**: Comprehensive health report with scores and recommendations
