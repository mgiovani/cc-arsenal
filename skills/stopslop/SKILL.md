---
name: stopslop
description: Run the stopslop AI-slop linter with every rule, report findings, and render them for review. Use for "run stopslop", "slop report", "check for AI slop". Not for code review (use review-code).
metadata:
  summary: "Install stopslop, run a full all-rules AI-slop report, and render it as a markable page"
---

# stopslop

Run the linter with every rule on, summarize from its JSON, and optionally turn the findings into a page the user marks up.

## Checklist

Copy this list and tick each step. A gate means stop and report if it fails.

- [ ] 1. Install or verify the binary. Gate: no `stopslop` and no `cargo` means print the install line and stop. See `references/install.md`.
- [ ] 2. Pick the scope: paths, `--staged`, `--changed`, or `--since <ref>`. See `references/cli.md`, and `references/config-file.md` for a repo `stopslop.toml`.
- [ ] 3. Run the full report and save the JSON. Gate: exit 2 means show stderr and stop. See `references/full-report.md`.
- [ ] 4. Summarize by tier, rule and file from the JSON. See `references/full-report.md`, and `references/rules.md` for rule groups.
- [ ] 5. Offer to render the findings (opt-in). See `references/render-and-fix.md`.
- [ ] 6. After the user marks the page, fix only the items marked `fix`, then re-run stopslop on the touched files. See `references/render-and-fix.md`, and `references/suppressions.md` for accepted findings.

## Rules

- Quote counts only from the JSON the run printed. Never estimate a number.
- Take rule names and codes only from `stopslop --list-rules`. Never invent one.
- Exit 0 under default settings does not mean clean: Tier B findings do not fail by default. The full report uses `--fail-on-tier C`.
- Never edit a file the user did not mark `fix`.
