---
name: review-perf
description: Deep-dive performance audit of database queries, algorithmic complexity,
  frontend bottlenecks, and resource leaks for a PR, a commit, or the whole codebase,
  producing a severity-ranked report. Use when the user explicitly wants a dedicated
  performance review, asks to "audit performance", "find N+1 queries", "check for
  memory leaks", or "review query efficiency" - especially when review-code's single
  performance dimension isn't thorough enough. Analysis only - identifies issues
  without modifying, fixing, or committing code. Not for a general six-dimension
  review where performance is just one concern among several (use review-code), and
  not for a full multi-agent PR review team (use team-review).
metadata:
  author: mgiovani
  version: 1.2.0
disable-model-invocation: true
---

# Performance Review

Comprehensive performance analysis targeting database query inefficiencies, algorithmic complexity issues, frontend bottlenecks, and resource leaks. **Analysis only** - identifies problems and suggests optimizations without making code changes.

## Constraints

- **Analysis only** - never modifies, fixes, or commits code, even if asked to "also fix these" mid-run; report the findings and stop
- **Static analysis** - no runtime profiling, no benchmarking, no load testing
- **Pattern-based** - Big O and impact estimates are approximate; may miss context-specific issues a profiler would catch
- **Not exhaustive** - does not guarantee 100% detection; profiling is recommended before acting on critical findings
- **Read before claiming** - never report a finding in a file that has not actually been read; every finding cites the specific file path and line number it came from
- **No invented numbers** - counts, query-multiplication estimates, and Big O claims must trace back to code actually read, not generic examples copied from the report template
- **Diff-scope confinement** - for a PR or commit review, never grep or read a file the diff didn't touch, and never let a pre-existing issue in a touched file masquerade as a PR finding; see Phase 0/2

## Scan Workflow

### Phase 0: Determine Scan Scope

Parse arguments:

- `<pr_number>`: scan only files changed in that PR (e.g. `123`, `#123`)
- `<commit_sha>`: scan only files changed in that commit
- `--all` or no args: scan entire codebase
- `--scope [database|algorithm|frontend|resources|backend]`: focus on specific categories (`backend` = database + algorithm + resources, excludes frontend)

If PR or commit specified, pull the *full diff* - not just the file list - so hunk ranges are available for Phase 2's confinement check:

```bash
# For PR
gh pr diff <pr_number>

# For commit
git diff-tree -p <commit_sha>
```

From that diff, extract two things and carry both into Phase 2:
1. **Changed-file list**: the paths after each `+++ b/` line.
2. **Hunk ranges per file**: each `@@ -a,b +c,d @@` header gives the new-file line range `c` to `c+d-1` for that hunk. A file can have multiple hunks.

`--all` or no args skips this entirely - there's no diff to confine to, the whole codebase is in scope.

### Phase 1: Project Technology Discovery

Explore the codebase to identify the stack (language, ORM, framework) - it determines which anti-patterns in [references/agent-prompts.md](references/agent-prompts.md) apply and which profiling tools to recommend.

### Phase 2: Scan the Codebase

Four scan categories, each with its own grep patterns and reporting format in [references/agent-prompts.md](references/agent-prompts.md):

- **Database**: N+1 queries, missing indexes, connection management
- **Algorithm**: quadratic+ complexity, inefficient data structures, unnecessary recomputation
- **Frontend**: bundle size, rendering (React re-renders, layout thrashing), network waterfalls
- **Resources**: memory leaks, connection/file-handle leaks, thread/process leaks

Spawn only the category matching `--scope`; spawn all 4 for `--all`, no scope, or `--scope backend` (database + algorithm + resources).

With subagent tools available: spawn one Explore agent per category in parallel, using the prompts in the reference file, and track progress with TodoWrite. Without subagent tools: run the categories sequentially inline in the same order, one grep pass and read-verify cycle per category.

For a PR or commit review, pass the Phase 0 changed-file list to every category (agent or inline) as the *only* valid grep/read target - a file the diff didn't touch is out of bounds even if it looks relevant (e.g. a service a changed view calls into). For `--all`, there's no such restriction.

Each category, agent or inline:
1. Grep for the anti-patterns for that category, restricted to the changed-file list on a PR/commit review
2. Read each match to verify context (hot path vs. cold path - a slow pattern in init code is not the same finding as one in a request handler)
3. On a PR/commit review, check the match's line number against that file's hunk ranges from Phase 0:
   - Inside a hunk → a PR finding, goes through steps 4-6 into the main Findings section
   - Outside every hunk (pre-existing code in a touched file) → skip steps 4-6's severity/fix writeup and instead route it to the separate "Pre-existing issues" bucket (Phase 4); never mix it into the main findings
4. Extract the exact code snippet (5-10 lines)
5. Classify severity (Critical/High/Medium/Low) and explain why
6. Give 2-3 optimization approaches
7. Estimate impact where the code supports it (e.g. "O(n²) → O(n log n)", "101 queries → 2 queries for 100 records")

### Phase 3: Consolidate & Prioritize

1. Collect findings from all categories scanned; deduplicate anything two categories both flagged
2. On a PR/commit review, keep the pre-existing-issues bucket separate from the main findings throughout - it never enters the severity tally below
3. Sort by severity:
   - **Critical**: N+1 in loops, O(n²+) on large datasets, memory leaks in long-running processes, unbounded resource allocation
   - **High**: missing indexes, sync blocking in async contexts, large bundle imports, connection pool exhaustion
   - **Medium**: suboptimal queries, unnecessary re-renders, missing caching, inefficient data structures
   - **Low**: minor optimizations, marginal-impact style preferences
4. Group by domain (Database/Algorithm/Frontend/Resources) and compute stats: total issues, by severity, by category, files scanned vs. files with issues

### Phase 4: Generate Report

Follow [references/report-template.md](references/report-template.md). Every number in it (finding counts, severity totals, file:line refs) must come from Phase 3's actual tally - never fill in the template's placeholder numbers as if they were real.

On a PR/commit review with a non-empty pre-existing-issues bucket, add a "Pre-existing Issues Noticed in Touched Files (outside this PR's changes)" section after the main Findings section - same file:line/snippet/severity format, clearly separated, excluded from the Severity Breakdown and Performance Impact Summary counts (which cover main findings only). If the bucket is empty, omit the section rather than writing a placeholder.

After writing the Findings sections, recount: count the actual Finding entries present in the report (per category and per severity) and use that recount for the Severity Breakdown and Performance Impact Summary table. Never estimate the summary counts or carry forward Phase 3's tally unreconciled - if a finding was dropped or merged while writing the report, the totals must reflect what's actually written, not what was originally found.

## Usage

```bash
review-perf 123                      # scan PR 123
review-perf #456
review-perf abc123def                # scan a commit
review-perf --all                    # scan entire codebase
review-perf                          # same as --all
review-perf --all --scope database   # codebase-wide, database findings only
review-perf 123 --scope frontend     # PR 123, frontend findings only
```

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md) - grep patterns and per-category scan prompts (load in Phase 2)
- [references/report-template.md](references/report-template.md) - full markdown report template (load in Phase 4)

## Performance References

- [Web Vitals](https://web.dev/vitals/) - Core Web Vitals metrics and thresholds
- [React Performance](https://react.dev/learn/render-and-commit) - React rendering optimization
- [Database Query Optimization](https://use-the-index-luke.com/) - SQL indexing and query patterns
- [Memory Management Best Practices](https://developer.chrome.com/docs/devtools/memory-problems/) - memory leak detection
