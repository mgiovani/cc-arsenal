---
name: review-perf
description: Perform comprehensive performance review analyzing database queries,
  algorithmic complexity, frontend bottlenecks, and resource leaks for PRs, commits,
  or entire codebases. This skill should be used when a user wants to audit code performance,
  identify bottlenecks, review query efficiency, or check for memory leaks. Analysis
  only - identifies issues without modifying code.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
---

# Review Perf

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Performance Review

Comprehensive performance analysis targeting database query inefficiencies, algorithmic complexity issues, frontend bottlenecks, and resource leaks. This skill performs **analysis only** - it identifies performance problems, explains findings, and suggests optimization approaches without making code changes.

## Anti-Hallucination Guidelines

**CRITICAL**: Performance reviews must be based on ACTUAL code analysis and VERIFIED patterns:
1. **Read before claiming** - Never report performance issues in code that has not been read
2. **Evidence-based findings** - Every finding must reference specific file paths and line numbers
3. **Pattern matching** - Use Grep to find actual anti-patterns, not hypothetical ones
4. **No invented metrics** - Only report measurable or verifiable performance concerns
5. **Quantifiable results** - Count actual instances, do not estimate
6. **No false positives** - Verify each finding matches documented performance anti-patterns
7. **Scope verification** - Only scan files within specified scope (PR/commit/all)
8. **Context matters** - A pattern that is slow in a hot path may be acceptable in initialization code

## Scan Workflow

### Phase 0: Determine Scan Scope

Parse arguments to determine what to scan:

```
Arguments:
- <pr_number>: Scan only files changed in PR (e.g., "123", "#123")
- <commit_sha>: Scan only files changed in commit (e.g., "abc123")
- "--all" or no args: Scan entire codebase
- "--scope [database|algorithm|frontend|resources|backend]": Focus on specific performance categories
If PR or commit specified, use Bash to get changed files:
```bash
# For PR
gh pr view <pr_number> --json files --jq '.files[].path'

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
### Phase 1: Project Technology Discovery

Explore the codebase to understand the project technology stack:

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track comprehensive scan progress across all 4 performance categories, consolidation, and report generation.

### Phase 3: Parallel Performance Scanning

Spawn **4 parallel Explore agents** for comprehensive performance analysis. Each agent targets specific performance categories using Grep patterns to find actual anti-patterns in code.

For detailed agent prompts and grep patterns for each performance category, see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1**: N+1 Queries & Database Performance
- **Agent 2**: Algorithmic Complexity & Computational Efficiency
- **Agent 3**: Frontend Bottlenecks (Bundle Size, Rendering, Network)
- **Agent 4**: Resource Leaks (Memory, Connections, File Handles)

Each agent must:
1. Grep for performance anti-patterns across files in scope
2. Read each match to verify context (hot path vs. cold path)
3. Extract exact code snippets (5-10 lines)
4. Explain why the code is a performance concern
5. Classify severity (Critical/High/Medium/Low)
6. Provide optimization recommendations (2-3 approaches)
7. Estimate performance impact where possible (e.g., "O(n²) → O(n log n)")

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. **Collect all findings** from the 4 parallel agents
2. **Deduplicate** - Remove duplicate findings across agents
3. **Prioritize by severity**:
 - **Critical**: N+1 queries in loops, O(n²+) on large datasets, memory leaks in long-running processes, unbounded resource allocation
 - **High**: Missing database indexes, synchronous blocking in async contexts, large bundle imports, connection pool exhaustion
 - **Medium**: Suboptimal queries, unnecessary re-renders, missing caching opportunities, inefficient data structures
 - **Low**: Minor optimization opportunities, style preferences with marginal impact
4. **Categorize by performance domain**: Group findings under Database, Algorithm, Frontend, Resources
5. **Statistics**: Count total issues, by severity, by category, files scanned vs files with issues
6. **Impact assessment**: Estimate overall performance impact and prioritize quick wins

### Phase 5: Generate Performance Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

### Phase 6: Verification & Quality Check

Before presenting report, verify:
1. Every finding has file path and line numbers
2. Every finding has actual code snippet (not placeholder)
3. Every finding has clear explanation of the performance impact
4. Every finding has 2-3 optimization approaches with examples
5. Statistics are accurate (counted, not estimated)
6. No duplicate findings
7. Severity ratings are justified with reasoning
8. Only scanned files within specified scope
9. No invented issues or false positives
10. Big O complexity claims are accurate
11. Profiling tool recommendations match the technology stack

## Usage

```bash
# Scan specific PR
review-perf 123
review-perf #456

# Scan specific commit
review-perf abc123def

# Scan entire codebase
review-perf --all
review-perf

# Focus on specific scope
review-perf --all --scope database
review-perf 123 --scope frontend
## Scope Options

- `database`: Focus on N+1 queries, missing indexes, inefficient queries, connection management
- `algorithm`: Focus on Big O complexity, data structure choices, unnecessary computation
- `frontend`: Focus on bundle size, rendering performance, network optimization, Core Web Vitals
- `resources`: Focus on memory leaks, connection pools, file handle management, thread safety
- `backend`: Focus on database + algorithm + resources (excludes frontend)

If no scope specified, perform comprehensive scan across all categories.

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md) - Detailed grep patterns and agent prompts for each performance category
- [references/report-template.md](references/report-template.md) - Full markdown report template with all sections

## What This Skill Does

- Identifies database query inefficiencies (N+1, missing indexes, full table scans)
- Analyzes algorithmic complexity and suggests optimal alternatives
- Detects frontend bottlenecks (bundle bloat, render thrashing, layout shifts)
- Finds resource leaks (memory, connections, file handles)
- Provides detailed explanations with Big O analysis
- Suggests multiple optimization approaches with code examples
- Generates comprehensive markdown report with profiling recommendations
- Prioritizes findings by severity and estimated impact

## What This Skill Does NOT Do

- Does not modify any code
- Does not automatically fix performance issues
- Does not commit changes
- Does not run runtime profiling or benchmarks
- Does not perform load testing
- Does not guarantee 100% performance issue detection

## Limitations

- **Static analysis only**: Cannot detect runtime-only performance issues
- **Pattern-based**: May miss context-specific performance problems
- **No runtime profiling**: Cannot measure actual execution time or memory usage
- **No load testing**: Cannot test performance under concurrent users
- **Estimates are approximate**: Big O analysis may not reflect real-world data sizes
- **Requires manual verification**: Profiling recommended for critical performance claims

## Performance References

- [Web Vitals](https://web.dev/vitals/) - Core Web Vitals metrics and thresholds
- [React Performance](https://react.dev/learn/render-and-commit) - React rendering optimization
- [Database Query Optimization](https://use-the-index-luke.com/) - SQL indexing and query patterns
- [Memory Management Best Practices](https://developer.chrome.com/docs/devtools/memory-problems/) - Memory leak detection
