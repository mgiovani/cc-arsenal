---
name: review-security
description: Perform an OWASP Top 10-focused static security review of a PR, commit, or
  entire codebase, grep for vulnerable patterns (injection, broken access control, crypto
  failures, hardcoded secrets), verify each match by reading it in context, and produce a
  severity-ranked report with file:line evidence and fix suggestions. Use to audit code
  security, scan for vulnerabilities, or check OWASP compliance, "security review", "scan
  for vulnerabilities", "check OWASP top 10", "audit for XSS/SQLi/hardcoded secrets", "is
  this PR safe to ship security-wise". Analysis only, never modifies code. Not for general
  code quality review (use review-code), dependency CVE/license/staleness auditing (use
  review-deps), or a multi-agent PR review team (use team-review).
metadata:
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: '[pr_number|commit_sha|--all] [--scope scope]'
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Task, TodoWrite, AskUserQuestion
context: fork
agent: general-purpose
---

# Security Review

Static security analysis targeting OWASP Top 10 vulnerabilities and common language-specific
security patterns. Analysis only: identifies vulnerabilities, explains findings, and
suggests fix approaches without making code changes.

OWASP renumbers and re-titles its Top 10 categories periodically. Before labeling any finding
with a category code (A01, A02, ...), do a quick web check against owasp.org/Top10/ to confirm
the codes below are still current; if they've shifted, use the current codes and note the
change in the report instead of silently reusing stale labels.

## Anti-Hallucination Guidelines

1. **Read before claiming**: never report a vulnerability in code that hasn't been read.
2. **Evidence-based findings**: every finding references a specific file path and line number.
3. **Pattern matching**: use Grep to find actual vulnerable patterns, not hypothetical ones.
4. **No invented CVEs**: only reference real vulnerabilities when providing context.
5. **Quantifiable results**: statistics come from counting actual matches, never estimates.
6. **No false positives**: verify each finding matches a documented vulnerability pattern.
7. **Scope verification**: only scan files within the specified scope (PR/commit/all).

## Scan Workflow

### Phase 0: Determine Scan Scope

Parse arguments to determine what to scan:

- `<pr_number>`: scan only files changed in PR (e.g. "123", "#123")
- `<commit_sha>`: scan only files changed in commit (e.g. "abc123")
- `--all` or no args: scan entire codebase
- `--scope [web|api|mobile|backend|frontend]`: focus on specific vulnerability categories

If a PR or commit is specified, use Bash to get changed files:

```bash
# For PR
gh pr view <pr_number> --json files --jq '.files[].path'

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
```

### Phase 1: Project Technology Discovery

Use an Explore agent (`model: haiku`) to identify the stack: languages/frameworks from
package.json/pyproject.toml/pom.xml/go.mod, existing security tooling
(.pre-commit-config.yaml, SAST steps in .github/workflows), web framework, DB/ORM patterns,
auth patterns (JWT/OAuth/sessions), and any SECURITY.md. Return a stack summary with the
vulnerability categories to prioritize. No Task tool available? Skip the agent, read those
same files and grep those same paths yourself, inline, and note the stack directly.

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track scan progress across all OWASP categories, bytecode security, and
report generation.

### Phase 3: Vulnerability Scanning

Each OWASP category is owned by a fixed agent number (grep patterns and full prompts for
each are in [references/agent-prompts.md](references/agent-prompts.md)):

| Agent | Owns |
|---|---|
| 1 | A01 Access Control, A07 Authentication |
| 2 | A02 Security Misconfiguration, A06 Insecure Design |
| 3 | A05 Injection, A08 Data Integrity |
| 4 | A04 Cryptographic Failures, A03 Supply Chain (SRI/lockfiles/CI trust settings only, see note below) |
| 5 | Bytecode & compiled-code security |
| 6 | A09 Logging/Monitoring, A10 Exception Handling |

**Scope → categories in scope** (the only place scope decides anything: edit this table,
nowhere else, if scope definitions change):

| `--scope` | Categories |
|---|---|
| `web` | A02, A05 |
| `api` | A01, A06, A07 |
| `mobile` | A04, A08 |
| `backend` | A05, A06, A08 |
| `frontend` | A02, A05, A08 |
| (none) / `--all` | all categories, all 6 agents |

Spawn every agent that owns at least one category from the scope's list (per the ownership
table above). Spawn all 6 for `--all` or no scope given.

Each agent must: grep for its patterns, read each match to verify context, extract the exact
code snippet (5-10 lines), explain why it's vulnerable, classify severity
(Critical/High/Medium/Low), and give 2-3 fix approaches.

No Task tool available? Work through each owned category inline and sequentially instead of
spawning its agent, same grep patterns from the reference file, same read-and-verify step,
one category at a time.

**A03 note**: dependency staleness and known-CVE checks (outdated package versions, `npm
audit`-style findings) are review-deps' job, not this skill's: don't duplicate them here.
Agent 4 only checks the supply-chain surface review-deps doesn't: missing SRI on CDN
`<script>` tags, absent lockfiles, and CI/CD steps that weaken package integrity (e.g.
`--trusted-host`, `strict-ssl false`). If dependency CVEs come up, point the user to
review-deps instead of reporting them here.

### Phase 4: Consolidate & Analyze Findings

After scanning completes:

1. **Collect all findings** from every agent/category pass.
2. **Deduplicate**: remove duplicate findings across categories.
3. **Prioritize by severity**: Critical (RCE, SQLi, auth bypass, hardcoded secrets) > High
   (XSS, CSRF, broken access control, weak crypto) > Medium (info disclosure, missing
   logging, insecure design) > Low (minor security-adjacent code quality).
4. **Categorize by OWASP category** (confirm codes are current per the note at the top of
   this file before tagging).
5. **Statistics**: total vulnerabilities, counts by severity/category, files scanned vs.
   files with issues, all counted from actual findings, never estimated.

### Phase 5: Generate Security Report

Generate a markdown report following [references/report-template.md](references/report-template.md).

### Phase 6: Verification & Quality Check

Before presenting the report, verify: every finding has a file path + line numbers + an
actual code snippet (not a placeholder) + a clear explanation + 2-3 fix approaches;
statistics are counted, not estimated; no duplicate findings; severity ratings are
justified; only scanned files within the specified scope; no invented vulnerabilities; any
CWE/CVE references are accurate.

## Usage

```bash
review-security 123              # scan files changed in PR #123
review-security abc123def        # scan files changed in a commit
review-security --all            # scan entire codebase
review-security                  # same as --all
review-security --all --scope web
review-security 123 --scope api
```

If no scope is specified, scan comprehensively across all categories.

## Worked Example

Input: `review-security --all --scope api` on a Flask API.

Agent 1 (A01/A07) and Agent 2 (A02/A06) run, per the scope table above, `api` maps to
A01/A06/A07, both owned by those two agents. A finding might read:

```
#### Finding 1: Missing authorization check on account balance endpoint
- Severity: Critical
- File: `app/routes/accounts.py:42-47`
- Code:
  @app.route("/api/accounts/<account_id>/balance")
  def get_balance(account_id):
      account = Account.query.get(account_id)
      return jsonify(balance=account.balance)
- Explanation: any authenticated user can read any account's balance by
  guessing/enumerating account_id, no ownership check against the current session user.
- Fix approaches:
  1. Add `if account.owner_id != current_user.id: abort(403)` before the query returns.
  2. Scope the query itself: `Account.query.filter_by(id=account_id, owner_id=current_user.id).first_or_404()`.
```

Agent 3/4/5/6 don't run for this scope: their categories (A03-A05, A08-A10, bytecode)
aren't in the `api` scope's list.

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md): grep patterns and full agent prompts per category
- [references/report-template.md](references/report-template.md): full markdown report template

## What This Skill Does NOT Do

- Does not modify code, auto-fix vulnerabilities, or commit changes
- Does not run dynamic security testing (DAST) or penetration testing
- Does not audit dependency CVEs, versions, or licenses (use review-deps)
- Does not guarantee 100% detection, static, pattern-based analysis only

## OWASP References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)
