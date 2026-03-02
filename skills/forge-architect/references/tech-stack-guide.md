# Tech Stack Guide for SaaS Products

Recommended technology stacks for different types of SaaS products, with rationale and trade-offs.

---

## How to Use This Guide

1. Identify your product type (section headers below)
2. Review the recommended stack and alternatives
3. Check whether team has experience with the recommendation
4. Evaluate constraints (compliance, integrations, hosting preferences)
5. Document your choice in `docs/architecture.md` with rationale

---

## Stack 1: Full-Stack Next.js + Supabase (Most Common B2B SaaS)

**Best for**: B2B SaaS products with a web dashboard, user authentication, and standard CRUD operations. Strong choice for solo founders and small teams.

### Core Stack

| Layer | Technology | Version (as of 2025) | Notes |
|-------|-----------|----------------------|-------|
| Frontend framework | Next.js | 15.x | App Router, Server Components |
| UI components | shadcn/ui + Tailwind CSS | Latest | Built on Radix UI |
| Backend | Next.js API Routes or Fastify | — | Route handlers in App Router |
| Database | PostgreSQL via Supabase | — | Managed, includes auth + storage |
| Auth | Clerk or Supabase Auth | — | Clerk for more features; Supabase for simplicity |
| Payments | Stripe | — | Subscriptions + one-time payments |
| Email | Resend | — | Developer-friendly, great docs |
| File storage | Supabase Storage or Cloudflare R2 | — | R2 for no egress fees |
| Deployment | Vercel | — | Zero-config, preview environments |
| Background jobs | Inngest or Trigger.dev | — | Serverless-friendly job queues |

### When to Choose This Stack

- ✅ Web-based B2B dashboard product
- ✅ Team is familiar with React/TypeScript
- ✅ Product needs auth, multi-tenancy, file storage
- ✅ Want to move fast with managed infrastructure
- ✅ Budget-conscious (generous free tiers across all tools)
- ❌ Real-time collaboration is a core feature (explore Liveblocks or Ably)
- ❌ Heavy computation or ML inference required
- ❌ Need to deploy on-premise for compliance

### Key Decisions

**App Router vs. Pages Router**: Always App Router for new projects (better performance, server components).

**Clerk vs. Supabase Auth**:
- Clerk: Better UI components, organization management, B2B SSO support
- Supabase Auth: Simpler, one less vendor, tightly integrated with Supabase RLS

**Inngest vs. Trigger.dev vs. Quirrel**:
- Inngest: Best for event-driven workflows, great DX
- Trigger.dev: Better for long-running jobs, has UI for monitoring
- pg-boss: Good if you want to avoid additional vendors and already use PostgreSQL

---

## Stack 2: Python FastAPI + PostgreSQL (API-First or Data-Heavy Products)

**Best for**: Products with complex server-side logic, data processing pipelines, ML/AI features, or where the team is Python-native.

### Core Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend framework | FastAPI | Async, fast, excellent auto-docs |
| Database | PostgreSQL | Via SQLAlchemy 2.0 + Alembic migrations |
| ORM | SQLAlchemy 2.0 | Or SQLModel for Pydantic integration |
| Auth | FastAPI-Users or custom JWT | |
| Background jobs | Celery + Redis or ARQ | ARQ for lighter async workloads |
| API validation | Pydantic v2 | Built into FastAPI |
| Testing | pytest + httpx | |
| Frontend | Next.js or React (separate) | Deployed separately from API |
| Deployment | Railway, Fly.io, or AWS ECS | Not serverless-friendly (startup time) |
| Container | Docker + docker-compose | |

### When to Choose This Stack

- ✅ Team is Python-native
- ✅ Heavy data processing, ETL, or ML features
- ✅ Need to use Python ML/AI libraries (scikit-learn, PyTorch, LangChain)
- ✅ Complex domain logic better expressed in Python
- ✅ Building an API product (not primarily a web UI)
- ❌ Team primarily knows JavaScript
- ❌ Need serverless deployment (FastAPI cold starts are slow)
- ❌ Very simple CRUD; Next.js stack would be faster to develop

### Key Decisions

**SQLAlchemy vs. SQLModel vs. raw SQL**:
- SQLAlchemy 2.0: Most mature, best async support, complex but powerful
- SQLModel: Combines SQLAlchemy + Pydantic, simpler but less flexible
- Raw SQL with asyncpg: Best performance, more boilerplate

**Celery vs. ARQ vs. Dramatiq**:
- Celery: Most feature-rich, best for complex workflows, heavier
- ARQ: Lightweight async Redis queue, simpler, good for most use cases
- Dramatiq: Simple, reliable, good middle ground

---

## Stack 3: Node.js + Express/Fastify (Custom Backend with React Frontend)

**Best for**: Products that want full control over the backend without Next.js conventions, or where the API will be consumed by multiple clients (web, mobile, integrations).

### Core Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Fastify or Express + TypeScript | Fastify: faster; Express: more ecosystem |
| ORM | Prisma or Drizzle | Prisma: great DX; Drizzle: more SQL control |
| Auth | Lucia, Better Auth, or custom JWT | |
| Frontend | React + Vite or Next.js | Separate deployment |
| Database | PostgreSQL | |
| Background jobs | BullMQ (Redis) or pg-boss | |
| Deployment | Railway, Fly.io, Render | |

### When to Choose This Stack

- ✅ Need separate API consumed by web + mobile
- ✅ Want more control than Next.js API routes provide
- ✅ Building real-time features (WebSockets easier with dedicated server)
- ✅ Team prefers separation of frontend and backend
- ❌ Want the simplest possible deployment (Next.js monorepo is simpler)
- ❌ Solo founder; too much initial setup

---

## Stack 4: Go + PostgreSQL (High-Performance APIs)

**Best for**: Infrastructure tools, developer tools, APIs needing very high throughput with minimal resource usage.

### Core Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Go + Chi or Gin | Chi: minimal; Gin: more batteries |
| Database | PostgreSQL + pgx | pgx is the best Go PostgreSQL driver |
| Auth | Custom JWT or Ory Kratos | |
| Frontend | React (separate) | |
| Deployment | Fly.io, Railway, or Kubernetes | |

### When to Choose This Stack

- ✅ Team knows Go
- ✅ Need high throughput with minimal compute cost
- ✅ Building a CLI tool, developer tool, or infrastructure product
- ✅ Low latency is critical
- ❌ Team doesn't know Go (steep learning curve vs. speed gain)
- ❌ Need to iterate UI quickly (Go web UIs are more complex)
- ❌ Heavy data processing (Python has better ML ecosystem)

---

## Database Selection Guide

### PostgreSQL (Default Choice)

Use PostgreSQL for almost all SaaS products. It is:
- Mature, battle-tested, and extremely reliable
- Excellent for relational data (which most SaaS products have)
- Supports JSON/JSONB for flexible fields
- Row-Level Security for multi-tenancy
- Full-text search built in (good enough for most products)
- Available as managed service everywhere (Supabase, Neon, RDS, Cloud SQL)

**When NOT to use**: Document-centric data (nested, schema-less) or time-series data.

### Redis

Use Redis as a secondary store for:
- Session data and JWT revocation lists
- Cache (cache-aside pattern)
- Rate limiting counters
- Job queue backend (BullMQ, Sidekiq)
- Pub/Sub for real-time features
- Leaderboards and sorted sets

**Never use as primary store**: Redis is in-memory; data is not durable without persistence config.

**Managed options**: Upstash (serverless, per-command pricing), Redis Cloud, ElastiCache.

### SQLite

Consider SQLite for:
- Edge computing (Cloudflare D1, Turso)
- CLI tools and desktop apps
- Single-tenant products (one database per customer)
- Development and testing environments

**Turso + LibSQL**: SQLite with multi-region replication. Good for latency-sensitive products.

### MongoDB / Document DB

Use only if:
- Data is genuinely document-structured with highly variable schema
- You have experience with MongoDB; it's not simpler than PostgreSQL

For most "flexible data" needs, PostgreSQL JSONB is sufficient.

---

## Authentication Comparison

| Provider | Best For | Pros | Cons | Cost |
|----------|---------|------|------|------|
| **Clerk** | B2B with org management | Polished UI, org support, B2B SSO, dev-friendly | Vendor lock-in, cost at scale | Free to $25+/mo |
| **Supabase Auth** | Supabase projects | Built-in RLS integration, no extra vendor | Less feature-rich than Clerk | Included in Supabase |
| **Auth0** | Enterprise compliance | SOC2, HIPAA, broad compliance | Complex, expensive at scale | Expensive |
| **Better Auth** | Full control | Open source, self-hostable, TypeScript-first | Self-managed ops | Free (self-hosted) |
| **Lucia** | Custom auth | Full control, no vendor lock | More boilerplate to write | Free |
| **NextAuth.js / Auth.js** | Next.js + OAuth | Many social providers, good Next.js integration | Session-based, less B2B features | Free |

**Recommendation for most B2B SaaS**: Clerk for speed; Better Auth if you want to self-host and avoid vendor lock-in.

---

## Email Service Comparison

| Provider | Best For | Pros | Cons |
|----------|---------|------|------|
| **Resend** | Developer-first products | Great API, React Email templates, good DX | Newer, smaller ecosystem |
| **SendGrid** | High volume transactional | Battle-tested, high deliverability | Complex UI, pricing can surprise |
| **Postmark** | Transactional email | Best deliverability, simple API | Higher cost per message |
| **AWS SES** | High volume, cost-sensitive | Very cheap at scale | Difficult setup, manual DNS config |
| **Loops** | Marketing + transactional | Beautiful editor, sequences, analytics | Less flexible for transactional |

**Recommendation**: Resend for most new products (great DX, free tier, React Email support).

---

## Hosting / Deployment Comparison

| Platform | Best For | Pros | Cons | Cost Model |
|----------|---------|------|------|-----------|
| **Vercel** | Next.js apps | Zero-config, instant deploy, edge network | Serverless constraints, expensive at compute scale | Per usage |
| **Railway** | Any Docker app | Easy deploys, persistent servers, databases | Less global CDN | Per usage |
| **Fly.io** | Persistent servers globally | Multi-region, low latency, good for WebSockets | More configuration | Per usage |
| **Render** | Simple persistent servers | Easy Postgres, cron jobs | Slower cold starts on free tier | Per service |
| **AWS/GCP/Azure** | Enterprise scale | Full control, compliance, any workload | High complexity, requires DevOps expertise | Per usage |
| **Cloudflare** | Edge workers, static sites | Global edge, R2 storage, zero egress | Worker constraints (no file system) | Per usage |

**Recommendation**:
- Next.js product → Vercel (frontend) + Railway/Fly.io (API if needed)
- Python/Go API → Railway or Fly.io
- High scale / compliance → AWS with managed services

---

## Quick Stack Decision Guide

```
Is your team primarily Python engineers?
  YES → FastAPI + PostgreSQL + Celery (Stack 2)
  NO  → Continue

Is real-time collaboration a core feature?
  YES → Next.js + Supabase + Liveblocks/Ably
  NO  → Continue

Do you want the fastest path to MVP?
  YES → Next.js + Supabase + Clerk (Stack 1)
  NO  → Continue

Do you need separate web and mobile clients?
  YES → Fastify/Express API + React Frontend (Stack 3)
  NO  → Next.js + Supabase (Stack 1)

Do you need very high throughput with minimal cost?
  YES → Go + PostgreSQL (Stack 4)
  NO  → Next.js + Supabase (Stack 1)
```
