# Rules

Source of truth: `stopslop --list-rules`. Run it for names, groups, tiers and defaults; do not recite rule names from memory.

Groups usable in `--select` and `--ignore`: `artifact`, `structure`, `stdlib`, `rhetoric`, `verbosity`, `sourcing`, `format`, `provenance`. `ALL` is reserved for everything.

Off by default: SLOP010, SLOP020, SLOP043, SLOP045, SLOP049. The full report command turns them on; SLOP010 needs `--check-imports` as well.

Tiers:

- A: mechanical, fails by default
- B: judgment, exit 0 by default
- C: provisional, off by default

Codes and prefixes both work: `--ignore SLOP01` covers the SLOP01x range.
