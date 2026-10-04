# CLI

`stopslop [OPTIONS] [PATHS]...`, no subcommands.

## Scope

- Paths: files or directories, default is the current directory.
- `--staged`, `--changed`, `--since <REF>`: mutually exclusive. Any paths given become pathspecs that narrow the selection.

## Flags

| Flag | Use |
|---|---|
| `--format text\|json\|sarif\|markdown` | Output format |
| `--select`, `--extend-select`, `--ignore`, `--extend-ignore` | Codes, prefixes, or groups; `ALL` is reserved |
| `--list-rules` | Canonical rule names, groups, tiers |
| `--help-config` | Every `stopslop.toml` key |
| `--baseline[=PATH]`, `--write-baseline[=PATH]` | Subtract or record accepted findings; the `=` is required for a custom path |
| `--check-imports` | Enables SLOP010; `--select ALL` alone does not |
| `--config PATH`, `--no-config` | Pick or ignore config files |
| `--fail-on-tier A\|B\|C` | Lowest tier that exits 1, default `A` |
| `--stats` | Per-rule counts in the output |
| `-j` | Parallel jobs |

## Exit codes and tiers

- 0: no finding at or above `--fail-on-tier`
- 1: at least one finding at or above it
- 2: usage or config error

Tiers:

- A: mechanical, fails by default
- B: judgment, exit 0 by default
- C: provisional, off by default
