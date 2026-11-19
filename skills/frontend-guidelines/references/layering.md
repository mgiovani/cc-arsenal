# Layering

## Contents

- [The one-way list](#the-one-way-list)
- [What each layer holds](#what-each-layer-holds)
- [Data and the API client](#data-and-the-api-client)
- [Vendor isolation](#vendor-isolation)
- [Enforcement](#enforcement)

## The one-way list

A layer imports only from the layers to its right:

`routes` and `widgets`, then `features`, then `entities`, then `ui-patterns`, then `ui`, then `lib`.

Create a layer only when it has a file to hold. A small app can start with `routes`, `features`, `entities`, `ui` and `lib`, and add `widgets` and `ui-patterns` later. Do not move code ahead of a reason to touch it.

Use an absolute alias (`@/` pointing at `src/`) for every import across folders. A relative path that climbs out of its folder hides which layer it crosses.

## What each layer holds

- `lib`: pure utilities and label maps (status labels, phase labels) with unit tests. It imports nothing from the app.
- `ui`: atomic primitives such as Button, Icon, Dialog. It imports `lib` only.
- `ui-patterns`: composed patterns built from primitives, such as EmptyState or ConfirmDialog.
- `entities`: domain types and query hooks, one `queries.ts` per entity.
- `features`: self-contained slices. The logic of one user flow lives in `features/<flow>/`. Distinct flows share code only through `features/_shared/`.
- `widgets`: page-level compositions of several features. Two widgets never import each other.
- `routes`: wiring only. A route file connects a path to a feature or widget and ships its pending, error and empty components.

An entity never imports a feature. A feature never imports a widget or a route. These follow from the list, and the lint contract states them so the rule survives a new contributor.

## Data and the API client

- Send every piece of server state through the project's query library. Hold query and mutation hooks in the entity, with a key factory scoped by project. Never write a raw key string inline in a component, and never build a client inline.
- Use loaders to prefetch with `ensureQueryData`, so the route renders with data in the cache.
- Default frequent, reversible user actions to optimistic updates with a rollback, and let `onSettled` invalidate. Do not update optimistically when the server decides the result.
- Generate the API client from the backend's OpenAPI file and commit both. Never edit the generated folder, and fail CI on drift between spec and client.
- A generated client often resolves on any HTTP status. Check the result explicitly (error, response ok, data defined) and throw a typed `ApiError`, or a dead server reads as an empty list.
- Convert errors for display in one helper that strips transport detail (request line, status code) and falls back to a sentence the caller supplies.
- Keep SDK types out of UI code. Components read entity types, not transport shapes.
- Poll from a change stamp rather than on a blind timer, and keep intervals and cache lifetimes as named constants.

## Vendor isolation

Import each third-party SDK in exactly one folder: the icon set inside `ui/Icon`, an auth SDK inside `lib/auth`, a telemetry SDK in its own client entrypoint. Everything else calls your wrapper, so a vendor swap or a browser-only SDK never leaks into server-rendered code.

A client-side guard such as a hidden button or a route redirect is not authorization. A server check must stand behind each one. Keep tokens and personal data out of local storage, and build redirects from an allowlist, not from a raw `returnTo` parameter.

## Enforcement

Write the layer rules into lint. A rule that lives only in this file will be broken within a month.

- Use a dependency-cruiser config or `eslint-plugin-boundaries` with a default of disallow. Declare each element type and its allowed targets, forbid cycles as an error, and warn on orphans.
- Add one rule per vendor isolation (`phosphor-only-in-icon`, `clerk-only-in-auth`) and one against deep imports into another package's `src`.
- Expose the check as its own script (`boundaries`) and include it in the project's single check command.
- When you add a layer or a package, extend the contract in the same change.
