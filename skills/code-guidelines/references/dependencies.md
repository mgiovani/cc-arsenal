# Dependencies

## Adding one

Use the standard library before a dependency. A new dependency needs a reason the standard library cannot meet, and the reason goes in writing in the PR body. Where the project's contract asks you to propose a dependency first, propose it with that reason before you edit the manifest.

Walk the ladder in simplicity.md first: this repo, the standard library, the platform, an installed dependency, and only then a new one.

A dependency earns its place when it replaces logic that is hard or risky: cryptography, protocol parsing, a real HTML or CSS parser, image decoding. It does not earn one for a few lines. A library you use for one function (`cloneDeep`, `groupBy`) is the pattern to avoid.

Check the runtime floor before choosing a built-in. `structuredClone` and `Object.groupBy` need recent runtimes. On an older one, a short reduce still beats a new package.

Platform replacements agents miss:

| Instead of | Use |
|---|---|
| a date library for formatting | `Intl.DateTimeFormat`, `Intl.NumberFormat` |
| a uuid package | `crypto.randomUUID()` |
| a fetch polyfill or `request` | global `fetch` |
| `dotenv` | `node --env-file` |
| `mkdirp`, `rimraf` | `fs.mkdir` and `fs.rm` with `recursive` |
| a query-string library | `URLSearchParams` |
| a modal or infinite-scroll package | `<dialog>`, `IntersectionObserver` |

This is a list of known cases, not a detector for old packages.

## Keeping them honest

- Change the manifest and the lockfile together. Never commit one without the other.
- Use the package manager the lockfile names. Never add a second lockfile or manager. For a new project, default to `uv` for Python and `bun` for JavaScript. An existing lockfile decides.
- Pin a package you import directly even when it also arrives transitively. Relying on the transitive copy breaks silently.
- Keep minimum versions as floors. Cap a tool only when its releases break the build, and write the reason beside the cap.
- Treat a package from a git URL, a tarball or a non-default registry as a supply-chain risk, and say why you need it.
- A major-version bump needs the matching code changes.
- Run the project's audit command for known vulnerabilities and licence conflicts. For a full audit, use the `review-deps` skill.

## Direction of dependencies

Dependencies point inward. A domain package imports the standard library and its own modules. It never imports an adapter, a framework, `config` or `db`.

- Enforce this with an import-linter style contract in the project's config, and extend the contract when you add a package.
- Contexts refer to each other by id, never by importing the other context's module.
- Confine each vendor SDK to one module. Everything else imports that wrapper.
- Nothing at the repository root depends on code inside an app directory. The code depends on the root.
- A shared utility never imports a feature module. Circular imports between packages are a defect.

## Tooling that stays out of the way

Keep one toolchain from leaking into another. A frontend toolchain stays out of the Python gate, and the reverse holds too. Two lockfiles in one repo are acceptable when each toolchain keeps its own root.
