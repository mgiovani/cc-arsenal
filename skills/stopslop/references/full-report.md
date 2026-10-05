# Full report

Every rule on, including the off-by-default ones, failing on any tier:

```bash
cd <repo-root> && STOPSLOP_NO_UPDATE_CHECK=1 stopslop --select ALL --check-imports --fail-on-tier C --format json --stats <scope> > <scratch>/stopslop.json
```

Write the JSON to a scratch directory, never into the repo. Exit 1 is expected when there are findings. Exit 2 is an error: show stderr and stop.

## JSON shape

```
{"findings":[{code,name,tier,path,line,col,message,fix?}],
 "stats":{files,findings,lines,rules:[{code,tier,name,count,files}],...}}
```

## Summarize

Compute everything from this file:

1. Totals: `stats.files`, `stats.findings`, per-tier counts.
2. Top rules by `count`, each printed as `<code> <name>` with `name` copied verbatim from `stats.rules[]`, plus tier.
3. Top files by finding count.
4. Tier A in full (file:line, message). Tier B and C grouped by rule: show a few per rule and the rule's total.
5. State the difference from the default gate: defaults fail on Tier A only, this run reports every tier.
6. For findings the user accepts, point to `references/suppressions.md` and `references/config-file.md`.

Zero findings: say what was scanned (`stats.files`) and that all rules ran.
