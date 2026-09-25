# Performance Review - Report Template

Use this template when generating the performance report in Phase 5.

## Report Format

```markdown
# Performance Review Report

| Field | Value |
| --- | --- |
| Scope | [PR #123 \| Commit abc123 \| Entire Codebase] |
| Date | [YYYY-MM-DD] |
| Technology Stack | [e.g., Next.js 14 + PostgreSQL + Prisma] |
| Files Scanned | [N files - on a PR/commit review, this is exactly the diff's changed-file list, never more] |
| Total Findings | [N performance issues - main findings only, excludes the Pre-existing Issues section] |

## Executive Summary

[2-3 sentence overview of performance posture, most critical bottlenecks, and estimated impact]

## Severity Breakdown

| Severity | Findings | Meaning |
| --- | --- | --- |
| Critical | N | Significant performance degradation, likely user-facing impact |
| High | N | Notable inefficiency, should be addressed before scaling |
| Medium | N | Optimization opportunity with measurable improvement potential |
| Low | N | Minor optimization, marginal impact |

## Findings by Performance Category

For every finding, whatever the category, provide a fields table (Severity, Type, File, and either Description or the category-specific fields shown below), the offending code snippet in a fenced block matching its language, and a numbered fix list with one entry marked Recommended. The examples below show one filled-in finding per category; add one such block per finding actually found.

### Database Performance (N findings)

#### Finding 1: [Issue Title]

| Field | Value |
| --- | --- |
| Severity | Critical |
| Type | N+1 Query |
| File | `path/to/file.py:45-60` |
| Description | [What the performance issue is and why it matters] |
| Impact analysis | [Quantified impact, e.g., "For 100 users, this generates 101 database queries instead of 2. At 1ms per query, this adds ~100ms latency per request."] |
| Profiling recommendation | [How to measure actual impact, e.g., "Enable Django DEBUG toolbar or add SQL query logging to verify query count"] |

```python
[Actual N+1 query code]
```

Fix options:
1. Recommended: [description with optimized code example]
2. Alternative: [alternative approach with code example]
3. Alternative: [another alternative if applicable]

### Algorithmic Complexity (N findings)

#### Finding 1: [Issue Title]

| Field | Value |
| --- | --- |
| Severity | High |
| Type | Quadratic Complexity |
| File | `path/to/file.ts:120-135` |
| Current complexity | O(n²) |
| Optimal complexity | O(n) or O(n log n) |
| Impact analysis | [Quantified impact, e.g., "At 1,000 items: ~1M operations. At 10,000 items: ~100M operations. Using a Set reduces to ~10,000 operations."] |

```typescript
[Actual quadratic-complexity code]
```

How to fix it:
1. Recommended: [optimized algorithm with code example]
2. Alternative: [alternative data structure approach]

### Frontend Bottlenecks (N findings)

#### Finding 1: [Issue Title]

| Field | Value |
| --- | --- |
| Severity | High |
| Type | Bundle Size / Rendering / Network |
| File | `path/to/component.tsx:30-45` |
| Web Vital impact | [LCP / CLS / INP affected] |
| Impact analysis | [Quantified impact, e.g., "Importing full lodash adds ~70KB to bundle. Using lodash-es/get adds ~2KB."] |
| Measurement | [How to verify, e.g., "Run `npx webpack-bundle-analyzer` to confirm bundle size reduction"] |

```tsx
[Actual offending component code]
```

Fix approaches:
1. Recommended: [optimized code with code example]
2. Alternative: [alternative approach]

### Resource Leaks (N findings)

#### Finding 1: [Issue Title]

| Field | Value |
| --- | --- |
| Severity | Critical |
| Type | Memory Leak / Connection Leak / File Handle Leak |
| File | `path/to/service.js:80-95` |
| Impact analysis | [Quantified impact, e.g., "Each request opens a database connection without releasing it. Under 100 concurrent users, the connection pool (default 10) will be exhausted in seconds."] |

```javascript
[Actual leak site code]
```

Cleanup approaches:
1. Recommended: [proper resource management with code example]
2. Alternative: [alternative approach]

## Pre-existing Issues Noticed in Touched Files (outside this PR's changes)

[Only on a PR/commit review, and only if non-empty - omit this section entirely otherwise. Same format as Findings above, but these are issues found in the diff hunks' surrounding files that were NOT introduced by this PR/commit (line number falls outside every hunk). Excluded from the Severity Breakdown and Performance Impact Summary counts below.]

#### Finding 1: [Issue Title]

| Field | Value |
| --- | --- |
| Severity | [Critical/High/Medium/Low] |
| File | `path/to/touched-file.py:12-18` (outside this PR's diff hunks) |
| Note | Pre-existing: not introduced by this PR/commit, flagged for awareness only |

```python
[Actual pre-existing code]
```

[Repeat for each pre-existing finding...]

## Performance Impact Summary

| Category | Critical | High | Medium | Low | Top Issue |
|----------|----------|------|--------|-----|-----------|
| Database | N | N | N | N | [Brief description] |
| Algorithm | N | N | N | N | [Brief description] |
| Frontend | N | N | N | N | [Brief description] |
| Resources | N | N | N | N | [Brief description] |
| Total | N | N | N | N | |

## Recommendations by Priority

### Immediate Action Required (Critical/High)
1. [Finding reference] - [Brief action item with expected improvement]
2. [...]

### Short-term Improvements (Medium)
1. [Finding reference] - [Brief action item with expected improvement]
2. [...]

### Long-term Enhancements (Low)
1. [Finding reference] - [Brief action item]
2. [...]

## Quick Wins

List 3-5 changes that are easy to implement and have high impact:

1. [Title]: [1-2 sentence description], expected improvement: [estimate]
2. [...]

## Profiling Recommendations

Based on the technology stack and findings, run these profiling tools to get accurate measurements:

| Area | Recommendation |
| --- | --- |
| Database | [Tool-specific recommendation based on detected stack]. Enable slow query logging with threshold [recommended ms]. Run EXPLAIN ANALYZE on queries identified in findings. |
| Application | [Language-specific profiler recommendation]. Focus on [specific endpoints/functions identified]. |
| Frontend | [Frontend-specific tool recommendation]. Run a Lighthouse audit in incognito mode, and measure Core Web Vitals in production with real user monitoring (RUM). |
| Load testing | [Load testing tool recommendation]. Test scenarios [based on findings, e.g., "concurrent user list loading to expose N+1 impact"]. |

## Monitoring Recommendations

To prevent performance regressions:

| Area | Recommendation |
| --- | --- |
| Performance budgets | Set bundle size limit at [X]KB, page load at [X]ms |
| Query monitoring | Alert when queries exceed [X]ms or count exceeds [X] per request |
| Memory monitoring | Track memory growth over time, alert on sustained increases |
| CI integration | Add Lighthouse CI or similar for automated performance checks |

---

Next steps: profile the Critical/High findings to measure actual impact, implement quick wins first, then address remaining findings by severity.
```

## Example Output

```
Performance Review Report

**Scope**: PR #123 (8 files changed)
**Technology Stack**: Next.js 14 + PostgreSQL + Prisma
**Files Scanned**: 8 files
**Total Findings**: 9 performance issues

Severity Breakdown:
- Critical: 1 finding
- High: 3 findings
- Medium: 4 findings
- Low: 1 finding

Top Critical Finding:
N+1 Query in user_service.py:45
  Loading user profiles in a loop triggers 1 query per user.
  For 100 users: 101 queries (1 list + 100 individual).
  Fix: Use prefetch_related('profile'), reduces to 2 queries.

Quick Wins:
1. Add select_related to user list endpoint, saves ~100 queries/request
2. Replace lodash with lodash-es, saves ~68KB bundle size
3. Add React.memo to UserCard component, eliminates ~50 unnecessary re-renders

[Full detailed report follows...]
```
