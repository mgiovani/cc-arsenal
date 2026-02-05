---
name: agent-browser
description: "Headless browser automation CLI optimized for AI agents. Uses snapshot + refs system for 93% less context overhead vs Playwright. Purpose-built for web testing, form automation, screenshots, and data extraction."
hooks:
  Stop:
    - hooks:
      - type: command
        command: "agent-browser close 2>/dev/null || true"
        once: true
        timeout: 10
---

# agent-browser

## Overview

**agent-browser** is an open-source browser automation CLI from Vercel Labs, purpose-built for AI agents. Unlike traditional browser automation tools, it's designed from the ground up for LLM interaction with a **snapshot + refs** system that reduces context usage by up to 93% compared to Playwright MCP.

### Key Advantages

- **93% less context overhead** - Accessibility tree snapshots instead of full DOM
- **Zero configuration** - Ready to use after installation
- **Semantic element targeting** - `@e1` refs instead of fragile CSS selectors
- **Rust + Node.js architecture** - Fast CLI with robust browser control
- **Session isolation** - Run multiple browsers with separate state
- **AI-optimized output** - Structured data perfect for LLM parsing

### Architecture

Three-layer design for performance and reliability:
1. **Rust CLI** - Fast command parsing and daemon communication
2. **Node.js Daemon** - Playwright-based browser lifecycle management
3. **Fallback Mode** - Pure Node.js when native binaries unavailable

### Installation

```bash
# Install globally via npm
npm install -g agent-browser

# Install browser dependencies
agent-browser install

# Linux: Install system dependencies
agent-browser install --with-deps
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

```bash
# Run multiple isolated browsers
agent-browser --session auth open https://app.com/login
agent-browser --session test open https://staging.com

# List all active sessions
agent-browser session list

# Clean up
agent-browser --session auth close
```

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

### Use agent-browser when:

✓ **AI agent automation** - Optimized for LLM workflows
✓ **CLI-first workflows** - Simple command-line usage
✓ **Context efficiency matters** - 93% less token overhead
✓ **Rapid prototyping** - Zero configuration needed
✓ **Multiple sessions** - Easy session isolation
✓ **Semantic targeting** - Prefer accessibility tree over DOM

### Use Playwright MCP when:

✓ **Complex programmatic control** - Full JavaScript API
✓ **Advanced browser features** - Service workers, device emulation
✓ **Existing Playwright tests** - Reuse test infrastructure
✓ **Fine-grained control** - Direct access to CDP
✓ **TypeScript integration** - Type-safe browser automation

**Summary**: agent-browser excels at **AI-driven automation** with minimal context. Playwright excels at **programmatic control** with maximum flexibility.

## Reference File Guide

Detailed information is available in bundled reference files (loaded on-demand):

### `references/command-reference.md`
Complete command documentation including:
- All command signatures and options
- Browser configuration (viewport, geolocation, headers)
- Storage management (cookies, localStorage)
- Network interception and mocking
- Multi-tab/window/frame operations
- Dialog handling
- JavaScript execution (`eval`)
- Global flags and environment variables

### `references/advanced-patterns.md`
Advanced usage patterns:
- Authentication state persistence
- Parallel session workflows
- Network request interception
- File download handling
- Custom proxy configuration
- Cloud provider integration (BrowserUse, BrowserBase)
- Video recording workflows
- CDP (Chrome DevTools Protocol) integration

### `references/best-practices.md`
Optimization and reliability guidance:
- Token efficiency strategies
- Error handling patterns
- Performance optimization
- Debugging techniques
- Common pitfalls and solutions
- Production deployment considerations

### `references/examples.md`
Real-world scenarios:
- E-commerce checkout automation
- Form submission and validation
- Web scraping with pagination
- Screenshot testing
- Data extraction workflows
- Multi-step authentication

## Resources

### Official Documentation
- **GitHub**: https://github.com/vercel-labs/agent-browser
- **AGENTS.md**: AI agent integration guide
- **Source Code**: Available in `opensrc/` directory

### Environment Variables

```bash
AGENT_BROWSER_SESSION           # Default session name
AGENT_BROWSER_EXECUTABLE_PATH   # Custom browser binary
AGENT_BROWSER_EXTENSIONS        # Comma-separated extension paths
AGENT_BROWSER_PROVIDER          # Cloud provider (browseruse, browserbase)
AGENT_BROWSER_STREAM_PORT       # WebSocket port for streaming
AGENT_BROWSER_HOME              # Installation directory
```

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
