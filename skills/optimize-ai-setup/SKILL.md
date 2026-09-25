---
name: optimize-ai-setup
description: Audits the AI coding setup on this machine (Claude Code, Codex CLI and app, Cursor, Antigravity, Gemini CLI, Claude Desktop) for token waste and quality drag, then ranks the fixes. A deterministic local script measures real session logs and configs (startup context size, prompt-cache hit rate and rebuilds, oversized CLAUDE.md/AGENTS.md, duplicate or unused skills, plugins and MCP servers, stale env settings, model and effort mix) without reading message content or secrets, so the audit itself costs few tokens. Use when the user asks why Claude Code or Codex burns through their limits, wants to cut the token usage or cost of their agent setup, audit their MCP servers or skills, fix prompt-cache misses, or optimize their AI setup. Not for cutting the cost of their own Claude API application code (use the claude-api skill's cost-optimize), and not for writing new memory rules (use create-rule).
metadata:
  summary: "Measure token waste across installed AI coding tools and rank the fixes"
allowed-tools: Bash(uv run *), Bash(python3 *), Bash(awk *), Bash(cp *), Read, Write, Edit, AskUserQuestion, Skill
---

# Optimize AI Setup

Measure first, then advise. A local script collects every number from configs and session logs; the model reads only its compact report plus the catalog entries for the findings that fired.

## Token rules for this skill

- Run the collector once per audit. Do not open transcripts, session logs, SQLite stores, or whole config files: the script already read them, safely and with size caps.
- Read `references/checks.md` only by ID (the `awk` range below), only for findings being presented.
- Answer with a short snapshot and a ranked fix table. Do not restate the whole report.

## Step 1: Collect evidence

From the user's project directory, run the collector (`<skill-dir>` is this skill's directory):

```bash
uv run <skill-dir>/scripts/collect.py --days 14
```

Without `uv`, use `python3 <skill-dir>/scripts/collect.py` (Python 3.11+). Flags: `--days N` (lookback window), `--project PATH`, `--all` (every finding, not just the top 15), `--json`.

- `no harness detected`: say so and stop.
- A harness line showing `error:`: mention it and continue with the others.

## Step 2: Explain the top findings

Print the catalog entries for every HIGH finding plus the top five overall, in one call (the `awk` range prints each entry and stops at the next heading):

```bash
awk '/^## (CC-STARTUP|CC-REBUILD|CX-AGENTSMD-CAP)$/{p=1;print;next} /^## /{p=0} p' <skill-dir>/references/checks.md
```

Interpret the evidence before recommending:

- Startup context is paid by every session and every subagent, so a large one outranks most other findings.
- A high token-weighted cache hit rate can still hide expensive writes; judge caching by the cost-weighted share and the rebuild count.
- Rebuilds after idle are fixed by a habit (`/compact` before a break); model or effort rebuilds by choosing both at session start; upgrade rebuilds are expected and need no fix.
- "Unused" only means no uses inside the window. Say "no uses in the last N days" and suggest demoting (`name-only`, `user-invocable-only`) before disabling.
- Quote the numbers the report printed. Never invent or extrapolate numbers the script did not measure.
- Flag any fix that trades quality for cost (lower effort, a smaller auto-compact window) with its Tradeoff line.

## Step 3: Propose fixes on a page (opt-in)

Use the `render` skill to build the proposals as one `audit` page (via the `Skill` tool as `render audit`, otherwise follow the render skill's steps inline). One anchored item per finding, anchor `finding-<harness>-<check-id>`, holding:

- the measured evidence exactly as the report printed it
- the concrete fix: the exact command, settings key and value, or file edit. A finding's `--json` output carries a `names` list (the actual skills, servers, or plugins it's about); substitute those for any generic `<name>` placeholder in the `fix` string instead of leaving it literal
- the impact and, when the catalog has one, the tradeoff
- a `fix` / `won't fix` / `discuss` verdict

Group the distribution by harness and sort by severity. Put the habits in a short section with no verdicts. Deliver the page path in two lines and ask the user to mark it. When they say it's marked, read the marks back per the render skill and apply only the items marked `fix`. Without a render skill, ask with AskUserQuestion (multi-select) or a numbered list instead.

Rules for applying the chosen fixes:

- Claude Code settings (`skillOverrides`, `promptCacheTtl`, `autoCompactWindow`, `statusLine`, removing a `DISABLE_PROMPT_CACHING*` env): use the `update-config` skill via the `Skill` tool where available, otherwise edit the settings JSON directly and keep every other key intact.
- Codex `~/.codex/config.toml` (`enabled = false` or `enabled_tools` on an MCP server, `project_doc_max_bytes`), `disable-model-invocation: true` on the user's own skills, and `.cursor/rules` frontmatter: edit in place.
- Never delete skills, plugins, MCP servers, rules, or memory files. Disable or demote them; deletion stays the user's call.
- `X-MCP-INLINE-SECRET`: name the file and server only, and tell the user to rotate the secret and reference it as `${VAR}`. Never print or move the value.
- Session habits (`/clear`, `/compact`, model choice) are advice, not edits.

Settings changes apply to new sessions. Do not re-run the collector to "verify" in the same session: its evidence comes from past sessions. Suggest re-running after a week or two of normal use to compare.

## Step 4: Close with habits

Print the `HABITS` entry with the same `awk` range and keep only the lines that match what the report showed (for example, the `/compact` line only when idle rebuilds were found).

## Output shape

In chat, keep it to the snapshot and the page link. The page carries the full proposal list:

```
**Setup snapshot** (last 14 days): <1-2 lines with the most telling metrics>
**Top fixes:** <the three highest-impact fixes, one line each>
Proposals: <page path> (mark fix / won't fix / discuss, save, then tell me)
```

## Notes

- Privacy: the script reads only numeric usage fields, model/effort/version values, tool names, and attachment sizes from session logs. It skips credential files, prints no env values, URLs, or message text, and makes no network calls.
- Coverage: token metrics come from Claude Code and Codex local logs. Cursor, Antigravity, Gemini CLI, and Claude Desktop keep no readable per-session token data, so their checks are config-based (Claude Desktop also uses its MCP server logs).
- For the current Claude Code session only, `/usage` (prompt cache line, usage attribution) and `/context` (startup composition) complement this audit.
