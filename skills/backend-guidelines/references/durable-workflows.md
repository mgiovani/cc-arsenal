# Durable workflows

## Contents

- [When to use one](#when-to-use-one)
- [Determinism and steps](#determinism-and-steps)
- [Retries, timeouts and idempotency](#retries-timeouts-and-idempotency)
- [Queues and schedules](#queues-and-schedules)
- [Lifecycle and deployment](#lifecycle-and-deployment)
- [Recovery and control](#recovery-and-control)
- [Testing](#testing)

These rules assume DBOS Transact on Postgres, the owner's engine. Another engine shares the determinism and idempotency rules.

## When to use one

Use a workflow when work must survive a restart: multi-step jobs, retries with backoff, schedules, queues with limits, human approval waits. Plain code covers everything else.

Use the engine's own primitives. A queue replaces a thread pool, `DBOS.sleep` replaces `time.sleep` and timer threads, step retries replace a retry loop, and a debouncer replaces a hand-built timer. The hand-rolled versions lose their state on a crash.

Never generate the retired forms: the old `transaction` decorator and `sql_session`, the in-memory `Queue(...)` class, the `scheduled` decorator, and the framework hooks on the `DBOS` constructor. Use datasources, `register_queue`, `apply_schedules` and the framework's own lifespan.

## Determinism and steps

On recovery the engine replays the workflow body and reuses saved step results. The body must therefore make the same decisions every time.

- The workflow body only orchestrates. Put each external call, file read, random draw, clock read and database query in a step or a datasource transaction.
- Start no threads, call no `time.sleep`, and write no module-level globals from a workflow or step. Keep shared state in the database through events, messages and streams.
- A step is leaf work. Do not start workflows or call `recv` from inside one.
- Run a concurrent sequence as a child workflow. If you start steps concurrently, start them in a fixed order and then gather them.
- Workflow inputs, outputs and step results must serialize. The default format is Python-only, so use the portable JSON format for data another language reads.
- Write database rows through a datasource transaction so each runs exactly once. Raw SQL in a workflow body runs again on recovery.
- To write rows and enqueue work atomically, use `enqueue_in_transaction` on the same connection. Two commits can orphan work if the process dies between them.

## Retries, timeouts and idempotency

- Retries are off unless `retries_allowed=True`. Setting `max_attempts` alone does nothing, and `max_attempts` counts the first try.
- Declare retries on the step and never loop with sleeps around it. Skip permanent failures with `should_retry`, such as a 4xx or a validation error, so a rejected request does not burn every attempt.
- When all attempts fail, the caller gets `DBOSMaxStepRetriesExceeded`, not the original exception.
- A step timeout needs an async step. A sync step cannot be preempted and rejects it.
- Make a start idempotent by wrapping it in `SetWorkflowID` with a business key such as the order id. For a webhook, pass the provider's event id as the `idempotency_key` on `send`.
- In an enqueue handler, catch `DBOSQueueDeduplicatedError` and answer "already in progress" instead of a 500.
- Bound every run with `SetWorkflowTimeout`. It survives restarts and cancels child workflows. Every agent or retry loop has a hard maximum.

## Queues and schedules

- Bound fan-out with a queue. A loop that calls `start_workflow` per item gives unbounded concurrency.
- Prefer `worker_concurrency`, per process, over `global_concurrency`, which also counts pending runs from older versions. Add a `limiter` for a rate-limited API, because it holds across every process.
- Partition a queue by tenant key when one tenant must not starve the rest. Once partitioned, every enqueue passes the key, or the run waits forever.
- Register queues after launch. Re-registering at startup overwrites runtime changes unless you pass the policy that keeps them.
- Enqueue and start by workflow name and queue name from other processes.
- Apply schedules at startup with `apply_schedules`. It upserts by name but replaces the whole definition, so pass every field every time. Name the schedule and its cron in `Final` constants.
- Cron runs in UTC unless the schedule names a zone. Missed runs are not backfilled unless asked. A schedule keeps firing until it is deleted.

## Lifecycle and deployment

- Configure and launch in `main` or the app's lifespan, never at import time. Launch before serving or running schedules.
- Set an explicit application version for a new app. An omitted version is a hash of the source and changes with every edit. Change an existing app's version only as a deployment decision, from the build's commit hash.
- Read the system database URL from settings. Point Postgres at the psycopg driver.
- Behind a transaction-mode pooler, set `use_listen_notify=False` before the system database is first created. Otherwise notifications drop silently and `recv` and `get_event` block forever.
- Run engine migrations as a privileged step and launch the application role with `run_migrations=False`.
- Use one database pool for steps. Never create a second engine per step.
- Shut down through one helper called from the lifespan.
- Split API and workers. The API process uses `DBOSClient` to enqueue and read, and destroys the client in a `finally`. Worker processes run the engine and dequeue. Always set `application_name` on a client of a shared system database.
- Workflows live in an outer package such as `engine`, and call services. Services do not know the engine.

## Recovery and control

- After a restart, reconcile durable ownership and liveness before dispatching new work. Start no duplicate supervisor, and keep incomplete cleanup visible.
- Keep the record of a human gate decision in durable storage. A resumed run reads it instead of asking again.
- A switched backend starts a fresh attempt. Historical session identities stay as they were.
- Cancellation takes effect at the start of the next step. After `cancel_workflow`, poll until the status leaves `PENDING` before cleaning up.
- Use `rewind_workflow` when an outside sender holds the workflow id, since `fork_workflow` issues a new id and their messages never arrive.
- Keep patch markers until no old run can still be in flight.
- Tag runs with attributes and filter on them. Do not encode customers in workflow ids.

## Testing

Reset the engine in a fixture: destroy any instance, construct a new one, call `reset_system_database(truncate=True)`, launch, yield, destroy. The reset is destructive, so it points at a test database only. Skipping it leaks state between tests. Patch workflows and steps with `mocker` where the caller looks them up.
