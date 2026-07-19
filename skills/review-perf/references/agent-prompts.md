# Performance Review - Agent Prompts & Anti-Pattern Detection

Detailed grep patterns and agent prompts for each performance category. Load this reference when running Phase 3 parallel performance scanning.

**On a PR/commit review, `[FILES_LIST]` is the complete and only set of files any agent may grep or read** - never follow an import, a caller, or "related-looking" file outside it, even if the anti-pattern would clearly extend there. Each file in `[FILES_LIST]` carries its Phase 0 hunk ranges; every match below gets classified against them before being written up - see the "0." step added to each agent's "For each finding" list.

## Agent 1 - N+1 Queries & Database Performance

```
Agent 1 - Database Performance Analysis:
- prompt: "Scan for N+1 query patterns, missing indexes, and database inefficiencies in [FILES_LIST]:

**N+1 Query Patterns:**
Use Grep to search for:

*ORM Loop Queries (most critical):*
- for.*in.*\.all\(\)  (iterating over querysets then accessing relations)
- \.objects\.get\(.*for  (individual gets inside loops)
- for.*in.*find\(  (MongoDB finds in loops)
- \.findOne\(.*for  (individual finds in loops)
- for.*in.*\.query\(  (SQLAlchemy queries in loops)
- \.load\(.*forEach  (Hibernate lazy loading in iteration)
- await.*prisma\.\w+\.find.*for  (Prisma queries in loops)

*Missing Eager Loading:*
- \.all\(\) without select_related or prefetch_related (Django)
- \.find\(\) without populate or include (Mongoose/Prisma)
- \.createQueryBuilder without leftJoinAndSelect (TypeORM)
- without includes: or joins: (ActiveRecord)
- FetchType\.LAZY in @ManyToOne/@OneToMany without entity graph

*Inefficient Query Patterns:*
- SELECT \* FROM  (selecting all columns unnecessarily)
- \.count\(\).*\.all\(\)  (loading all records just to count)
- LIKE '%search%'  (leading wildcard prevents index usage)
- OR.*OR.*OR  (multiple OR conditions instead of IN clause)
- NOT IN.*SELECT  (correlated subqueries)
- ORDER BY.*RAND\(\)  (random ordering on large tables)
- DISTINCT without necessity

*Missing Index Indicators:*
- \.filter\(.*__contains  (text search without full-text index)
- \.where\(.*LIKE  (pattern matching without index)
- \.order_by\( on non-indexed columns
- frequent GROUP BY columns without index

*Connection Management:*
- connection\.open\( without corresponding close
- new.*Connection\( without pool usage
- createConnection without pool: true
- Missing connection pool configuration

For each finding:
0. On a PR/commit review, confirm the file is in [FILES_LIST]; if not, skip it entirely. Check whether the match's line falls inside one of that file's hunk ranges - if it's outside every hunk, it's pre-existing code, not a PR finding; route it to the separate pre-existing bucket instead of continuing this list
1. Read the file to verify context and trace the query pattern
2. Check if the query runs in a loop or is called per-request
3. Extract exact code snippet (5-10 lines) showing the anti-pattern
4. Estimate the query multiplication factor (e.g., N+1 where N = number of records)
5. Reference the specific ORM documentation for the fix

Return structured findings with:
- File path and line numbers
- Anti-pattern type (N+1, missing index, inefficient query, connection leak)
- Severity (Critical/High/Medium/Low)
- Code snippet
- Estimated impact (e.g., '100 records = 101 queries instead of 2')
- Fix recommendations (2-3 approaches with ORM-specific code examples)"
- subagent_type: "Explore"
```

## Agent 2 - Algorithmic Complexity & Computational Efficiency

```
Agent 2 - Algorithmic Complexity Analysis:
- prompt: "Scan for algorithmic complexity issues and computational inefficiencies in [FILES_LIST]:

**Quadratic and Worse Complexity (O(n²+)):**
Use Grep to search for:

*Nested Loops on Collections:*
- for.*for.*\.(includes|indexOf|find)\(  (nested search = O(n²))
- for.*in.*for.*in  (nested iteration)
- \.forEach\(.*\.forEach\(  (nested forEach)
- \.map\(.*\.filter\(  (map with filter inside = potential O(n²))
- \.find\(.*\.find\(  (nested find operations)
- while.*while  (nested while loops on data)

*Inefficient Search/Sort:*
- \.sort\(.*\.sort\(  (sorting already sorted or double sorting)
- \.indexOf\(.*for  (linear search in loop)
- \.includes\(.*for  (linear membership test in loop)
- Array\.from\(.*Set  (converting to set and back repeatedly)
- in\s+list  (Python 'in list' instead of 'in set' for membership)

*Unnecessary Recomputation:*
- Function calls with same args inside loops without caching
- \.split\(.*for  (splitting string repeatedly)
- new RegExp\( inside loops (compiling regex per iteration)
- JSON\.parse\(.*JSON\.stringify\(  (deep clone via serialization)
- \.keys\(\).*\.values\(\)  (iterating object twice)

**Inefficient Data Structure Usage:**
Use Grep to search for:
- Array used for frequent lookups (should be Set/Map/Object)
- Linear search where hash lookup would work
- Concatenating strings in loops (should use StringBuilder/join/array)
- +=.*string inside for/while (string concatenation in loop)
- list\.append.*for.*if.*in list  (O(n) membership test on list)

**Unnecessary Work:**
Use Grep to search for:
- Fetching data that is never used
- Computing values that are overwritten before use
- Loading entire files/datasets when only partial data needed
- \.readFileSync\( or \.readFile\( for large files without streaming
- Synchronous I/O in async contexts: readFileSync, writeFileSync
- sleep\(|time\.sleep\(|Thread\.sleep\( in request handlers

**Recursive Issues:**
- Recursive functions without memoization on overlapping subproblems
- No tail-call optimization on deep recursion
- Missing base case guards (potential stack overflow)

For each finding:
0. On a PR/commit review, confirm the file is in [FILES_LIST]; if not, skip it entirely. Check whether the match's line falls inside one of that file's hunk ranges - if it's outside every hunk, it's pre-existing code, not a PR finding; route it to the separate pre-existing bucket instead of continuing this list
1. Read the code to verify the complexity claim
2. Determine the expected data size (small/medium/large)
3. Calculate actual Big O complexity
4. Provide the optimal alternative complexity

Return structured findings with:
- File path and line numbers
- Current complexity (e.g., O(n²))
- Optimal complexity (e.g., O(n log n) or O(n))
- Severity based on data size and frequency
- Code snippet showing the anti-pattern
- Optimized code example with explanation"
- subagent_type: "Explore"
```

## Agent 3 - Frontend Bottlenecks (Bundle Size, Rendering, Network)

```
Agent 3 - Frontend Performance Analysis:
- prompt: "Scan for frontend performance bottlenecks in [FILES_LIST]:

**Bundle Size Issues:**
Use Grep to search for:

*Large Library Imports:*
- import.*from ['\"](lodash|moment|moment-timezone)['\"]  (should use lodash-es/date-fns)
- import.*from ['\"]@mui/  without specific path (barrel import)
- import \{.*\} from ['\"]antd['\"]  (should use antd/es/component)
- require\(['\"]lodash['\"]  (full lodash import)
- import.*from ['\"]\.\./\.\./.*index['\"]  (barrel file re-exports)

*Missing Code Splitting:*
- import .* from without React.lazy or dynamic import() for route components
- No next/dynamic usage for heavy components (Next.js)
- Large components without Suspense boundaries

*Unoptimized Assets:*
- <img.*src=.*\.(png|jpg|jpeg|bmp) without width/height or next/image
- No srcSet or sizes attributes on images
- Inline SVGs > 5KB without external file
- @import url\( for fonts (render-blocking)
- <link.*stylesheet without preload for critical CSS

**Rendering Performance:**
Use Grep to search for:

*React-specific:*
- useEffect\(\s*\(\)\s*=>\s*\{[^}]*setState  (state updates in effects causing re-renders)
- useMemo\(\s*\(\)\s*=>\s*\w+\s*,\s*\[\]  (useMemo with empty deps = should be constant)
- new Object\(\)|new Array\(\)|\[\]|\{\} in render/return (creating new references per render)
- \.map\(.*key=\{.*index  (using array index as key)
- useContext\( in frequently re-rendering components
- forceUpdate\(  (forcing re-renders)
- \.style\s*=\s*\{  (inline style objects causing re-renders)
- dangerouslySetInnerHTML  (bypasses virtual DOM diffing)

*Layout Thrashing:*
- offsetWidth|offsetHeight|getBoundingClientRect followed by style mutation
- getComputedStyle in loops
- scrollTop|scrollLeft reads mixed with writes

*DOM Manipulation:*
- document\.querySelector.*for  (DOM queries in loops)
- innerHTML\s*\+=  (repeated DOM manipulation instead of batch)
- createElement.*appendChild in loops without DocumentFragment

**Network Performance:**
Use Grep to search for:
- fetch\(|axios\.|\.get\(|\.post\( inside useEffect without debounce/throttle
- No AbortController for cancellable requests
- Missing cache headers or stale-while-revalidate
- Sequential await.*await.*await  (waterfall requests, should be Promise.all)
- await.*fetch.*await.*fetch  (sequential fetches that could be parallel)

**Web Vitals Impact:**
- Largest Contentful Paint: Large unoptimized hero images, render-blocking resources
- Cumulative Layout Shift: Missing width/height on images/ads, dynamic content injection
- Interaction to Next Paint: Long tasks on main thread, heavy event handlers

For each finding:
0. On a PR/commit review, confirm the file is in [FILES_LIST]; if not, skip it entirely. Check whether the match's line falls inside one of that file's hunk ranges - if it's outside every hunk, it's pre-existing code, not a PR finding; route it to the separate pre-existing bucket instead of continuing this list
1. Read the component/file to verify the rendering context
2. Assess impact on Core Web Vitals (LCP, CLS, INP)
3. Check if the component is in a critical rendering path
4. Estimate bundle size impact where applicable

Return structured findings with:
- File path and line numbers
- Performance category (Bundle/Rendering/Network/Web Vitals)
- Severity based on user-facing impact
- Code snippet showing the anti-pattern
- Optimized code example
- Estimated impact on Core Web Vitals"
- subagent_type: "Explore"
```

## Agent 4 - Resource Leaks (Memory, Connections, File Handles)

```
Agent 4 - Resource Leak Analysis:
- prompt: "Scan for resource leaks and management issues in [FILES_LIST]:

**Memory Leaks:**
Use Grep to search for:

*Event Listener Leaks:*
- addEventListener\( without corresponding removeEventListener
- \.on\( without corresponding \.off\( or \.removeListener\(
- \.subscribe\( without corresponding \.unsubscribe\( or cleanup
- useEffect.*addEventListener without cleanup return
- setInterval\( without clearInterval (especially in components/classes)
- setTimeout\( in recursive patterns without clear exit condition

*Object Accumulation:*
- \.push\( in long-running loops without bounds/cleanup
- global\.\w+\s*=|window\.\w+\s*= (global variable accumulation)
- cache\[|_cache\[|memo\[ without eviction/TTL/max-size
- Map\.set\(|WeakMap not used for DOM references
- static.*=.*\[\]|static.*=.*\{\} (static collections growing unbounded)
- module-level lists/dicts that grow without bounds

*Closure Leaks:*
- Closures capturing large objects or DOM references
- Callbacks referencing 'this' in classes that should be garbage collected
- Promise chains holding references to large data

**Connection Leaks:**
Use Grep to search for:

*Database Connections:*
- \.connect\( without \.close\( or \.end\( or \.release\(
- new Pool\( without proper shutdown handling
- getConnection\( without release in finally block
- createClient\( without disconnect in error paths
- Missing try/finally or context manager around connection usage

*HTTP Connections:*
- new.*Client\( without close/destroy
- \.createServer without graceful shutdown handler
- fetch\( without AbortController for long-running requests
- WebSocket connections without close handlers
- Missing connection timeout configuration

*Stream/File Handle Leaks:*
- \.createReadStream\(|\.createWriteStream\( without .on('error') and close
- open\( without close\( in finally/with block (Python)
- fopen\( without fclose\( (PHP/C)
- new FileInputStream without try-with-resources (Java)
- Missing 'with' statement for file operations (Python)

**Thread/Process Leaks:**
Use Grep to search for:
- new Thread\( without join or daemon=True
- ProcessPoolExecutor|ThreadPoolExecutor without shutdown
- spawn\(|fork\( without process management
- Worker threads without termination handling
- async tasks without await (fire and forget)

**Resource Pool Exhaustion:**
Use Grep to search for:
- Pool configuration with very high/no max limits
- Missing health checks on pooled connections
- No timeout on resource acquisition
- Blocking operations in async pools

For each finding:
0. On a PR/commit review, confirm the file is in [FILES_LIST]; if not, skip it entirely. Check whether the match's line falls inside one of that file's hunk ranges - if it's outside every hunk, it's pre-existing code, not a PR finding; route it to the separate pre-existing bucket instead of continuing this list
1. Read the file to trace resource lifecycle (acquire → use → release)
2. Verify that cleanup/release is missing or conditional
3. Check error handling paths (does the resource leak on exception?)
4. Assess the runtime context (long-running server vs. short script)

Return structured findings with:
- File path and line numbers
- Resource type (Memory/Connection/File Handle/Thread)
- Leak pattern (missing cleanup, missing error handling, unbounded growth)
- Severity based on runtime context and resource type
- Code snippet showing the leak
- Fix recommendations with proper resource management patterns (try/finally, context managers, RAII, cleanup functions)"
- subagent_type: "Explore"
```

## Performance Best Practices by Role

### For Developers
1. **Profile before optimizing**: Measure actual bottlenecks, don't guess
2. **Fix Critical/High first**: Prioritize based on measured impact
3. **Test performance fixes**: Verify improvements with benchmarks
4. **Consider data scale**: An O(n²) algorithm on 10 items is fine; on 10,000 items it's not
5. **Add performance tests**: Write benchmarks to prevent regressions

### For Frontend Engineers
1. **Measure Core Web Vitals**: Use Lighthouse, WebPageTest, or Chrome DevTools
2. **Bundle analysis**: Run webpack-bundle-analyzer regularly
3. **Lazy load routes**: Code-split at route boundaries
4. **Optimize images**: Use next/image, WebP/AVIF, responsive sizes
5. **Minimize re-renders**: Use React DevTools Profiler to identify wasted renders

### For Backend Engineers
1. **Use query logging**: Enable slow query logs and EXPLAIN ANALYZE
2. **Connection pooling**: Always use connection pools, never individual connections
3. **Eager loading**: Use prefetch_related/select_related/include to avoid N+1
4. **Caching strategy**: Cache expensive computations and frequent queries
5. **Resource cleanup**: Use context managers, try/finally, or RAII patterns

### For DevOps/SRE
1. **APM tooling**: Deploy application performance monitoring (DataDog, New Relic, Prometheus)
2. **Performance budgets**: Set and enforce bundle size limits in CI
3. **Database monitoring**: Track slow queries, connection pool usage, index effectiveness
4. **Memory monitoring**: Alert on memory growth trends, not just threshold
5. **Load testing**: Regular load tests to identify bottlenecks under concurrency

## Recommended Follow-up

1. **Runtime profiling**: Use language-specific profilers for actual measurements
2. **Load testing**: Use tools like k6, Artillery, or JMeter for concurrent user testing
3. **APM setup**: Deploy application performance monitoring for ongoing visibility
4. **Database tuning**: Run EXPLAIN ANALYZE on flagged queries
5. **Bundle analysis**: Run bundle analyzer for accurate size measurements

## Profiling Tool Recommendations

- **Python**: cProfile, py-spy, memory_profiler, django-debug-toolbar, SQLAlchemy logging
- **JavaScript/Node.js**: clinic.js, 0x, node --inspect, Chrome DevTools Performance tab
- **React**: React DevTools Profiler, why-did-you-render, @welldone-software/why-did-you-render
- **Java**: JProfiler, VisualVM, async-profiler, Spring Boot Actuator
- **Go**: pprof, trace, benchstat
- **Database**: EXPLAIN ANALYZE (PostgreSQL), EXPLAIN (MySQL), MongoDB explain(), pg_stat_statements
- **Frontend**: Lighthouse, WebPageTest, Chrome DevTools Performance, webpack-bundle-analyzer
- **Load Testing**: k6, Artillery, JMeter, Locust
