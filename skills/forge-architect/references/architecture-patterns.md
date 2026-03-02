# SaaS Architecture Patterns

Common architectural patterns for SaaS products with trade-offs and when to use each.

---

## Pattern 1: Modular Monolith (Recommended Starting Point)

**Description**: A single deployable application organized into well-defined internal modules with clear boundaries. Not a big ball of mud — modules have explicit interfaces and can be extracted later.

**Structure**:
```
app/
├── modules/
│   ├── auth/          # Authentication & authorization
│   ├── billing/       # Subscription & payments
│   ├── users/         # User management
│   ├── [core domain]/ # Your product's core feature
│   └── notifications/ # Email, push, webhooks
├── shared/            # Shared utilities, types, database client
└── api/               # HTTP layer (routes, middleware)
```

**When to use**:
- Team size: 1–20 engineers
- Product stage: MVP through Series A
- Use case: Most B2B SaaS products

**Pros**:
- Simple deployment (one process, one database)
- Easy to debug (single process, same logs)
- Fast to develop (no network overhead between modules)
- Easy to refactor and move code
- Low operational overhead (no service mesh, no distributed tracing needed)

**Cons**:
- All modules must scale together (can't scale billing independently from core)
- A bug in one module can crash the whole app
- Tight coupling risk if discipline is not maintained
- Database becomes a single point of failure

**When to evolve**: When you have ≥5 engineers per module, or when one module needs 10x more scale than others.

---

## Pattern 2: Monolith + Background Workers

**Description**: A monolith for synchronous operations + separate worker processes for async jobs. The most common production SaaS architecture.

**Structure**:
```
web/        # Handles HTTP requests
workers/    # Processes background jobs
shared/     # Common code and database client
jobs/
├── send-email.job.ts
├── process-payment.job.ts
├── generate-report.job.ts
└── sync-integration.job.ts
```

**Message queue options**:
- **Redis + BullMQ** (Node.js): Simple, no extra infra if Redis already used
- **Redis + Sidekiq** (Ruby): Battle-tested, excellent monitoring UI
- **PostgreSQL + pg-boss**: No extra infrastructure, durable, great for smaller workloads
- **Amazon SQS / Google Pub-Sub**: Managed, scales infinitely, costs more

**When to use**:
- Any product with: email sending, PDF generation, third-party syncs, scheduled tasks, webhook delivery, file processing

**Pros**:
- Non-blocking: Web requests return immediately
- Retry logic built in
- Work can be distributed across multiple worker instances
- Workers can scale independently from web

**Cons**:
- More complexity than pure monolith
- Requires monitoring two process types
- Debugging async flows requires correlation IDs
- Queue can back up if workers are slow

---

## Pattern 3: Serverless / Functions

**Description**: No persistent server; compute is triggered per-request. Deploy as individual functions (AWS Lambda, Vercel Functions, Cloudflare Workers).

**Structure**:
```
pages/api/         # Vercel API routes (Next.js)
functions/         # Individual serverless functions
edge-functions/    # Ultra-fast, runs at edge CDN nodes
```

**When to use**:
- Low and variable traffic (serverless scales to zero when idle)
- Simple CRUD operations
- Event-driven workflows (webhooks, file uploads)
- Next.js-based products where Vercel is the deployment target

**Pros**:
- Pay per invocation (cheap at low volume)
- Auto-scales without configuration
- No server management
- Zero-downtime deploys by default

**Cons**:
- Cold start latency (50–2000ms depending on runtime)
- Execution time limits (typically 10–30 seconds)
- Difficult to run long-running jobs
- Stateless by nature (no in-memory caching between requests)
- Debugging is harder (no SSH, logs can be fragmented)
- Database connections need careful pooling (use PgBouncer or Supabase connection pooler)

**When NOT to use**:
- Products with long-running jobs (video processing, ML inference, large reports)
- WebSocket / real-time features (though edge workers partially solve this)
- High-frequency operations where cold starts matter

---

## Pattern 4: Frontend + Managed Backend (BaaS)

**Description**: Lightweight frontend that talks directly to a managed backend-as-a-service for database, auth, storage, and real-time. No custom backend server.

**Common BaaS choices**:
- **Supabase**: PostgreSQL + Auth + Storage + Realtime. Open source, can self-host.
- **Firebase**: Firestore + Auth + Storage + Functions. Google Cloud. Document DB model.
- **PocketBase**: Single-binary Go server with auth, DB, files. Good for small apps.

**Structure**:
```
src/
├── components/   # UI components
├── pages/        # Routes
├── lib/
│   └── supabase.ts  # Supabase client
└── hooks/        # Data fetching hooks
```

**When to use**:
- Solo founders or very small teams
- Products where real-time sync is a core feature
- Products where Supabase/Firebase feature set is sufficient
- Rapid prototyping / MVPs

**Pros**:
- Extremely fast to build (auth, storage, realtime out of the box)
- Low operational overhead
- Built-in row-level security (Supabase)
- Real-time subscriptions without extra infrastructure

**Cons**:
- Vendor lock-in (especially Firebase)
- Complex business logic is hard to hide from client
- RLS rules can become complex and hard to test
- Scaling costs can be high at volume
- Limited customization of auth flows, email templates

**When NOT to use**:
- Products with complex server-side business logic
- Products needing custom compliance requirements
- Products where data model doesn't fit document (Firebase) or basic SQL

---

## Pattern 5: Microservices

**Description**: Independent, separately-deployed services communicating over HTTP or message queues.

**When to use**:
- Team size: 50+ engineers, multiple independent teams
- Product stage: Late Series B / Series C and beyond
- Use case: When specific services have very different scaling needs

**Why you should NOT start with microservices**:
- Distributed systems are fundamentally harder to debug
- Network failures between services are common; must design for partial failures
- Requires DevOps maturity (container orchestration, service mesh, distributed tracing)
- Latency for inter-service calls adds up
- Maintaining API contracts across teams requires governance
- Much higher operational overhead

**If you still want to explore**: Start with a modular monolith. Extract services only when a specific module's scale requirements justify it.

---

## Multi-Tenancy Patterns

### Shared Database, Shared Schema (Row-Level)

All tenants in the same tables, isolated by `organization_id` column.

```sql
-- Every query must include org filter
SELECT * FROM documents WHERE organization_id = $1;

-- PostgreSQL Row-Level Security
CREATE POLICY tenant_isolation ON documents
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

**Pros**: Simple, cheap, easy to develop
**Cons**: One miscoded query can expose another tenant's data; noisy neighbor risk

**Best for**: Most B2B SaaS startups; strong with PostgreSQL RLS

### Shared Database, Separate Schemas

Each tenant gets their own PostgreSQL schema.

```sql
-- Tenant A
SELECT * FROM acme_corp.documents;

-- Tenant B
SELECT * FROM globex.documents;
```

**Pros**: Strong isolation, easier to migrate individual tenant data
**Cons**: Schema migrations must run for every tenant; limits practical tenant count

**Best for**: Dozens to hundreds of enterprise customers with strict isolation requirements

### Separate Databases per Tenant

Each tenant has their own database or database cluster.

**Pros**: Maximum isolation; can be in different regions/clouds per tenant requirements
**Cons**: Extremely high operational overhead; expensive; hard to query across tenants

**Best for**: Heavily regulated industries (healthcare, finance) or enterprise-only products with strict compliance

---

## Real-Time Patterns

### Polling

Client requests data on a timer.

```javascript
setInterval(async () => {
  const data = await fetchLatestData();
  setState(data);
}, 5000);
```

**Use when**: Updates are infrequent; latency of 5–30s is acceptable; team unfamiliar with WebSockets.

### Server-Sent Events (SSE)

Server pushes one-directional stream to client.

```javascript
// Server
res.setHeader('Content-Type', 'text/event-stream');
res.write(`data: ${JSON.stringify(update)}\n\n`);

// Client
const source = new EventSource('/api/stream');
source.onmessage = (e) => setState(JSON.parse(e.data));
```

**Use when**: Server-to-client only (notifications, live feeds, progress updates). Simpler than WebSockets.

### WebSockets

Full-duplex bidirectional connection.

**Use when**: Client must also send real-time data (collaborative editing, chat, live cursor positions). More complex; use managed service (Ably, Pusher, Supabase Realtime) unless you need control.

---

## Caching Patterns

### Cache-Aside (Lazy Loading)

Read from cache; on miss, read from DB and populate cache.

```python
def get_user(user_id):
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    user = db.query("SELECT * FROM users WHERE id = $1", user_id)
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user
```

**Use for**: Frequently read, infrequently written data (user profiles, org settings).

### Write-Through

Write to cache and DB simultaneously.

**Use for**: Data where cache miss is unacceptable (session data, rate limit counters).

### Cache Invalidation Strategy

**Time-based (TTL)**: Set expiry and let it expire naturally. Simple, but data may be stale.
**Event-based**: Invalidate cache when data changes. Accurate, more complex.
**Version keys**: Append version to cache key (`user:123:v2`). Effective for config-style data.

---

## Database Connection Patterns

### Connection Pooling

Serverless and high-concurrency apps must pool database connections.

- **PgBouncer**: Dedicated pooler for PostgreSQL; most configurable
- **Supabase connection pooler**: Built-in; use for Supabase projects
- **Prisma Accelerate**: Edge-compatible pooler for Prisma ORM users

**Pool sizing formula**: `connections = (core_count * 2) + effective_spindle_count`
For most web workloads, 10–25 connections per database is sufficient at startup.

---

## Choosing a Pattern: Decision Tree

```
Start here: What is your team size?

1–5 engineers → Modular Monolith (Pattern 1) or BaaS (Pattern 4)
5–20 engineers → Modular Monolith + Workers (Pattern 2)
20–50 engineers → Modular Monolith + Workers, extract 1–2 services if needed
50+ engineers → Consider Microservices (Pattern 5) per-team

Does your product need real-time?
- No → Standard polling is fine
- Yes, server-to-client → Server-Sent Events
- Yes, bidirectional → WebSockets (use managed service)

Is your traffic predictable?
- Yes, steady → Traditional server (Railway, Fly.io)
- No, very spiky → Serverless / Functions (Vercel, AWS Lambda)
```
