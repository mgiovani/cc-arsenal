# Database and migrations

## Contents

- [Models and sessions](#models-and-sessions)
- [Migrations](#migrations)
- [Schema choices](#schema-choices)
- [Queries and writes](#queries-and-writes)
- [Row security](#row-security)
- [Tests and slow queries](#tests-and-slow-queries)

To create or run a migration, use the `db-migrate` skill. This file holds the rules a migration must follow.

## Models and sessions

Use SQLAlchemy with typed `Mapped[...]` columns for a new project. Entities live in the owning context's `models.py` and are the source of truth for the schema. A project that writes plain SQL with a driver and keeps a migration list does that on purpose, so keep its style.

- Set `nullable=` explicitly on every column and keep one naming convention for constraints in the base class.
- Open one pool for the process. Never open a connection per request.
- Open sessions through one helper, so tenant or user context is set at the start of the transaction and never leaks to the next caller.
- Behind a transaction-mode pooler, avoid named prepared statements, which vanish between requests. Use unnamed statements or session mode for that path.
- Keep a transaction short. Validate and call outside services before opening it. An HTTP call inside a transaction holds row locks for the length of the network call.

## Migrations

A migration is appended and never edited after it merges. Its version is its position in the chain. A fix is a new revision at the end.

- Autogenerate cannot see roles, grants or row policies, so add those by hand.
- Run `upgrade head` as its own deploy step. Never run it inside the app's startup hook, where every replica races and a failure takes the API down.
- Read the database URL from the settings object in `env.py`, not from an ini file.
- Open a revision on a populated table with `SET LOCAL lock_timeout`, so it fails fast instead of queueing behind traffic and blocking everything after it.
- Create and drop indexes on live tables with `CONCURRENTLY`. Configure the tool to run that revision without a wrapping transaction.
- Add a CHECK or foreign key to a big table as `NOT VALID`, then `VALIDATE CONSTRAINT` in a later step. A plain add scans every row under a strong lock.
- `ADD CONSTRAINT IF NOT EXISTS` is not valid Postgres. Check `pg_constraint` for the name and table first.
- A workflow engine that owns its own schema creates it itself. Do not write a revision for it.
- Test the downgrade path only where the project promises one.

## Schema choices

- Names are lowercase snake_case, unquoted. Name columns for meaning (`is_active`, `created_at`, `user_id`).
- Use `timestamptz` for every timestamp, `numeric` with scale for money, `text` unless a real length rule exists, and `boolean` for flags.
- Use identity columns for ids in one database, and `bigint` for anything that can grow past two billion. Use UUIDv7 for ids made across systems or exposed to clients, because random v4 keys scatter inserts on large tables. Check whether the server version has a native generator before adding an extension.
- Index every foreign key column. Postgres does not, and joins and cascading deletes then scan the child table.
- In a composite index, put equality columns first and the range column last. An index on `(status, created_at)` does not serve a filter on `created_at` alone.
- Use a partial index when hot queries repeat one predicate, and `INCLUDE` for columns you only select. Use GIN for JSONB containment and full-text, and a stored generated `tsvector` column rather than a leading-wildcard `LIKE`.
- Add `tenant_id` and a unique constraint on `(tenant_id, pk)` where child rows must reference a parent in the same tenant.
- Mutable entities carry audit timestamps through one mixin. An append-only table does not.

## Queries and writes

- Write a guarded transition as `UPDATE ... WHERE state = 'open' ... RETURNING`. Zero rows updated means a lost race or an invalid transition, and the caller handles it by name.
- Write idempotently with `INSERT ... ON CONFLICT` on a unique index: `DO UPDATE` when the latest value wins, `DO NOTHING` for write-once rows.
- Claim queue rows with a single statement using `FOR UPDATE SKIP LOCKED` and `RETURNING`.
- Fix an N+1 loop by passing an array and matching `= ANY(...)`, or by one join. Batch inserts at about a thousand rows a statement and use `COPY` for bulk loads.
- When locking several rows, lock them in one sorted order or change them in one statement. Mixed orders deadlock.
- Set `statement_timeout` with `SET LOCAL` inside a transaction. A plain `SET` sticks to a pooled connection and leaks into the next client.
- Select named columns. A row with big JSON attributes makes `SELECT *` expensive.
- Keyset pagination needs an index that matches the sort order. All sort columns share one direction, or each comparison is written out per column.
- A transaction-scoped advisory lock serves singleton jobs. A session-scoped lock sticks to a pooled connection.

## Row security

Where the project isolates tenants in the database, enable row-level security and force it, so the table owner is also subject. Application filters alone expose every row the first time one `WHERE` is forgotten.

- The application connects as a role that is neither superuser nor owner, with only the grants it needs. Group roles without login hold the grants, and login roles inherit them.
- Index each column a policy filters on, and wrap auth lookups in a scalar subselect so they run once per statement.
- A policy helper function lives in a private schema with an empty `search_path` and checks the caller itself. A security-definer function bypasses the policies on the tables it reads.
- Every new table gets a policy test case that runs as the application role. A test run as the owner passes while the application is exposed.

## Tests and slow queries

- Run database tests against a real Postgres in a disposable container. A mocked database proves nothing about locks, constraints or policies.
- Mark them `db`. They are part of the gate, so a missing database fails the run or is reported as not run, never as passed.
- Read a slow query with `EXPLAIN (ANALYZE, BUFFERS)`. It executes the statement, so wrap a write in a transaction and roll it back. A sequential scan on a large table points at a missing index, and an external merge sort points at too little `work_mem`.
- Enable `pg_stat_statements` and rank by total time first, then by mean time, then by call count. Reset the counters after a fix to measure it.
