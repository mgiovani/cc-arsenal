# Tooling

## Contents

- [Package manager and scripts](#package-manager-and-scripts)
- [Lint and format](#lint-and-format)
- [No suppressions](#no-suppressions)
- [TypeScript](#typescript)
- [Lint rules that guard the design](#lint-rules-that-guard-the-design)
- [Generated files](#generated-files)
- [Tests](#tests)
- [The check chain](#the-check-chain)

## Package manager and scripts

Use bun: install with `bun install --frozen-lockfile` in CI and `bun run <script>` for every script, and commit `bun.lock`. Keep one lockfile at one root. Two package managers in one tree mean two lockfiles that disagree.

A project that already uses another manager (a `pnpm-lock.yaml`, a `packageManager` field) keeps it. Translate the commands here and do not migrate unasked.

Keep the frontend toolchain out of a backend gate in a mixed repo. The frontend has its own check command, so a backend change does not wait on a frontend install.

## Lint and format

The default is ESLint with Prettier.

- ESLint: a flat config with `recommendedTypeChecked` from typescript-eslint using the project service, `jsx-a11y` recommended, `react-hooks` recommended with `exhaustive-deps` as an error, and `no-unused-vars` that ignores a leading underscore.
- Prettier: `semi: true`, `singleQuote: true`, `trailingComma: 'all'`, `printWidth: 100`, two-space indent, and the Tailwind plugin pointed at the main stylesheet with `functions: ['cn', 'cx', 'tv']` so class order sorts inside those calls.
- Run `eslint .`, then `prettier --check .`, then the boundary check, as separate steps.

A project with a `biome.json` uses Biome for both lint and format, with single quotes, two-space indent and `a11y.recommended`, and adds no ESLint or Prettier beside it. Two formatters rewrite each other. Defer to whichever the project already runs.

## No suppressions

Add no `eslint-disable` and no `@ts-ignore`. The general suppression rule is in `code-guidelines`. These are the frontend specifics.

- If a rule is wrong for the whole project, change it in the shared config with the reason written beside it. Ignore generated paths there as well.
- Parse unknown data at the boundary with a schema, so the rest of the code holds real types.
- For an upstream typing bug you cannot fix, stop and report it instead of suppressing it.
- Enable `no-warning-comments` so `TODO` and `FIXME` fail the lint run.

## TypeScript

- Turn on `strict`, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`, `isolatedModules`, `noUnusedLocals`, `noUnusedParameters` and `noFallthroughCasesInSwitch`. Add `exactOptionalPropertyTypes` when starting fresh.
- `verbatimModuleSyntax` makes type imports explicit: write `import type` or an inline `type` modifier.
- Use string-literal unions instead of enums, and no namespaces or parameter properties (`erasableSyntaxOnly`).
- Use `moduleResolution: Bundler`, `jsx: react-jsx`, `noEmit`, and one `@/*` alias for `src/*`.
- When tsconfig files use project references, the root and app files are solution files with `files: []`. A loose `tsc --noEmit` inside them compiles nothing and returns a false green. Run `tsc -b`.
- Named exports only. Type props with an interface and handlers with specific event types, never `any`.

## Lint rules that guard the design

Wire the rules from the other references into lint, so they fail a build instead of waiting for a reviewer.

- `no-restricted-syntax` on raw colors (hex, `rgb`, `hsl`, `oklch`, `bg-[#`) in `className` and in `style`, on palette names and on references to primitive color variables. Exempt the generated token file.
- `no-restricted-syntax` on physical Tailwind utilities when the project uses logical ones, on `dangerouslySetInnerHTML`, and on literal `h2` to `h6` when a heading component exists.
- `no-restricted-imports` banning the icon package outside the `Icon` wrapper.
- A small test that greps `src` for the design rules lint cannot express: raw hex, font weights above the allowed set, `rounded-` classes when radius is zero, native `<select>`, and stroke attributes on icons.
- Layer boundaries through dependency-cruiser or `eslint-plugin-boundaries` (see the layering reference).
- No inline `style` also keeps a strict `style-src 'self'` policy workable.

## Generated files

Generate the token CSS from the token source, the API client from the OpenAPI file and the route tree from the router. Commit them, never edit them, and exclude them from lint, format and prose checks. Gate each with a check script that fails on drift without writing (`tokens:check`, `codegen:check`).

## Tests

- Use the project's runner. Vitest is the default, in browser mode where the project runs components in a real engine, otherwise with a DOM environment. A project on `bun test` with a DOM shim keeps it.
- Register the DOM environment once and share it. Unregistering it breaks later test files.
- Stub the network at the generated SDK module or with a small `fetch` stub that records requests. Add a mock server only when that is not enough.
- Run stories as tests with the axe addon, and query by role and accessible name.
- Keep coverage thresholds where the project sets them, and fix the code, not the number.
- Run visual regression in a pinned container with committed baselines and animations switched off, so a local font difference cannot fail CI.

## The check chain

Expose one script that runs the whole chain in this order, so the cheap and likely failures come first:

```
codegen:check -> tokens:check -> typecheck -> lint -> format:check -> boundaries -> build -> test
```

Run it before you call the work done, and report the exit code and counts from that run. Frontend changes also need a look at the rendered page: see the visual design reference.
