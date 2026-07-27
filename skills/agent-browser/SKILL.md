---
name: agent-browser
description: "Headless browser automation CLI optimized for AI agents: drives a real browser via accessibility-tree snapshots and @e1-style refs for ~93% less context than raw DOM tools. Use whenever a task needs to interact with a live web page: click, fill forms, log in, extract text or data, take screenshots, test a running web app, or scrape a site. Triggers on 'automate the browser', 'fill this form', 'click the button', 'take a screenshot of the page', 'log into', 'scrape this site', 'test my web app', 'headless browser'. Not for Playwright test-suite authoring or CDP/service-worker work needing the full JS API: use Playwright directly. Not for driving the user's own already-open, logged-in Chrome tab: use claude-in-chrome for that."
hooks:
  Stop:
    - hooks:
      - type: command
        command: "agent-browser close --session \"$(basename \"$(pwd)\" 2>/dev/null)\" 2>/dev/null || agent-browser close 2>/dev/null || true"
        once: true
        timeout: 10
---

# agent-browser

## Overview

**agent-browser** is an open-source browser automation CLI from Vercel Labs, built for LLM interaction with a **snapshot + refs** system: instead of a full DOM, `snapshot` returns an accessibility tree of just the interactive elements (buttons, inputs, links) with semantic labels, each tagged with a stable `@e1`-style ref. Full DOM dumps run 5000+ nodes / 200KB of context; an accessibility-tree snapshot is 50-100 elements / ~10KB, roughly a 93% reduction. Refs also survive re-renders, so they don't need re-deriving after every DOM tweak the way CSS selectors do.

See [When to Use vs Playwright](#when-to-use-vs-playwright) for when this CLI beats DOM-based tools.

### Installation

```bash
# macOS (preferred — managed by Homebrew)
brew install agent-browser

# Linux / fallback
npm install -g agent-browser

# Install browser binaries after either method
agent-browser install

# Linux: also install system dependencies
agent-browser install --with-deps

# Verify health
agent-browser doctor
```

## Quick Start

### Basic Workflow

```bash
# 1. Navigate to a page
agent-browser open https://example.com

# 2. Get snapshot with refs
agent-browser snapshot -i

# Output shows:
# textbox "Email" [ref=e1]
# textbox "Password" [ref=e2]
# button "Submit" [ref=e3]

# 3. Interact using refs
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3

# 4. Wait and verify
agent-browser wait --load networkidle
agent-browser snapshot -i
```

Refs are invalidated whenever the page changes (navigation, dropdown opening,
DOM re-render). Re-run `snapshot -i` after any action that could change the
page before reusing a ref: an ref from before the action may now point at a
different element or nothing at all.

### Session Management

Always pass `--session`: one named session per project prevents stale
daemons from accumulating across parallel agent sessions.

```bash
# Use project name as session (run this pattern everywhere)
agent-browser --session "$(basename "$PWD")" open https://app.com

# Authenticated flows: add persistent profile (gitignored)
agent-browser --session "$(basename "$PWD")" --profile .claude/browser-profile open https://app.com/login

# Stateless scraping/extraction: use Lightpanda instead (10x less memory)
agent-browser --session "$(basename "$PWD")" --engine lightpanda open https://public-site.com

# List all active sessions
agent-browser session list

# Diagnose + clean stale sockets (run when things feel wrong)
agent-browser doctor --fix

# Close this project's session only (never use --all with parallel projects)
agent-browser close --session "$(basename "$PWD")"
```

### Engine Choice

| Task | Engine | Why |
|---|---|---|
| Testing your own app, screenshots, React/SPA | `chrome` (default) | Full rendering, CDP, JS |
| Authenticated flows needing saved login | `chrome` + `--profile` | Persistent storage state |
| Bulk scraping / data extraction from public pages | `lightpanda` | 10x less memory, 10x faster |
| Paginated crawls, `get text` at scale | `lightpanda` | Ephemeral, no cache buildup |
| Extensions, headed mode, file access | `chrome` (required) | Lightpanda can't do these |

Rule: **if it only reads public pages and needs no login or screenshot → Lightpanda. Otherwise Chrome.**

## Command Cheat Sheet

```bash
agent-browser --session "$(basename "$PWD")" open <url>   # navigate
agent-browser snapshot -i                                  # get @refs
agent-browser click @e1                                    # click
agent-browser fill @e2 "text"                               # fill a field
agent-browser wait --load networkidle                       # wait for load
agent-browser get text @e3                                  # read element
agent-browser is visible @e1                                 # verify state
agent-browser screenshot page.png                            # capture
agent-browser close --session "$(basename "$PWD")"          # cleanup
```

Full command surface (navigation, all interactions, `find` semantic
locators, waits, screenshots/video, tabs, network, cookies, auth, MCP server,
global flags) lives in [references/commands.md](references/commands.md).

## Verify Before You Claim

Browser automation's core failure mode is confidently reporting page state
nobody actually read. Before writing any claim into your final report:

- **Every claimed value traces to a command.** A total, a heading, a success
  banner: read it with `get text` / `get value` (or a `snapshot` that
  covers it) and quote the exact string returned. Never restate a value from
  the test plan or a product label as if it were observed on the page.
- **`snapshot -i` hides non-interactive content.** Totals, prices, and
  confirmation banners often live in a `<span>`/`<div>`, not a button or
  input: `-i` won't surface them. Use plain `snapshot` or
  `get text <selector>` to reach them.
- **A screenshot filename is a claim.** Confirm you're on the expected page
  (`get url` or a snapshot heading) immediately before calling `screenshot`,
  and name the file after what you just confirmed, not what you set out to
  capture.
- **Own every process you start.** If the task needs a local server to test
  against, announce it when you start it (command, port, PID) and stop it
  before finishing: state the kill explicitly. "Closed the browser session"
  is not the same claim as "shut down the app."

## Worked Examples

### Login and verify

```bash
agent-browser --session myapp open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser get url               # confirm redirected off /login
agent-browser close --session myapp
```

### Scrape a public listing (stateless)

```bash
agent-browser --session catalog --engine lightpanda open https://shop.example.com/catalog
agent-browser get count ".product-card"
agent-browser snapshot -i -s ".product-card"
agent-browser close --session catalog
```

### Verify state before asserting success

```bash
agent-browser --session checkout open http://localhost:3000/cart
agent-browser snapshot -i
agent-browser click @e4             # Add to cart
agent-browser get text .cart-total  # read the total — e.g. "$9.99" — don't assume it changed
agent-browser click @e9             # Checkout
agent-browser wait --url "**/confirmation"
agent-browser get text @e2          # read the confirmation heading
agent-browser close --session checkout
```

Report only the strings those two `get text` calls actually returned, not
a number copied from the test plan.

### Test an app you started locally

```bash
python3 -m http.server 3111 --directory ./dist &   # note the PID
echo "started static server on :3111, pid $!"
agent-browser --session localtest open http://localhost:3111
agent-browser snapshot -i
agent-browser get url                # confirm you're on the expected page first
agent-browser screenshot cart-page.png              # name matches what get url just confirmed
agent-browser close --session localtest
kill %1                              # stop the server you started, before declaring done
echo "stopped server on :3111"
```

## When to Use vs Playwright

| Need | Use | Why |
|---|---|---|
| AI agent driving a browser, CLI-first, minimal tokens | agent-browser | ~93% less context via accessibility-tree snapshots, zero config, `@e1` refs survive DOM changes |
| Multiple isolated sessions in parallel | agent-browser | Built-in `--session` isolation |
| Full JS API, service workers, device emulation, CDP internals | Playwright (direct) | agent-browser doesn't expose the full programmatic API |
| Reusing an existing Playwright test suite | Playwright (direct) | Don't rewrite working tests to switch tools |
| Interacting with the user's already-open, logged-in Chrome tab | claude-in-chrome | agent-browser drives its own separate browser instance, not the user's live session |

## Reference File Guide

Detailed reference material lives in bundled files, loaded on-demand, and is
regenerated from the CLI's own `agent-browser skills get core --full` so it
stays in sync with the installed version. Load each only when the task
needs it:

- **[references/commands.md](references/commands.md)**: load when you need a command signature, flag, or alias not covered by the cheat sheet above (navigation, interaction, `find`, wait, screenshot/video, settings, tabs, frames, network/console, MCP server, global flags).
- **[references/advanced.md](references/advanced.md)**: load for session-state persistence, authentication (login flows, OAuth, 2FA, cookie import), trust-boundary safety rules, proxy configuration, or Chrome DevTools profiling.
- **[references/workflows.md](references/workflows.md)**: load for the snapshot + ref model in depth, or video-recording patterns.

If these ever drift from the installed CLI, regenerate with
`agent-browser skills get core --full` and re-split (see git history of this
file for the split points).

## Resources

### Official Documentation

- **GitHub**: https://github.com/vercel-labs/agent-browser
- **AGENTS.md**: AI agent integration guide, bundled with the CLI
- **CLI source**: `npx opensrc vercel-labs/agent-browser` (fetches the actual source for reference: there is no vendored copy in this skill)

### Environment Variables

```bash
AGENT_BROWSER_IDLE_TIMEOUT_MS   # Auto-close daemon after N ms idle (set 300000 in dotfiles)
AGENT_BROWSER_SESSION           # Default session name (set per-project in your agent config file)
AGENT_BROWSER_ENGINE            # Default engine: chrome | lightpanda
AGENT_BROWSER_EXECUTABLE_PATH   # Custom browser binary path
AGENT_BROWSER_EXTENSIONS        # Comma-separated extension paths
AGENT_BROWSER_PROVIDER          # Cloud provider (browseruse, browserbase, browserless)
AGENT_BROWSER_ENCRYPTION_KEY    # AES-256-GCM key for session state files (64-char hex)
AGENT_BROWSER_STREAM_PORT       # WebSocket port for streaming
AGENT_BROWSER_HOME              # Installation directory
```

### Operational Rules

- **Always pass `--session <project-name>`**: prevents stale-socket accumulation across parallel sessions (can cause daemon OOM)
- **Never run `agent-browser close --all`** or kill the browser process globally: breaks other projects' parallel sessions
- **Persistent profile directories (e.g. `.claude/browser-profile/`) must be in `.gitignore`**: they contain plaintext cookies and login tokens
- **Omit `--profile` for stateless work**: persistent profiles accumulate browser cache; idle-timeout only reclaims RAM, not disk cache
- **Run `agent-browser doctor --fix`** when sessions feel stuck: cleans stale sockets without killing active sessions
- **A test-target server you started is your process to stop**: `agent-browser close` only tears down the browser session, not an app server; kill it explicitly and say so (see [Verify Before You Claim](#verify-before-you-claim))
- **For the authoritative, version-matched command reference**: `agent-browser skills get core --full`
