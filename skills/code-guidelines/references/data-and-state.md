# Data and state

## Values

Make values immutable and functions pure by default. In Python that is a frozen dataclass with slots. In TypeScript it is a new object instead of a mutation.

- Hold collections in values as tuples or frozen sets, and expose read-only mappings.
- A function must not mutate its parameters unless that is its documented contract.
- Closed sets are enums or literal unions. Put a derived group next to the enum as a frozen constant.
- Use a tagged or discriminated union in place of a status string plus nullable data and error fields. The impossible combinations then cannot be written.
- Collapse interacting boolean flags into one state value with one transition function.
- Compute a derived fact once, in the narrowest scope that needs it, and let readers take it as a field.

## Validation models and plain types

Use a validating model class (such as a Pydantic model) at the edge: HTTP bodies, config, events, external payloads. Inside the program, use plain frozen dataclasses. A static type checker already catches mismatches there, so runtime validation adds cost without safety.

A validating model is a snapshot. Anything rewritten over an object's lifetime belongs in an ordinary class.

Do not subclass a model and then declare the base type on a field. The subclass fields vanish on validation and on dump.

Projects differ on this. The default is the edge; follow whatever the project already does.

## Numbers, money and time

- Store money as integer minor units (cents), never floats.
- Round with an explicit rule and test zero, negative and boundary amounts.
- Take time from one clock function that returns aware UTC. Never build naive datetimes. Tests use a fixed clock constant.
- Time-bound features state the unit in the name or type (`timeout_seconds`).

## Shared and mutable state

- Avoid module-level mutable state. A flag set once and never reset leaks across users, tests and reloads.
- State kept in the process (dicts, caches, per-process limiters) covers one process only. A limit shared across servers needs a shared store.
- A read-modify-write or check-then-act sequence is a race. Make it one atomic operation, take a lock, or give the state a single owner.
- Key a rate limiter per client, not globally, or one abusive client blocks everyone.
- Every cache has a bound and an eviction rule. For a pure function, `functools.lru_cache` beats a hand-built cache class.
- On sign-out or an identity change, clear the client cache, reset stores and wipe persisted storage. Otherwise the next user on a shared machine sees the previous user's data.
- Copy deeply with the platform call (`structuredClone`, `copy.deepcopy`), not a JSON round trip that turns dates into strings and drops `undefined`.

## Output you can compare

Output must be deterministic. When a message names one of several qualifying items, choose the first in document order, not whichever a hash map yields. Identical runs then print identical text, and recorded fingerprints keep matching.

Match recorded findings by a fingerprint of code, path and message with digits normalized, never by line number.

## Append-only history

A migration is appended to the chain and never edited after it merges. A fix is a new migration at the end, not a rewrite of an old one. The same holds for any ledger or log: add entries, never alter past ones.

- Autogenerate a migration, then review it by hand. The generator cannot see roles, grants or row-level security.
- Add isolation, such as a tenant column and its policy, in the table's first migration. Adding it to a populated table is a data migration.
- A migration that alters a populated table opens by setting a short lock timeout. Build indexes concurrently, outside the transaction.
- Run `upgrade` as its own step before the app starts, never inside the app's startup.
