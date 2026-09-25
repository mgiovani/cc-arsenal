# Check catalog

One `## <ID>` section per check. Look up only the IDs the collector script fired; do not read the rest of this file.

## CC-STARTUP
Why: Everything loaded before the first prompt is re-sent on every turn of every session and subagent. Setups with many skills, MCP connectors and hooks commonly start at tens of thousands of tokens versus an ~8K illustrative baseline in the docs. skill_listing, deferred_tools_delta (grouped by `mcp__<server>__`), mcp_instructions_delta, and hook injections are the usual contributors.
Fix: `disable-model-invocation: true` on skills only ever called by `/name`; `skillOverrides: "name-only"`/`"off"` for unused ones; `/mcp` to disable idle servers; run `/context` to see the current breakdown.
Source: https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/mcp

## CC-CACHE
Why: Cache hit rate drives cost directly: a 90% vs 96% hit rate was $1.62 vs $0.99 for the same task.
Fix: Keep a session on one model/effort; avoid gaps past the TTL; API-key/cloud users set `promptCacheTtl: "1h"` (v2.1.242+) or `ENABLE_PROMPT_CACHING_1H=1`; check the "Prompt cache (main)" line in `/usage`.
Tradeoff: A 1h cache write costs 2x a 5m write (1.25x); it only pays off if the session actually has a gap that long.
Source: https://code.claude.com/docs/en/prompt-caching, https://claude.com/blog/what-a-task-costs-on-opus-5-5

## CC-REBUILD
Why: Cache rebuilds (writes > half the prompt, reads < half the prior prompt) re-write the whole conversation at 1.25x (5m) or 2x (1h) the input price instead of reading it at 0.1x. The most common avoidable cause is resuming after an idle gap past the TTL (1h subscription, 5m API key).
Fix: `/compact <focus>` before a break, not after; pick model and effort at session start, switching either mid-session forces a full rewrite; prefer `/rewind` over `/compact` to drop turns without losing cache.
Source: https://code.claude.com/docs/en/prompt-caching, https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything

## CC-LONGCTX
Why: Every turn re-reads the whole context, so long sessions multiply cost per turn; peak context creep also risks hitting auto-compact (~967K on 1M-context models) mid-task, an expensive, disruptive compaction.
Fix: `/clear` between unrelated tasks; `/autocompact <N>` (`autoCompactWindow`) to compact earlier and predictably; `/compact <focus>` to drop a finished sub-thread.
Tradeoff: A smaller auto-compact window summarizes earlier, so fine detail from early in the session can be lost; `/clear` between unrelated tasks has no such cost.
Source: https://code.claude.com/docs/en/settings, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## CC-MEMORY
Why: CLAUDE.md content over 200 lines, `@imports` (eager, up to 4 hops), and `.claude/rules/*.md` without `paths:` all load in full every session regardless of relevance.
Fix: Trim CLAUDE.md under 200 lines; move workflows into skills (loaded on demand); add `paths:` to `.claude/rules/*.md` so a rule only loads for matching files.
Source: https://code.claude.com/docs/en/memory

## CC-SKILL-DUP
Why: The same skill name listed from more than one source (a user symlink plus a plugin copy, for example) doubles its description in the startup listing for no benefit.
Fix: Keep one source per skill; `/plugin` to disable the plugin's copy, or remove the redundant user-level symlink.
Source: https://code.claude.com/docs/en/skills

## CC-SKILL-LISTING
Why: `description`/`when_to_use` past 1,536 chars are truncated anyway, and the total listing size adds directly to every session's startup tokens.
Fix: Trim descriptions under 1,536 chars; for skills only ever invoked by explicit `/name`, set `disable-model-invocation: true` to drop the description from context entirely.
Source: https://code.claude.com/docs/en/skills

## CC-SKILL-UNUSED
Why: A skill with zero `Skill` tool_use and zero `/name` invocations in the lookback window still costs its description's tokens every session.
Fix: Set `skillOverrides` to `"name-only"` (keeps `/name`, drops auto-trigger) or `"off"` (settings.json, or the `/skills` menu); never delete, it may still be wanted on demand.
Tradeoff: A skill demoted to `name-only` or `user-invocable-only` no longer triggers on its own; invoke it with `/name` when needed.
Source: https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/settings

## CC-PLUGIN-UNUSED
Why: An enabled plugin whose skills and MCP servers were never invoked in the lookback still contributes its full listing to every session's startup.
Fix: `/plugin` to disable the plugin (stays installed, stops loading).
Source: https://code.claude.com/docs/en/plugins

## CC-MCP-UNUSED
Why: A configured or connected MCP server with zero `mcp__<server>__*` calls in the lookback still loads its tool names and server instructions at startup.
Fix: `/mcp` to disable the server; prefer a CLI tool you already have (`gh`, `aws`, `gcloud`) over keeping an MCP server for the same job.
Source: https://code.claude.com/docs/en/mcp

## CC-TOOLSEARCH-OFF
Why: Tool search is on by default and keeps only tool names plus server instructions in context; with it off, every MCP tool's full schema loads up front.
Fix: Remove `ENABLE_TOOL_SEARCH=false` and `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` if set without reason; a non-first-party `ANTHROPIC_BASE_URL` disables tool search unless `ENABLE_TOOL_SEARCH=true` is also set.
Source: https://code.claude.com/docs/en/mcp

## CC-STALE-ENV
Why: `DISABLE_PROMPT_CACHING*` forces every request to skip caching, the single biggest lever this skill checks. `MAX_THINKING_TOKENS` is silently ignored by adaptive-reasoning models. `MAX_MCP_OUTPUT_TOKENS` above 25K defeats the default output cap (warns at 10K).
Fix: Unset `DISABLE_PROMPT_CACHING*`; drop `MAX_THINKING_TOKENS` on adaptive models, use `/effort` instead; keep `MAX_MCP_OUTPUT_TOKENS` at or under 25000.
Source: https://code.claude.com/docs/en/settings

## CC-HOOK-INJECT
Why: `SessionStart`/`UserPromptSubmit` hook output enters context every session or prompt; the hard cap is 10,000 chars per hook, and a large average injection compounds over a long session.
Fix: Trim hook output to what's actionable; put static context in CLAUDE.md/skills (loaded once, cached) instead of re-injecting it every prompt.
Source: https://code.claude.com/docs/en/hooks

## CC-MODEL-MIX
Why: Token share skewed to the top tier compounds cost; Fable 5.1 input runs 2.5x Opus 5.5 ($10/$50 vs $4/$20 per MTok), so small Fable volume can still dominate spend.
Fix: Match model to task (a stronger model at lower effort usually beats a weaker model at high effort); reserve Fable 5.1 for work where the result matters more than price; watch `opusplan` toggles, each flips the model and busts cache.
Source: https://claude.com/blog/what-a-task-costs-on-opus-5-5

## CC-SUBAGENT-MODEL
Why: Subagent (`isSidechain`) tokens riding the top-tier model multiply cost. Explore subagents inherit the main model (capped at Opus) unless told otherwise.
Fix: Set `model:` in the agent definition, or on the `Agent` call, for cheap/research subagents; avoid `CLAUDE_CODE_SUBAGENT_MODEL` for a mixed fleet since it forces one model onto every subagent regardless of role.
Source: https://code.claude.com/docs/en/sub-agents

## CC-EFFORT
Why: Effort defaults to high (medium on Opus 5.5); pinning routine work to xhigh/max pays for reasoning it doesn't need, and effort changes mid-session bust the cache except on Opus 5.5/Fable 5.1 first-party.
Fix: Pick effort at session start: medium for daily work, low for mechanical edits, high only when medium stalls; use `/effort`, not `MAX_THINKING_TOKENS` (ignored on adaptive models).
Tradeoff: Lower effort can miss on genuinely hard problems; raise it for those turns rather than keeping xhigh/max as the default.
Source: https://claude.com/blog/claude-model-and-effort-level-in-claude-code

## CC-PROMPT-CRUFT
Why: Patterns like "double-check", "verify twice", "be maximally thorough", "CRITICAL: YOU MUST", manual scratchpads, and contradictory rules measurably inflate cost, an additional ~9% cut was measured after removing them.
Fix: Run `/claude-api prompt-audit` on CLAUDE.md and skills; delete emphasis boosters and verification rituals, state each requirement once.
Source: https://claude.com/blog/what-a-task-costs-on-opus-5-5

## CC-OBSERVABILITY
Why: With no `statusLine` configured, cache and context state are invisible turn to turn, so rebuilds and context creep go unnoticed until they've already cost tokens.
Fix: Configure a `statusLine` (`prompt_cache`, `context_window` fields); check `/usage` (v2.1.251+) for the Prompt cache line and per-skill/plugin/MCP attribution, and `/context` for startup composition.
Source: https://code.claude.com/docs/en/statusline, https://code.claude.com/docs/en/costs

## CX-AGENTSMD-CAP
Why: The combined AGENTS.md chain is read only up to `project_doc_max_bytes` (default 32 KiB); anything past the cap is silently dropped, so late sections of a long chain may never reach the model.
Fix: Raise `project_doc_max_bytes` in `~/.codex/config.toml`, or split guidance across nested directories/files instead of one growing root file.
Source: https://developers.openai.com/codex/config-advanced

## CX-CACHE
Why: `cached_input_tokens / input_tokens` from `token_count.info.total_token_usage` well below ~90% means most sessions are re-processing history instead of reusing cache.
Fix: Avoid switching model or reasoning effort mid-session; keep related work in one session rather than restarting threads.
Source: https://developers.openai.com/codex/config-reference

## CX-LONGCTX
Why: p90 context fill (`last_token_usage.input_tokens / model_context_window`) close to 1.0 means sessions are running up against the model's window before Codex compacts.
Fix: Lower `model_auto_compact_token_limit` in `config.toml` so compaction triggers earlier and more predictably.
Source: https://developers.openai.com/codex/config-advanced

## CX-MCP
Why: Each configured `[mcp_servers.<name>]` loads its tool set; `enabled` with no `enabled_tools` allowlist exposes every tool the server has.
Fix: Set `enabled = false` for unused servers; add an `enabled_tools` allowlist to scope the ones you keep.
Source: https://developers.openai.com/codex/mcp

## CX-EFFORT
Why: A global `model_reasoning_effort` of high/xhigh/max (or the same on `plan_mode_reasoning_effort`) applies that cost to every request, including ones that don't need it.
Fix: Set `model_reasoning_effort` (and `plan_mode_reasoning_effort` separately if plan mode runs often) to the lowest level that holds for your typical task.
Source: https://developers.openai.com/codex/config-reference

## CX-SKILLS
Why: Codex's initial skill listing is capped at `skills.max_context_tokens` in `config.toml` when set, else about 2% of the latest session's `model_context_window`, else 8,000 chars when neither is known; once installed skills exceed that budget, some are prioritized by description and others omitted with a warning. A skill disabled via a `[[skills.config]]` entry (`enabled = false`, matched by its SKILL.md path or folder) never competes for that budget and is excluded from the count.
Fix: Trim skill descriptions, or remove/consolidate skills in `~/.agents/skills` (and `~/.codex/skills` if present) that don't need to compete for that budget.
Source: https://learn.chatgpt.com/docs/build-skills

## CU-RULES
Why: `.cursor/rules/*.mdc` with `alwaysApply: true` (and a legacy `.cursorrules`) load on every request regardless of relevance; cursor-agent also reads AGENTS.md and CLAUDE.md as rules, so the same guidance can load twice.
Fix: Prefer `globs` or `description`-triggered rules over `alwaysApply`; migrate a legacy `.cursorrules` into scoped `.cursor/rules/*.mdc` files.
Source: https://cursor.com/docs/rules

## AG-RULES
Why: Antigravity reads global rules from `~/.gemini/GEMINI.md`/`AGENTS.md` and `~/.gemini/config/rules/*.md`, plus workspace `AGENTS.md`/`GEMINI.md` and `.agents/rules/*.md`; each rules/workflow file is capped at 12,000 chars, and large ones load on every session.
Fix: Keep GEMINI.md/CLAUDE.md as thin entry points that reference one shared AGENTS.md; split large rule files under the 12,000-char cap.
Source: https://ai.google.dev/gemini-api/docs/antigravity-agent

## GM-CONTEXT
Why: Gemini CLI compresses chat history once usage crosses `model.compressionThreshold` (fraction of the context window, default 0.5); a large GEMINI.md chain (`context.fileName`) pushes toward that threshold sooner every session.
Fix: Lower `model.compressionThreshold` in `settings.json` if long sessions run out of room before compacting; trim the GEMINI.md chain.
Source: https://geminicli.com/docs/cli/settings

## CD-MCP-UNUSED
Why: A configured Desktop MCP server with no matching `method` lines in its `~/Library/Logs/Claude/mcp-server-*.log` (or `mcp.log`) in the lookback window was never actually called.
Fix: Disable the connector in Claude Desktop settings; removing it from `claude_desktop_config.json`'s `mcpServers` is the user's call.
Source: https://modelcontextprotocol.io/quickstart/user

## X-DUP-INSTR
Why: CLAUDE.md, AGENTS.md, and GEMINI.md sitting in the same directory with high line overlap and no `@AGENTS.md` import mean the same instructions load twice, once per tool that reads its own file.
Fix: Keep one source of truth, AGENTS.md, and add `@AGENTS.md` at the top of CLAUDE.md (and the equivalent for GEMINI.md) so tool-specific files stay thin imports.
Source: https://code.claude.com/docs/en/memory

## X-MCP-INLINE-SECRET
Why: A literal token/key value inside a committed `.mcp.json` (or any tool's MCP config) ships the secret to everyone who reads the repo, and to the server's own logs.
Fix: Replace literal values with `${VAR}` env references and set the actual value outside the file (shell env, secrets manager); rotate any credential already committed.
Source: https://code.claude.com/docs/en/mcp

## HABITS
- Run `/clear` between unrelated tasks, not mid-task; a fresh session avoids carrying a long context into unrelated work.
- Run `/compact <focus>` before a break, not after; the cache is often still warm when you stop and cold once you return.
- Prefer `/rewind` over `/compact` when you just need to drop the last few turns; it cuts turns without burning a compaction pass.
- @-mention files instead of asking Claude to search for them; it skips the exploration tool calls entirely.
- Pipe noisy commands (`gh run watch`, long logs) through quiet flags or a subagent, so the raw output never lands in the main thread.
- Pick model and effort at the start of a session, not partway through; switching either mid-session forces a full, uncached rewrite.
Source: https://claude.com/blog/what-a-task-costs-on-opus-5-5
