# API and schemas

## Contents

- [Boundary models](#boundary-models)
- [Writing a model](#writing-a-model)
- [Routes and dependencies](#routes-and-dependencies)
- [Errors and status codes](#errors-and-status-codes)
- [Pagination and contracts](#pagination-and-contracts)

## Boundary models

Every request body, response, event payload and LLM output is a Pydantic v2 `BaseModel`, declared in the context's `schemas.py`. The ORM class lives in `models.py` and is a different class. Never use SQLModel or any class that is both a table and a schema.

Build a response model from a row with `ConfigDict(from_attributes=True)` and `Schema.model_validate(row)`, done in the service layer so a handler never sees an ORM object.

- Give request and config models `ConfigDict(frozen=True, extra='forbid')`. An unknown field then fails loudly instead of being dropped.
- Never return an ORM object, an internal id you did not mean to expose, a stack trace or a raw driver error.
- Use `AwareDatetime` for time fields so a naive timestamp is rejected at the edge.
- Pydantic coerces by default: a numeric string becomes an int. Use strict mode on a field or model where a wrong type must be refused.

## Writing a model

- Declare constraints with `Annotated` and the built-ins (`Gt`, `max_length`, `StringConstraints` for strip and case). A hand-written validator for "greater than 1" hides the rule from the generated schema.
- Keep `alias`, `default` and `default_factory` in the `Field()` assignment form, because type checkers read that form. Put everything else in `Annotated`.
- Write no `...` for a required field. A field without a default is already required.
- Prefer an after-validator, which gets a value already coerced to the field type. A before-validator sees raw input of any shape, and a model-level one may not receive a dict at all.
- Model a polymorphic payload as a discriminated union: each variant has a `Literal` type field and the union names it. Declaring the base class on a field silently drops the subclass fields on validation and on dump.
- Declare `int` where numeric strings are acceptable, not `int | str` plus a converter. Use `list[...]` and let tuples coerce.
- Closed sets are `StrEnum` with lowercase snake values, or a `Literal` for a local set.
- Put model-level metadata (`description`, `title`, constraints) on the type. Put field-level metadata (`deprecated`) on the outermost type of a union, not on one branch.
- Skip `from __future__ import annotations` in modules that define models, because stringified annotations are harder to resolve. The exception is a project that already uses it with ruff's runtime-evaluated-base-classes setting for `pydantic.BaseModel`.

## Routes and dependencies

Keep a handler to a few lines: take validated input, call one service function, return the result. Business rules in a handler cannot be reused by a worker or a test.

- Declare every path, query, header and body parameter with `Annotated`, constraints inside it.
- Give every handler a return annotation. FastAPI filters, validates and serializes by it, so a wrong hint changes what clients receive. Add `response_model=` only when the returned object differs from the public schema.
- Declare each dependency once as a module-level alias, such as `Annotated[AsyncSession, Depends(get_session)]`, and reuse the alias. Suffix it `Dep` or name it for the role (`CurrentPrincipal`). Keep aliases in `dependencies.py`, never in `api.py`.
- Make each dependency a plain function, not a class. A dependency that needs cleanup yields the resource and releases it in `finally`.
- Put prefix, tags and shared `dependencies=[...]` on the `APIRouter` itself. A check every route needs, such as auth, belongs there so a route added later cannot forget it.
- Write one function per HTTP verb. Do not branch on `request.method`.
- Use `def` when unsure. FastAPI runs it in a threadpool, while a blocking call in `async def` stalls every request.
- Build the app in a `create_app(settings=None)` factory with no import-time side effects, and start it with the server's factory flag.
- Do not reach for `ORJSONResponse` or `UJSONResponse`. Declare a return type and let Pydantic serialize.

## Errors and status codes

Map each domain exception to a response once, in an exception handler at the app edge. The detail is a short sentence that names the fix and holds no internals. The exception classes themselves follow code-guidelines.

- Use 201 for create, 204 for delete, 404 for a missing id, 409 for a state conflict, 422 for a refused input, 503 for an unavailable dependency, and 429 on a rate limit.
- An unhandled exception is logged once at the edge and answers a generic 500. See the observability reference.
- A route added next to siblings gets the same authorization guard they use. An id taken from the request needs an ownership check before it is used.
- Never mass-assign a request body onto a model. Copy named fields.

## Pagination and contracts

Page with a keyset cursor, not OFFSET. Sort on an immutable non-null column plus a unique tiebreaker, fetch `limit + 1` rows to learn whether another page exists, and cap any total count with a bounded subquery.

- Make the cursor opaque and authenticated, with an expiry. It carries a position and never grants access, so every page re-checks authorization.
- A cursor that points at a row the caller can no longer see invalidates the continuation with a 422. Do not drop the row silently.
- Derive the cursor key from its own setting. Never reuse a session, PII or third-party key, and never generate a random one per process.
- Give each route a stable snake_case `operation_id` when a client is generated from the schema.
- Regenerate `openapi.json` from `create_app().openapi()` without touching a database, commit it, and fail the lint when it drifts.
- Where the web framework is an optional extra, import it lazily so the CLI still starts without it.
