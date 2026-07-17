---
name: agent-browser
description: "Headless browser automation CLI optimized for AI agents — uses accessibility-tree snapshots and @e1-style refs for ~93% less context than raw DOM tools. Use whenever the task needs to interact with a live web page: click, fill forms, log in, extract text/data, take screenshots, test a running web app, or scrape a site. Triggers on 'automate the browser', 'fill this form', 'click the button', 'take a screenshot of the page', 'log into', 'scrape this site', 'test my web app'. Not for Playwright test-suite authoring or CDP/service-worker work needing the full JS API — use Playwright directly for those."
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

**agent-browser** is an open-source browser automation CLI from Vercel Labs, purpose-built for AI agents. Unlike traditional browser automation tools, it's designed from the ground up for LLM interaction with a **snapshot + refs** system that reduces context usage by up to 93% compared to Playwright MCP.

See the comparison table under [When to Use vs Playwright](#when-to-use-vs-playwright) for when this CLI beats DOM-based tools.

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

### Session Management

Always pass `--session` — one named session per project prevents stale daemons from accumulating across parallel Claude Code sessions.

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

## Snapshot + Refs System

The **snapshot** command is the core of agent-browser's AI optimization. It generates an **accessibility tree** - a structured, semantic representation of interactive elements.

### Why Accessibility Trees?

Traditional tools expose full DOM trees with thousands of nodes. Accessibility trees contain **only interactive elements** (buttons, inputs, links) with semantic labels - exactly what AI agents need.

**Comparison:**
- **Full DOM**: 5000+ nodes, 200KB context
- **Accessibility tree**: 50-100 elements, 10KB context
- **Savings**: 93% reduction in token usage

### Snapshot Modes

```bash
# Interactive elements only (recommended for AI)
agent-browser snapshot -i

# Full accessibility tree
agent-browser snapshot

# Compact format (fewer details)
agent-browser snapshot -c

# Limit tree depth (for large pages)
agent-browser snapshot -d 3

# Scope to specific section
agent-browser snapshot -s "#main-content"
```

### Understanding Refs

Refs are **stable identifiers** assigned to interactive elements in snapshots:

```
textbox "Email address" [ref=e1]
  placeholder: "Enter your email"
  required: true

button "Sign In" [ref=e5]
  role: button
  enabled: true
```

Use refs in commands: `@e1`, `@e5`, etc.

**Advantages over CSS selectors:**
- Semantic and human-readable
- Survive DOM changes (stable across re-renders)
- No need to inspect HTML structure
- AI agents can reason about element purpose

## Essential Commands

### Navigation

```bash
# Open URL (auto-prepends https://)
agent-browser open example.com

# History control
agent-browser back
agent-browser forward
agent-browser reload

# Close browser
agent-browser close
```

### Interaction

```bash
# Click elements
agent-browser click @e3
agent-browser dblclick @e5

# Fill forms (clears then types)
agent-browser fill @e1 "text"

# Type text (preserves existing content)
agent-browser type @e2 "additional text"

# Press keys
agent-browser press Enter
agent-browser press "Control+A"

# Checkboxes
agent-browser check @e4
agent-browser uncheck @e4

# Dropdowns
agent-browser select @e6 "Option 2"

# Hover (reveals hidden elements)
agent-browser hover @e7

# Scroll
agent-browser scroll 0 500
agent-browser scrollintoview @e8

# File upload
agent-browser upload @e9 /path/to/file.pdf

# Drag and drop
agent-browser drag @e10 @e11
```

### Information Retrieval

```bash
# Get element data
agent-browser get text @e1
agent-browser get html @e2
agent-browser get value @e3        # Input field value
agent-browser get attr @e4 href    # Attribute value

# Page metadata
agent-browser get title
agent-browser get url

# Element metrics
agent-browser get count ".product-card"
agent-browser get box @e5          # Bounding box coordinates
agent-browser get styles @e6       # Computed CSS
```

### State Verification

```bash
# Check element state before interaction
agent-browser is visible @e1
agent-browser is enabled @e2
agent-browser is checked @e3
```

### Waiting

```bash
# Wait for element
agent-browser wait @e5

# Wait duration (milliseconds)
agent-browser wait 2000

# Wait for text
agent-browser wait --text "Success"

# Wait for URL pattern (glob)
agent-browser wait --url "**/dashboard"

# Wait for network idle
agent-browser wait --load networkidle

# Wait for JavaScript condition
agent-browser wait --fn "document.readyState === 'complete'"
```

### Media Capture

```bash
# Screenshot (PNG)
agent-browser screenshot page.png
agent-browser screenshot page.png --full    # Full page scroll

# PDF export
agent-browser pdf document.pdf

# Video recording (webm)
agent-browser record start demo.webm
agent-browser click @e1
agent-browser record stop
```

## Semantic Find Commands

Alternative to refs - use **human-readable locators** for direct targeting:

```bash
# By ARIA role
find role button click --name "Submit"
find role textbox fill --label "Email" "user@example.com"

# By text content
find text "Click here" click
find text "Exact Match" click --exact

# By form labels
find label "Username" fill "admin"

# By placeholder
find placeholder "Search..." fill "query"

# By alt text (images)
find alt "Logo" click

# By title attribute
find title "Close dialog" click

# By test ID
find testid "submit-btn" click

# Position-based
find first "button" click
find last ".item" click
find nth 2 ".card" click
```

**When to use find vs refs:**
- **Refs** - Reliable, AI-optimized, survives DOM changes
- **Find** - Quick one-off actions, human-readable scripts

## When to Use vs Playwright

| Need | Use | Why |
|---|---|---|
| AI agent driving a browser, CLI-first, minimal tokens | agent-browser | ~93% less context via accessibility-tree snapshots, zero config, `@e1` refs survive DOM changes |
| Multiple isolated sessions in parallel | agent-browser | Built-in `--session` isolation |
| Full JS API, service workers, device emulation, CDP internals | Playwright (direct) | agent-browser doesn't expose the full programmatic API |
| Reusing an existing Playwright test suite | Playwright (direct) | Don't rewrite working tests to switch tools |

## Reference File Guide

Detailed information is available in bundled reference files (loaded on-demand), regenerated from the CLI's own `agent-browser skills get core --full` so they stay in sync with the installed version:

### `references/commands.md`
Every command signature, flag, and alias — navigation, interaction, find, wait, screenshot, settings, tabs, network/console, global flags.

### `references/advanced.md`
Session management, authentication (login flows, OAuth, 2FA, cookie import), trust-boundary safety rules, proxy configuration, and Chrome DevTools profiling.

### `references/workflows.md`
The snapshot + ref model in depth, plus video-recording workflows.

If these ever drift from the CLI again, regenerate with `agent-browser skills get core --full` and re-split (see git history of this file for the split points).

## Resources

### Official Documentation
- **GitHub**: https://github.com/vercel-labs/agent-browser
- **AGENTS.md**: AI agent integration guide
- **Source Code**: Available in `opensrc/` directory

### Environment Variables

```bash
AGENT_BROWSER_IDLE_TIMEOUT_MS   # Auto-close daemon after N ms idle (set 300000 in dotfiles)
AGENT_BROWSER_SESSION           # Default session name (set per-project in CLAUDE.md)
AGENT_BROWSER_ENGINE            # Default engine: chrome | lightpanda
AGENT_BROWSER_EXECUTABLE_PATH   # Custom browser binary path
AGENT_BROWSER_EXTENSIONS        # Comma-separated extension paths
AGENT_BROWSER_PROVIDER          # Cloud provider (browseruse, browserbase, browserless)
AGENT_BROWSER_ENCRYPTION_KEY    # AES-256-GCM key for session state files (64-char hex)
AGENT_BROWSER_STREAM_PORT       # WebSocket port for streaming
AGENT_BROWSER_HOME              # Installation directory
```

### Operational Rules (mgiovani-specific)

- **Always pass `--session <project-name>`** — prevents 4-daemon stale socket accumulation (was causing OOM)
- **Never run `agent-browser close --all`** or `pkill chrome-headless-shell` — breaks other projects' parallel sessions
- **`.claude/browser-profile/` must be in `.gitignore`** — contains plaintext cookies and login tokens
- **Omit `--profile` for stateless work** — persistent profiles accumulate Chrome cache; idle-timeout only reclaims RAM, not disk cache
- **Run `agent-browser doctor --fix`** when sessions feel stuck — cleans stale sockets without killing active sessions
- **For the authoritative, version-matched command reference**: `agent-browser skills get core --full`

### Code Style Requirements

- **No emojis** in code, output, or documentation
- Unicode symbols acceptable: ✓, ✗, →, ⚠
- Use `cli/src/color.rs` for colored output (respects `NO_COLOR`)

### Fetching Dependency Source

```bash
# npm packages
npx opensrc <package>

# Python packages
npx opensrc pypi:<package>

# Rust crates
npx opensrc crates:<package>

# GitHub repos
npx opensrc <owner>/<repo>
```

---

**Quick Reference Card**

```bash
# Navigate
agent-browser open <url>

# Analyze
agent-browser snapshot -i

# Interact
agent-browser click @e1
agent-browser fill @e2 "text"
agent-browser wait @e3

# Verify
agent-browser is visible @e1

# Capture
agent-browser screenshot page.png

# Semantic find
find role button click --name "Submit"
```

**Best Practices:**
1. Always `snapshot -i` before interacting
2. Use refs (`@e1`) for reliability
3. Wait strategically (`--load networkidle`, `--url` patterns)
4. Scope snapshots (`-s` selector) for large pages
5. Verify state (`is visible`, `is enabled`) before interaction
6. Use sessions (`--session`) for isolation
7. Save/load authentication state to avoid repetitive logins
