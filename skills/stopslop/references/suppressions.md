# Suppressions

Inline, in the file's own comment syntax (`<!-- -->` in Markdown and HTML):

- `ai-slop-ignore`: this line and the next, every rule
- `ai-slop-ignore: SLOP002,SLOP004`: only those codes
- `ai-slop-ignore: verbosity`: a whole group
- `ai-slop-ignore-file` or `ai-slop-ignore-file: CODES`: the whole file

Unused directives are reported as findings, so remove one when its finding is gone.

Baselines record accepted findings so only new ones show:

```bash
stopslop --write-baseline=.stopslop-baseline.json <scope>
stopslop --baseline=.stopslop-baseline.json <scope>
```

Per-path rules go in `[per-file-ignores]` in `stopslop.toml` (see `config-file.md`).

Add a suppression only when the user asks or marks `won't fix`. Never add one to make a run pass.
