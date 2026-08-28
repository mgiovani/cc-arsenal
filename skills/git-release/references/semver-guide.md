# Semantic versioning quick reference

Based on [Semantic Versioning 2.0.0](https://semver.org/).

## Version format

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

## Conventional commit → semver mapping

| Commit Type | Breaking? | Bump |
|---|---|---|
| `feat` | No | MINOR |
| `feat!` or `BREAKING CHANGE:` | Yes | MAJOR |
| `fix` | No | PATCH |
| `fix!` or `BREAKING CHANGE:` | Yes | MAJOR |
| `docs` | No | PATCH |
| `style` | No | PATCH |
| `refactor` | No | PATCH |
| `refactor!` | Yes | MAJOR |
| `perf` | No | PATCH |
| `test` | No | PATCH |
| `build` | No | PATCH |
| `ci` | No | PATCH |
| `chore` | No | PATCH |

## Pre-1.0 versions (0.x.y)

Before version 1.0.0, the public API is not considered stable:
- **0.MINOR.PATCH**: Minor may include breaking changes
- Initial development uses `0.x.y` versions
- Anything may change at any time

## Version precedence

When multiple bump types are detected in a single release:
1. **MAJOR** wins over all (any breaking change)
2. **MINOR** wins over PATCH (any feature addition)
3. **PATCH** is the default (only fixes and maintenance)

## Breaking change detection

A commit indicates a breaking change if:
1. Type has `!` suffix: `feat!:`, `fix!:`, `refactor!:`
2. Commit body contains `BREAKING CHANGE:` footer (note: must be uppercase)
3. Commit body contains `BREAKING-CHANGE:` footer (hyphenated variant)

## Tag convention

- Prefix with `v`: `v1.0.0`, `v2.3.1`
- Match existing repository convention if tags already exist
- Annotated tags preferred over lightweight tags

## Changelog section order

1. Breaking Changes (highest visibility)
2. Features
3. Bug Fixes
4. Performance
5. Documentation
6. Other Changes
