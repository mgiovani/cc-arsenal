# stopslop.toml

Lookup: the nearest `stopslop.toml` walking up from the current directory, else `~/.config/stopslop/stopslop.toml`. Files are never merged. `--config PATH` picks one, `--no-config` ignores all.

Run `stopslop --help-config` for every key with its default.

Keys: `select`, `extend-select`, `ignore`, `extend-ignore`, `exclude`, `check-imports`, `baseline`, `fail-on-tier`, `language`, `[per-file-ignores]`, `[[custom-rule]]` (codes start at SLOP900).

Caveats:

- `exclude` applies only to directory walks, not to paths passed explicitly.
- `extend-ignore` is subtracted last, so it beats `extend-select`.
- A repo config can hide findings. When the user asks for "everything", say which config was found, and offer `--no-config`.
