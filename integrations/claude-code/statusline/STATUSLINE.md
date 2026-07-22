# Claude Code Statusline

Shows model, git, cost, context, and usage-window information in your Claude Code prompt — computed fresh on every call, no background daemon.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Multiple accounts](#multiple-accounts)
- [Platform support](#platform-support)
- [Troubleshooting](#troubleshooting)

## Overview

The statusline renders two lines:

**Line 1** — model, context, directory, git, cost, session duration:
```
🤖 Opus │ 📊 22% │ 📁 cc-arsenal │ 🌿 main ● │ 💰 $0.043 │ ⏱️ 21m
```

**Line 2** — usage-window details (only when rate-limit data is available):
```
🔄 5h: 16% → 21:00 │ 📅 7d: 39% → Dec 31 21:00
```

Line 1 components, in order:
- 🤖 **Model** — name/version, from `model.display_name` or `model.id`
- 📊 **Context** — `context_window.used_percentage`, rounded
- 📁 **Directory** — current directory, `~`-shortened
- 🌿 **Git** — branch, with `●` for uncommitted changes
- 🌳 **Worktree** — worktree name, shown only when in a worktree
- 💰 **Cost** — `cost.total_cost_usd` for the session
- 📝 **Lines changed** — `+added/-removed`; **disabled by default**, enable via config
- ⏱️ **Session duration** — from `cost.total_duration_ms`; hidden until a session has run

Line 2 is the usage line (see [Usage](#usage) for where its data comes from) plus, when multi-account is configured, an account badge (see [Multiple accounts](#multiple-accounts)).

Git/worktree data prefers the native `worktree.branch`/`worktree.name` fields Claude Code passes on stdin; it only shells out to `git` when those are absent.

## Installation

### Prerequisites
- **bash** and **jq** (jq is used for all JSON parsing; the script degrades to a minimal fallback line without it)
- **git** (for branch/worktree detection when native JSON fields aren't present)

### Quick install

From the cc-arsenal project root:
```bash
make install-statusline
```
This symlinks the statusline directory to `~/.claude/scripts/claude/statusline` and configures `~/.claude/settings.json` to invoke it.

To remove it:
```bash
make uninstall-statusline
```

### Manual installation

```bash
mkdir -p ~/.claude/scripts/claude/statusline/
cp -r integrations/claude-code/statusline/* ~/.claude/scripts/claude/statusline/
chmod +x ~/.claude/scripts/claude/statusline/statusline.sh
```

Add to `~/.claude/settings.json`:
```json
{
  "statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
}
```

Restart Claude Code to pick up the setting.

### Verification

```bash
echo '{"model":{"id":"claude-opus-4-1","display_name":"Opus"},"workspace":{"current_dir":"'$PWD'"},"cost":{"total_cost_usd":0.043}}' \
  | bash ~/.claude/scripts/claude/statusline/statusline.sh
```

## Usage

The statusline runs automatically — Claude Code pipes a JSON status object to it on every interaction (max ~300ms refresh rate per Claude Code docs). No manual step is required.

### The usage line (rate limits)

Line 2 comes from the `rate_limits` object Claude Code includes on stdin (`rate_limits.five_hour` / `rate_limits.seven_day` — `used_percentage` and `resets_at`). This is the default source and needs no configuration.

If nothing is piped in with `rate_limits` (e.g. the interactive/no-stdin fallback), line 2 is simply omitted.

When `CLAUDE_CODE_OAUTH_TOKEN` is set (see [Multiple accounts](#multiple-accounts)), the script instead fetches usage directly from the Anthropic OAuth API for that account and uses it in place of whatever came in on stdin.

### External consumers (tmux, etc.)

On every run, the statusline persists the current rate-limit snapshot to `/tmp` so other tools (a tmux statusbar, a separate script) can read it without re-parsing stdin JSON:

- Default account (no `CLAUDE_CODE_OAUTH_TOKEN` set): `/tmp/claude_rate_limits_cache.json` — a stable, well-known path.
- Per env-token account: `/tmp/claude_rate_limits_cache.<hash>.json`, where `<hash>` is the first 12 hex characters of the SHA-256 of the token value.

Both files contain `{"five_hour": {...}, "seven_day": {...}}`. Treat the default path as stable for scripting; the hashed path is stable per-token but the hash itself is only reproducible if you compute it the same way (`shasum -a 256` truncated to 12 chars).

## Configuration

### Config file

Settings live in `~/.claude/cc-arsenal/statusline_config.json`. This file is **not** auto-created on first run — create or edit it with the interactive tool:

```bash
make configure   # from integrations/claude-code/statusline/
```

which drives `configure_statusline.py` (writes directly to `~/.claude/cc-arsenal/statusline_config.json`).

The config surface is intentionally small — every key here is actually honored by the code (`lib/config.sh`, `lib/display/builder.sh`):

```json
{
  "components": {
    "enabled": {
      "lines_changed": false
    }
  },
  "display": {
    "display_mode": "emoji"
  }
}
```

Unknown keys are ignored, so older config files with extra keys keep working.

To point the script at a different config file entirely (e.g. for previewing a candidate config), set `STATUSLINE_CONFIG_OVERRIDE=/path/to/file.json`.

### Environment variables

| Variable | Effect |
|---|---|
| `STATUSLINE_DISPLAY_MODE` | `emoji` (default), `text`, or `ascii` — overrides the config file's `display.display_mode` |
| `STATUSLINE_TEXT_MODE` | Legacy boolean (`true`/`1`) forcing text mode; superseded by `STATUSLINE_DISPLAY_MODE` |
| `STATUSLINE_CONFIG_OVERRIDE` | Path to an alternate config JSON file, used instead of `~/.claude/cc-arsenal/statusline_config.json` |
| `STATUSLINE_SEPARATOR` | Component separator on line 1 (default `│`) |
| `STATUSLINE_DEBUG` | `1` to log raw input JSON and context-window extraction to `/tmp/claude_statusline_debug.log` |
| `STATUSLINE_PERF` | `1` to print `[perf] <ms>ms` to stderr after each run |
| `CLAUDE_CODE_OAUTH_TOKEN` | Selects a specific account's OAuth token and enables the multi-account code path — see below |
| `CLAUDE_STATUSLINE_ACCOUNT_LABEL` | Badge text shown on line 2 whenever it's set; unset means no badge. Independent of `CLAUDE_CODE_OAUTH_TOKEN` — works with any account-switch mechanism (env token, `CLAUDE_SECURESTORAGE_CONFIG_DIR`, etc.) |
| `OAUTH_USAGE_CACHE_FILE` | Overrides the OAuth usage cache path (otherwise auto-derived, see below) |
| `OAUTH_USAGE_CACHE_TTL` | OAuth usage cache TTL in seconds (default `300`) |

## Multiple accounts

The statusline supports more than one Claude account on the same machine, driven entirely by `CLAUDE_CODE_OAUTH_TOKEN`.

### Precedence

`CLAUDE_CODE_OAUTH_TOKEN`, when set in the environment the statusline runs in (e.g. exported in a project's `.envrc`, or per-tmux-pane), always takes precedence over the OS keychain/credentials-file lookup that the default (single-account) path uses. Unset it to fall back to the default account resolved via macOS Keychain, Linux `secret-tool`, or `~/.claude/.credentials.json`.

### Per-account isolation

Everything scoped to an account is keyed by the first 12 hex characters of `sha256(token)` — **tokens themselves are never written to disk**, only this hash:

- OAuth usage cache: `/tmp/claude_oauth_usage_cache.<hash>.json` (vs. `/tmp/claude_oauth_usage_cache.json` for the default account)
- Rate-limit backoff/lock state (used by the background fetcher): `/tmp/statusline_live_cache/oauth_backoff.<hash>`, `oauth_backoff_count.<hash>`, `oauth_cache.lock.<hash>`
- External-consumer rate-limit snapshot: `/tmp/claude_rate_limits_cache.<hash>.json` (vs. the stable `/tmp/claude_rate_limits_cache.json` for the default account)

This means two accounts running statuslines concurrently (e.g. in separate tmux sessions with different `CLAUDE_CODE_OAUTH_TOKEN` exports) never clobber each other's cache, backoff, or lock state.

### Account badge

Set `CLAUDE_STATUSLINE_ACCOUNT_LABEL` (e.g. `work`, `personal`) to show a badge on line 2:
```
👤 work │ 🔄 5h: 16% → 21:00
```
The label is independent of how you switched accounts — it renders whenever it's set, whether you select the account via `CLAUDE_CODE_OAUTH_TOKEN` or a separate credential store (`CLAUDE_SECURESTORAGE_CONFIG_DIR=~/.claude-alt`). Unset means no badge. Note the per-account usage-cache isolation and background OAuth refresh are still keyed on `CLAUDE_CODE_OAUTH_TOKEN`; with the securestorage path, line-2 usage comes from the `rate_limits` Claude Code sends on stdin for that account.

### Refresh behavior

`statusline.sh` kicks off a background, non-blocking refresh (`lib/oauth_fetcher.sh`) whenever the account's usage cache is older than `OAUTH_USAGE_CACHE_TTL` (default 300s). The statusline itself only ever reads the cache (`fetch_oauth_usage_cached_only`) — it never blocks on network I/O. The fetcher applies its own file locking (`flock`, with a PID-file fallback on systems without it) and exponential backoff on repeated rate-limit responses from the OAuth API (120s → 300s → 600s).

### Fail-soft behavior

If the OAuth token is invalid, the network call fails, or the cache is simply empty/stale, the statusline falls straight back to whatever `rate_limits` data (if any) arrived on stdin for that call — it never blocks or errors the whole statusline over a failed usage fetch.

## Platform support

- **macOS and Linux**: first-class, actively used code paths (`lib/core/platform.sh` branches on `uname -s` for `stat`, hashing, and date parsing).
- **WSL**: behaves as Linux (uses the Linux branches of `platform.sh`, and the file-based credentials fallback since there's no macOS Keychain).
- **Native Git Bash on Windows**: best-effort, untested — the script sources `sha256sum`/`date -d` style Linux commands as a fallback, which Git Bash generally provides, but this path has no test coverage.

## Troubleshooting

### Statusline not showing

```bash
grep statusline ~/.claude/settings.json
ls -l ~/.claude/scripts/claude/statusline/statusline.sh
chmod +x ~/.claude/scripts/claude/statusline/statusline.sh
```

### Debug a bad or missing value

```bash
STATUSLINE_DEBUG=1 bash -c 'echo "{\"model\":{\"id\":\"test\"}}" | ~/.claude/scripts/claude/statusline/statusline.sh'
tail -20 /tmp/claude_statusline_debug.log
```

### Check timing

```bash
echo '{"model":{"id":"test"}}' | STATUSLINE_PERF=1 ~/.claude/scripts/claude/statusline/statusline.sh
```

### Rate-limit / usage line missing or stale

- No line 2 at all: Claude Code isn't sending `rate_limits` on stdin for this call (normal on very first invocation) — it will appear once available.
- Using `CLAUDE_CODE_OAUTH_TOKEN` and it's stale: check the fetcher's error log and force a fresh fetch:
  ```bash
  tail -20 /tmp/statusline_live_cache/oauth_errors.log
  ~/.claude/scripts/claude/statusline/lib/oauth_fetcher.sh
  ```
- Clear a stuck cache for a specific account (replace `<hash>` or omit it for the default account):
  ```bash
  /bin/rm -f /tmp/claude_oauth_usage_cache.json /tmp/claude_rate_limits_cache.json
  /bin/rm -f /tmp/claude_oauth_usage_cache.<hash>.json /tmp/claude_rate_limits_cache.<hash>.json
  ```

### Git worktree not detected

```bash
git rev-parse --git-dir
git rev-parse --git-common-dir
```
Different output for the two means you're in a worktree — the statusline detects this from git directly whenever `worktree.name`/`worktree.branch` aren't present on stdin.

### Getting help

1. Reproduce with `STATUSLINE_DEBUG=1` (above) and check the log.
2. If it involves usage/rate limits, also check `/tmp/statusline_live_cache/oauth_errors.log`.
3. Open an issue on [GitHub](https://github.com/mgiovani/cc-arsenal/issues) with the debug log, your `~/.claude/settings.json` statusline entry, and steps to reproduce.

---

**Questions or issues?** Open an issue on [GitHub](https://github.com/mgiovani/cc-arsenal/issues) or check the main [cc-arsenal documentation](../../../README.md).
