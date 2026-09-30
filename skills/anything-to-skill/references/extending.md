# Extending: adding a source handler

A new input type is one new subpackage under `scripts/anything_to_skill/sources/`. Nothing in `core/`, `plan/` or `emit/` changes, apart from one line in the registry.

## Files

```
sources/<name>/
  __init__.py
  detect.py     stdlib only
  run.py        heavy imports live inside functions
```

Plus one shim, `scripts/ingest_<name>.py`, copied from an existing shim: a `uv run --script` shebang, a PEP 723 dependency block, a `sys.path.insert` of the scripts directory, and a call to `run_source('<name>', sys.argv[1:])`. Dependencies go in that shim's block, never in another handler's.

## Contract

`detect.py`:

```python
NAME = '<name>'
def detect(arg: str) -> int: ...   # 0 = not mine; higher wins; web returns 1 as the fallback
```

`run.py`:

```python
def add_args(parser): ...                      # flags specific to this handler
def run(ctx, args) -> RunSummary: ...          # ctx.store, ctx.goal, ctx.effort, ctx.max_pages, ctx.over_budget()
```

Add the name to `NAMES` in `sources/__init__.py` (order breaks score ties; keep web last) so routing sees it.

## Rules a handler must follow

- **Routing imports only `detect`.** `a2s.py detect` and `seed` must never import a handler's heavy dependencies, so a markdown folder never installs a speech or PDF stack.
- **Expand your own seeds first.** A unit of `kind='seed'` is expanded by `run` into `page`, `video` or `file` units and marked `done` or `skipped`. `estimate` reports unexpanded seeds separately.
- **`Store.finish` is the only place content is saved.** It strips invisible Unicode, counts tokens, hashes and writes `md/<id>.md`. Never write to `md/` directly.
- **Claim work with `Store.claim`**, finish with `finish`, `fail` (retries with backoff) or `mark`. Never invent a status; use the existing ones (`needs_*` for work another script completes).
- Give each unit a `hint` (its section path in the source's own terms) and a `priority`. The planner turns hints into the tree.
- Honor `ctx.max_pages` and `ctx.over_budget()`; stop cleanly and leave the rest `pending`.
- Network handlers go through the SSRF check (`core/ssrf.py`) and honor robots.txt.
- Return a `RunSummary` with errors listed in `errors`; do not swallow them.

## Tests

Add `scripts/tests/test_a2s_<name>.py` with fixtures under `scripts/tests/fixtures/anything_to_skill/<name>/`. Tests must not touch the network; fake heavy dependencies with stubs. Add the handler to the routing tests and a subprocess check that routing does not import `run`.

## Docs

Add the handler to `references/sources.md`, the SKILL.md phase 1 section, and the CHANGELOG.
