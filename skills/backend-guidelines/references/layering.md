# Layering

## Contents

- [Package shape](#package-shape)
- [Dependency direction](#dependency-direction)
- [Enforcing it](#enforcing-it)
- [Wiring](#wiring)

## Package shape

Each bounded context is one package under the source root, split by role:

- `models.py` holds entities, value objects and invariants.
- `service.py` holds use cases.
- `exceptions.py` holds domain errors.
- `schemas.py`, `dependencies.py` and `api.py` appear only when the context has a web surface.

A concept gets its own module once it has its own vocabulary. A module is created when something uses it, and an existing module is extended first.

The owner's repos disagree on file names: two use `service.py`, one uses `services.py` and names the router file `api.py`. For a new context, use `service.py`. In an existing project, copy the plural or singular form it already has. Never run both forms side by side.

The backend package is the backend. Do not add a `backend/` layer inside a repo whose root package already is one.

## Dependency direction

The direction rule is in code-guidelines. The backend specifics:

- `models`, `schemas` and `service` never import `fastapi`, `starlette` or a workflow engine.
- Contexts refer to each other by a schema-qualified foreign key string.
- `db/` holds only infrastructure shared by contexts: engine, base class, naming convention, session helpers. A business entity never lives there.
- Adapters import inward and nothing imports them back. An inbound adapter (HTTP, CLI, scheduler) may import the services it drives.
- A context declares the port it needs as a `Protocol`. The adapter for each outside system sits in its own package and is wired at the composition root.
- Confine the database driver, HTTP client, cloud SDK and LLM library each to one package, and re-export driver exceptions there under domain names.
- Do not create an interface with one implementation and no boundary to isolate. A test double counts as a second implementation.

## Enforcing it

Write each rule as an import-linter contract in `pyproject.toml`, and run `lint-imports` in the lint gate. A rule that only lives in prose erodes within a month.

Use three contract kinds:

- `forbidden` contracts keep the framework, the driver and the LLM SDK out of the packages that must not know them.
- `layers` contracts fix the order inside a context, such as api above dependencies above services above models above exceptions.
- `independence` contracts keep sibling contexts from importing each other.

Extend the contracts in the same change that creates a package. A package added later starts outside every rule. Mark `allow_indirect_imports` only where the contract says why.

When a contract blocks a change, move the code or add a port. Do not widen the contract to make the import pass. If the contract is wrong, change it in its own commit with the reason.

## Wiring

- Build the object graph once at the composition root, which is `create_app` for the web process and `main` for a worker. Business rules never instantiate an adapter.
- Services are module-level functions that take the session or port first. A service class is justified only by state it must hold.
- A service never commits in the middle of a session it did not open. The caller owns the transaction boundary.
- A new behaviour variant enters as a new implementation of the port. Do not edit the code that consumes the abstraction.
- A workflow engine or scheduler sits in its own outer package and calls services. Services do not know it exists.
- Keep one clock function and one HTTP client factory in a shared module, and import them from there.
- Where the code is not yet split this way, a ticket that edits a module moves that module toward the shape. Nothing is moved ahead of a reason to touch it.
