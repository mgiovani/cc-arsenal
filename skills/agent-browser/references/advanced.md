# Advanced Browser Automation Guide

This reference covers advanced topics for power users working with browser automation through the agent-browser skill.

## Table of Contents

1. [Session Management](#session-management)
2. [Network Interception and Mocking](#network-interception-and-mocking)
3. [Cookies and Storage Manipulation](#cookies-and-storage-manipulation)
4. [Tab and Frame Management](#tab-and-frame-management)
5. [Debugging Tools](#debugging-tools)
6. [Cloud Provider Integration](#cloud-provider-integration)
7. [Playwright MCP vs Direct Playwright](#playwright-mcp-vs-direct-playwright)
8. [Performance Optimization](#performance-optimization)
9. [Advanced Patterns](#advanced-patterns)

---

## Session Management

### Persistent Browser Sessions

The Playwright MCP maintains a single browser instance across multiple operations, providing session persistence without explicit configuration.

**How it works:**
- Browser instance starts on first navigation
- Remains open between operations
- Cookies and localStorage persist automatically
- Authentication state maintained across commands

**Session lifecycle:**
```bash
# First interaction - browser starts
browser_navigate(url="https://example.com/login")

# Fill login form - same session
browser_fill_form(fields=[...])

# Navigate to protected page - authenticated session persists
browser_navigate(url="https://example.com/dashboard")

# Close when done
browser_close()
```

### Browser Profiles and Contexts

While Playwright MCP doesn't expose `--profile` flags directly, you can achieve profile-like behavior through:

**1. Cookie persistence:**
```javascript
// Save authentication state
browser_evaluate(
  function: `() => {
    const state = {
      cookies: document.cookie,
      localStorage: Object.entries(localStorage),
      sessionStorage: Object.entries(sessionStorage)
    };
    return JSON.stringify(state);
  }`
)

// Restore in new session
browser_evaluate(
  function: `() => {
    const state = ${saved_state};
    state.localStorage.forEach(([k,v]) => localStorage.setItem(k,v));
    state.sessionStorage.forEach(([k,v]) => sessionStorage.setItem(k,v));
  }`
)
```

**2. Browser state files:**
Save network requests, cookies, and console logs to files for replay:
```bash
# Capture session state
browser_network_requests(
  filename="session_requests.json",
  includeStatic=false
)

browser_console_messages(
  filename="session_console.log",
  level="info"
)
```

### Window Size and Viewport

Control browser dimensions for responsive testing:
```bash
# Desktop viewport
browser_resize(width=1920, height=1080)

# Tablet
browser_resize(width=768, height=1024)

# Mobile
browser_resize(width=375, height=667)
```

**Headless considerations:**
- Default viewport is typically 1280x720
- Resize before navigation for consistent rendering
- Screenshots respect current viewport unless `fullPage=true`

---

## Network Interception and Mocking

### Monitoring Network Traffic

**Capture all requests:**
```bash
# Navigate and perform actions
browser_navigate(url="https://api-heavy-app.com")
browser_click(ref="submit-button")

# Capture network activity
browser_network_requests(
  includeStatic=false,  # Exclude images, fonts, CSS
  filename="api_calls.json"
)
```

**Output format:**
```json
[
  {
    "url": "https://api.example.com/v1/users",
    "method": "POST",
    "status": 200,
    "timing": "234ms",
    "requestHeaders": {...},
    "responseHeaders": {...},
    "requestBody": {...},
    "responseBody": {...}
  }
]
```

### Request/Response Modification

While Playwright MCP doesn't expose route interception directly, you can modify behavior through JavaScript injection:

**1. Mock API responses:**
```javascript
browser_evaluate(
  function: `() => {
    // Override fetch globally
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
      if (url.includes('/api/users')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({users: [/* mock data */]})
        });
      }
      return originalFetch(url, options);
    };
  }`
)
```

**2. Block specific resources:**
```javascript
browser_evaluate(
  function: `() => {
    // Block analytics scripts
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.tagName === 'SCRIPT' &&
              (node.src?.includes('analytics') ||
               node.src?.includes('tracking'))) {
            node.remove();
          }
        });
      });
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  }`
)
```

**3. Inject custom headers:**
```javascript
browser_evaluate(
  function: `() => {
    // Override XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      const result = originalOpen.call(this, method, url, ...rest);
      this.setRequestHeader('X-Custom-Header', 'value');
      return result;
    };
  }`
)
```

### Analyzing Network Patterns

**Debug failed requests:**
```bash
browser_network_requests(includeStatic=false)
# Look for status codes >= 400
# Check CORS errors
# Identify slow endpoints (>1s)
```

**Monitor real-time network:**
```bash
browser_console_messages(level="error")
# Network errors appear in console
# CORS violations logged
# Failed fetch/XHR requests
```

---

## Cookies and Storage Manipulation

### Cookie Management

**Read cookies:**
```javascript
browser_evaluate(
  function: `() => {
    const cookies = document.cookie.split(';').map(c => {
      const [name, ...value] = c.split('=');
      return {name: name.trim(), value: value.join('=')};
    });
    return cookies;
  }`
)
```

**Set cookies:**
```javascript
browser_evaluate(
  function: `() => {
    document.cookie = "session_id=abc123; path=/; max-age=3600";
    document.cookie = "user_pref=dark_mode; path=/";
  }`
)
```

**Delete specific cookie:**
```javascript
browser_evaluate(
  function: `() => {
    document.cookie = "session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
  }`
)
```

**Clear all cookies:**
```javascript
browser_evaluate(
  function: `() => {
    document.cookie.split(';').forEach(c => {
      const name = c.split('=')[0].trim();
      document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/';
    });
  }`
)
```

### LocalStorage Operations

**Read all localStorage:**
```javascript
browser_evaluate(
  function: `() => {
    const storage = {};
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      storage[key] = localStorage.getItem(key);
    }
    return storage;
  }`
)
```

**Set complex data:**
```javascript
browser_evaluate(
  function: `() => {
    const userData = {
      id: 123,
      preferences: {theme: 'dark', lang: 'en'},
      lastLogin: new Date().toISOString()
    };
    localStorage.setItem('user', JSON.stringify(userData));
  }`
)
```

**Clear storage:**
```javascript
browser_evaluate(
  function: `() => {
    localStorage.clear();
    sessionStorage.clear();
  }`
)
```

### SessionStorage vs LocalStorage

**SessionStorage** (tab-scoped):
- Cleared when tab closes
- Not shared between tabs
- Use for temporary state

**LocalStorage** (domain-scoped):
- Persists across sessions
- Shared between tabs
- Use for user preferences

**IndexedDB access:**
```javascript
browser_evaluate(
  function: `() => {
    return new Promise((resolve) => {
      const request = indexedDB.open('myDatabase');
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('myStore', 'readonly');
        const store = tx.objectStore('myStore');
        const getAllRequest = store.getAll();
        getAllRequest.onsuccess = () => resolve(getAllRequest.result);
      };
    });
  }`
)
```

---

## Tab and Frame Management

### Multiple Tabs

**List tabs:**
```bash
browser_tabs(action="list")
# Returns: [{index: 0, url: "...", title: "..."}]
```

**Open new tab:**
```bash
browser_tabs(action="new")
# Opens blank tab, switches to it
# Returns: {index: 1}
```

**Switch between tabs:**
```bash
browser_tabs(action="select", index=0)  # Switch to first tab
browser_tabs(action="select", index=1)  # Switch to second tab
```

**Close tabs:**
```bash
browser_tabs(action="close", index=1)  # Close specific tab
browser_tabs(action="close")            # Close current tab
```

**Multi-tab workflow:**
```bash
# 1. Open main page
browser_navigate(url="https://example.com")

# 2. Open comparison page in new tab
browser_tabs(action="new")
browser_navigate(url="https://competitor.com")

# 3. Take screenshots of both
browser_take_screenshot(filename="competitor.png")
browser_tabs(action="select", index=0)
browser_take_screenshot(filename="main.png")

# 4. Close extra tabs
browser_tabs(action="close", index=1)
```

### Working with Iframes

**Detect iframes:**
```javascript
browser_evaluate(
  function: `() => {
    const iframes = Array.from(document.querySelectorAll('iframe'));
    return iframes.map(iframe => ({
      src: iframe.src,
      id: iframe.id,
      name: iframe.name
    }));
  }`
)
```

**Access iframe content:**
```javascript
browser_evaluate(
  function: `() => {
    const iframe = document.querySelector('iframe#target');
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    return iframeDoc.querySelector('button').textContent;
  }`
)
```

**Interact with iframe elements:**
```javascript
browser_evaluate(
  function: `() => {
    const iframe = document.querySelector('iframe#payment');
    const iframeDoc = iframe.contentDocument;
    const button = iframeDoc.querySelector('button.submit');
    button.click();
  }`
)
```

**Cross-origin iframe limitations:**
- Cannot access content from different origin
- Use `browser_snapshot()` to see iframe structure
- Some iframes may require separate navigation

### Popup Windows

**Handle new windows:**
```javascript
browser_evaluate(
  function: `() => {
    // Prevent popups from opening
    window.open = function() { return null; };
  }`
)
```

**Detect popup attempts:**
```bash
browser_console_messages(level="warning")
# Check for "popup blocked" messages
```

---

## Debugging Tools

### Console Logging

**Capture console messages:**
```bash
# All messages (debug, info, warning, error)
browser_console_messages(level="debug", filename="full_console.log")

# Only errors
browser_console_messages(level="error", filename="errors.log")

# Only warnings and errors
browser_console_messages(level="warning")
```

**Console message levels:**
- `error`: Only error messages (most critical)
- `warning`: Warnings + errors
- `info`: Info + warnings + errors (default)
- `debug`: All messages including debug logs

**Output format:**
```
[ERROR] 10:23:45 - Uncaught TypeError: Cannot read property 'x' of undefined
  at script.js:45:12

[WARNING] 10:23:50 - Resource blocked by CORS policy
  https://api.example.com/data

[INFO] 10:24:00 - User logged in successfully

[DEBUG] 10:24:05 - State updated: {user: {...}}
```

### Custom Logging

**Inject console interceptor:**
```javascript
browser_evaluate(
  function: `(() => {
    window.__logs = [];
    const methods = ['log', 'warn', 'error', 'info', 'debug'];
    methods.forEach(method => {
      const original = console[method];
      console[method] = function(...args) {
        window.__logs.push({
          level: method,
          message: args.join(' '),
          timestamp: new Date().toISOString(),
          stack: new Error().stack
        });
        original.apply(console, args);
      };
    });
  })()`
)

# Later, retrieve logs
browser_evaluate(
  function: `() => window.__logs`
)
```

### Error Handling

**Catch JavaScript errors:**
```javascript
browser_evaluate(
  function: `() => {
    window.__errors = [];
    window.addEventListener('error', (event) => {
      window.__errors.push({
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        stack: event.error?.stack
      });
    });

    window.addEventListener('unhandledrejection', (event) => {
      window.__errors.push({
        message: 'Unhandled Promise Rejection',
        reason: event.reason,
        promise: event.promise
      });
    });
  })`
)
```

**Check for errors:**
```javascript
browser_evaluate(
  function: `() => window.__errors || []`
)
```

### Screenshot Debugging

**Full page screenshot:**
```bash
browser_take_screenshot(
  type="png",
  fullPage=true,
  filename="full_page_debug.png"
)
```

**Element screenshot:**
```bash
# First get element reference from snapshot
browser_snapshot()
# Find element ref (e.g., "ref_123")

browser_take_screenshot(
  element="Submit button",
  ref="ref_123",
  type="png",
  filename="button_debug.png"
)
```

**Screenshot comparison workflow:**
```bash
# Before action
browser_take_screenshot(filename="before.png")

# Perform action
browser_click(ref="toggle-button")

# After action
browser_take_screenshot(filename="after.png")

# Compare externally using image diff tools
```

### Trace Viewer Integration

While Playwright MCP doesn't expose trace recording directly, you can achieve similar results:

**Record page state over time:**
```bash
# 1. Take initial snapshot
browser_snapshot(filename="state_01_initial.md")

# 2. Perform action
browser_click(ref="nav-link")
browser_snapshot(filename="state_02_after_click.md")

# 3. Fill form
browser_fill_form(fields=[...])
browser_snapshot(filename="state_03_form_filled.md")

# 4. Submit
browser_click(ref="submit")
browser_snapshot(filename="state_04_submitted.md")

# Review snapshots chronologically
```

### Using browser_run_code for Advanced Debugging

**Execute custom Playwright code:**
```bash
browser_run_code(
  code: `async (page) => {
    // Access full Playwright API
    await page.tracing.start({ screenshots: true, snapshots: true });

    await page.goto('https://example.com');
    await page.click('button');

    await page.tracing.stop({ path: 'trace.zip' });

    return { success: true };
  }`
)
```

**Performance metrics:**
```bash
browser_run_code(
  code: `async (page) => {
    const metrics = await page.metrics();
    const performance = await page.evaluate(() =>
      JSON.stringify(window.performance.timing)
    );
    return { metrics, performance };
  }`
)
```

---

## Cloud Provider Integration

### Remote Browser Connections

Playwright supports connecting to remote browsers running in cloud services like BrowserStack, Sauce Labs, or custom Selenium Grid.

**Connect to remote browser:**
```bash
browser_run_code(
  code: `async (page) => {
    // The browser instance is already connected
    // Just use the page normally
    await page.goto('https://example.com');
    return await page.title();
  }`
)
```

**Note:** Remote connection configuration happens outside the MCP layer, typically through environment variables or Playwright config.

### Container-Based Browsers

**Docker integration:**
```bash
# Run Playwright container
docker run -d -p 9323:9323 \
  mcr.microsoft.com/playwright:latest \
  playwright run-server --port 9323

# Configure Playwright to connect
# (Done via environment or config file)
```

**Benefits:**
- Consistent browser versions
- Isolated test environments
- Scalable parallel execution
- Cross-platform compatibility

### Cloud-Specific Considerations

**Network latency:**
- Remote browsers add 50-200ms latency
- Use `browser_wait_for()` more liberally
- Increase timeout defaults

**Resource limits:**
- Cloud providers may limit concurrent sessions
- Monitor usage through provider dashboards
- Implement retry logic for "no capacity" errors

**Debugging remote sessions:**
```bash
# Capture more context for remote debugging
browser_console_messages(level="debug", filename="remote_debug.log")
browser_network_requests(includeStatic=true, filename="remote_network.json")
browser_take_screenshot(fullPage=true, filename="remote_state.png")
```

---

## Playwright MCP vs Direct Playwright

### Architectural Comparison

| Aspect | Playwright MCP | Direct Playwright |
|--------|----------------|-------------------|
| **Integration** | Claude Code native | Code-based API |
| **Setup** | Plugin install | npm/pip install |
| **Language** | Tool calls (any language) | JavaScript/Python/Java/.NET |
| **Context overhead** | ~500 tokens per tool call | Zero (local code) |
| **Learning curve** | Low (natural language) | Medium (API knowledge) |
| **Flexibility** | Limited to exposed tools | Full Playwright API |
| **Debugging** | Console logs, screenshots | DevTools, traces, debugger |
| **CI/CD** | Requires Claude Code | Standard test frameworks |

### Tool Count Comparison

**Playwright MCP Tools (23 total):**
- Navigation: 3 tools (`navigate`, `navigate_back`, `tabs`)
- Interaction: 6 tools (`click`, `type`, `hover`, `drag`, `select_option`, `fill_form`)
- Evaluation: 2 tools (`evaluate`, `run_code`)
- State: 4 tools (`snapshot`, `take_screenshot`, `console_messages`, `network_requests`)
- Control: 5 tools (`wait_for`, `file_upload`, `handle_dialog`, `resize`, `close`)
- Installation: 1 tool (`install`)
- Browser management: 2 tools (`tabs`, `close`)

**Direct Playwright API:**
- 200+ methods on Page object
- 50+ assertions in expect
- 30+ locator methods
- Full event system
- Complete configuration options

### Element Selection Approaches

**Playwright MCP (Snapshot-based):**
```bash
# 1. Take snapshot
browser_snapshot()

# Output shows elements with refs:
# - [ref_1] "Submit" button
# - [ref_2] "Email" textbox
# - [ref_3] "Password" textbox

# 2. Use ref in interactions
browser_click(element="Submit button", ref="ref_1")
browser_type(element="Email textbox", ref="ref_2", text="user@example.com")
```

**Pros:**
- No selector knowledge needed
- Visual reference in markdown
- Permission-based (explicit confirmation)
- Works with dynamic content

**Cons:**
- Requires snapshot before interaction
- Refs may change on re-snapshot
- Extra token overhead (~1000-3000 tokens/snapshot)

**Direct Playwright (Locator-based):**
```javascript
// CSS selectors
await page.click('button.submit');
await page.fill('input[type="email"]', 'user@example.com');

// Text selectors
await page.click('button:has-text("Submit")');

// Role-based (recommended)
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');

// XPath
await page.click('//button[contains(text(), "Submit")]');
```

**Pros:**
- Direct, fast interaction
- Powerful selector engine
- Auto-waiting built-in
- No intermediate steps

**Cons:**
- Requires selector knowledge
- May need page structure familiarity
- Harder to debug selector issues

### Context Overhead Analysis

**Playwright MCP token costs:**

| Operation | Token Cost | Breakdown |
|-----------|-----------|-----------|
| `browser_navigate()` | ~50 tokens | URL + basic response |
| `browser_snapshot()` | 1000-5000 tokens | Full page accessibility tree |
| `browser_click()` | ~100 tokens | Element description + confirmation |
| `browser_take_screenshot()` | 2000-4000 tokens | Image encoding (vision model) |
| `browser_console_messages()` | 500-3000 tokens | Log entries with timestamps |
| `browser_network_requests()` | 1000-5000 tokens | Request/response details |

**Example workflow cost:**
```
1. browser_navigate()         →    50 tokens
2. browser_snapshot()         → 2,000 tokens
3. browser_click() x3         →   300 tokens
4. browser_fill_form()        →   150 tokens
5. browser_snapshot()         → 2,500 tokens (more content)
6. browser_take_screenshot()  → 3,000 tokens
                               ─────────────
                          Total: 8,000 tokens
```

**Direct Playwright has zero context overhead** - all operations are local code execution.

### When to Use Each

**Use Playwright MCP when:**
- ✅ Exploring unfamiliar websites interactively
- ✅ One-off automation tasks
- ✅ Debugging UI issues collaboratively
- ✅ Quick data scraping (< 100 pages)
- ✅ Visual regression testing with human verification
- ✅ Prototyping automation workflows
- ✅ You don't have coding infrastructure set up

**Use Direct Playwright when:**
- ✅ Building production automation
- ✅ Running in CI/CD pipelines
- ✅ High-volume testing (1000+ tests)
- ✅ Performance-critical operations
- ✅ Complex conditional logic
- ✅ Advanced features (video recording, HAR files, network mocking)
- ✅ Integration with test frameworks (Jest, pytest)
- ✅ You need programmatic control

**Hybrid approach:**
```bash
# 1. Use MCP for exploration
browser_navigate(url="https://complex-app.com")
browser_snapshot()  # Understand structure

# 2. Identify selectors
browser_evaluate(
  function: `() => {
    const button = document.querySelector('button.submit');
    return {
      selector: 'button.submit',
      text: button.textContent,
      role: button.getAttribute('role')
    };
  }`
)

# 3. Generate Playwright script
# Based on findings, write: await page.click('button.submit');
# Run in your own codebase for production
```

---

## Performance Optimization

### Reducing Snapshot Overhead

**Problem:** `browser_snapshot()` can consume 1000-5000 tokens per call.

**Solutions:**

1. **Use targeted evaluation instead:**
```javascript
// Instead of full snapshot just to check button state
browser_evaluate(
  function: `() => document.querySelector('button.submit').disabled`
)
```

2. **Cache refs between operations:**
```bash
# Take ONE snapshot
browser_snapshot()
# Note: Submit button is ref_5, Email is ref_2, Password is ref_3

# Use refs for multiple operations without re-snapshotting
browser_type(ref="ref_2", text="user@example.com")
browser_type(ref="ref_3", text="password123")
browser_click(ref="ref_5")
```

3. **Use `browser_run_code()` for multi-step operations:**
```bash
browser_run_code(
  code: `async (page) => {
    await page.fill('input[type="email"]', 'user@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button.submit');
    await page.waitForSelector('.dashboard');
    return { success: true };
  }`
)
# Single operation instead of 4 separate tool calls
```

### Minimizing Network Costs

**Disable unnecessary resources:**
```javascript
browser_evaluate(
  function: `() => {
    // Block images
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.tagName === 'IMG') {
            node.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
          }
        });
      });
    });
    observer.observe(document, { childList: true, subtree: true });
  }`
)
```

**Skip static resources in network logs:**
```bash
browser_network_requests(
  includeStatic=false  # Excludes images, fonts, CSS
)
```

### Batch Operations

**Fill multiple fields at once:**
```bash
browser_fill_form(
  fields=[
    {name: "Email", type: "textbox", ref: "ref_2", value: "user@example.com"},
    {name: "Password", type: "textbox", ref: "ref_3", value: "password123"},
    {name: "Remember me", type: "checkbox", ref: "ref_4", value: "true"},
    {name: "Country", type: "combobox", ref: "ref_5", value: "United States"}
  ]
)
# One tool call instead of 4
```

### Wait Optimization

**Avoid fixed waits:**
```bash
# ❌ Bad: arbitrary wait
browser_wait_for(time=5)  # May be too long or too short

# ✅ Good: wait for specific condition
browser_wait_for(text="Dashboard")  # Waits until text appears
```

**Combined wait and action:**
```bash
browser_run_code(
  code: `async (page) => {
    await page.click('button.submit');
    await page.waitForResponse(
      resp => resp.url().includes('/api/login') && resp.status() === 200
    );
    return { success: true };
  }`
)
```

---

## Advanced Patterns

### Scraping with Pagination

```bash
# Pattern 1: Fixed number of pages
browser_navigate(url="https://example.com/items?page=1")

for page in 1..10:
  browser_snapshot(filename=f"page_{page}.md")

  # Extract data
  browser_evaluate(
    function: `() => {
      return Array.from(document.querySelectorAll('.item')).map(item => ({
        title: item.querySelector('h2').textContent,
        price: item.querySelector('.price').textContent
      }));
    }`
  )

  # Next page
  browser_click(ref="next-page-ref")
  browser_wait_for(text="Page ${page + 1}")
```

### Form Automation with Validation

```bash
# 1. Fill form
browser_fill_form(fields=[...])

# 2. Check for validation errors
browser_evaluate(
  function: `() => {
    const errors = document.querySelectorAll('.field-error');
    return Array.from(errors).map(e => ({
      field: e.closest('.form-field').querySelector('label').textContent,
      message: e.textContent
    }));
  }`
)

# 3. If errors, correct and retry
# 4. If no errors, submit
```

### Dynamic Content Loading

```bash
# Scroll to trigger lazy loading
browser_evaluate(
  function: `() => {
    window.scrollTo(0, document.body.scrollHeight);
  }`
)

# Wait for new content
browser_wait_for(text="Load more")  # Or specific element

# Repeat until all content loaded
```

### Testing with Multiple Viewports

```bash
# Desktop test
browser_resize(width=1920, height=1080)
browser_navigate(url="https://example.com")
browser_take_screenshot(filename="desktop.png")

# Tablet test
browser_resize(width=768, height=1024)
browser_navigate(url="https://example.com")
browser_take_screenshot(filename="tablet.png")

# Mobile test
browser_resize(width=375, height=667)
browser_navigate(url="https://example.com")
browser_take_screenshot(filename="mobile.png")
```

### Authentication Persistence

```bash
# 1. Login once
browser_navigate(url="https://app.example.com/login")
browser_fill_form(fields=[...])
browser_click(ref="submit")
browser_wait_for(text="Dashboard")

# 2. Save authentication
browser_evaluate(
  function: `() => {
    return {
      cookies: document.cookie,
      localStorage: JSON.stringify(localStorage),
      sessionStorage: JSON.stringify(sessionStorage)
    };
  }`
)
# Save result to file: auth_state.json

# 3. In new session, restore
browser_navigate(url="https://app.example.com")
browser_evaluate(
  function: `() => {
    const state = ${saved_auth_state};

    // Restore cookies
    state.cookies.split(';').forEach(cookie => {
      document.cookie = cookie.trim();
    });

    // Restore storage
    const local = JSON.parse(state.localStorage);
    Object.keys(local).forEach(key => {
      localStorage.setItem(key, local[key]);
    });
  }`
)
browser_navigate(url="https://app.example.com/dashboard")
# Already authenticated!
```

### Error Recovery Patterns

```bash
# Pattern: Retry with exponential backoff
for attempt in 1..3:
  try:
    browser_navigate(url="https://flaky-site.com")
    browser_wait_for(text="Content loaded", time=5)
    break  # Success
  except:
    if attempt < 3:
      wait(2 ** attempt)  # 2s, 4s, 8s
    else:
      # Final attempt failed
      browser_console_messages(level="error", filename="failure.log")
      browser_take_screenshot(filename="error_state.png")
      raise
```

### Data Extraction Pattern

```bash
# 1. Navigate to page
browser_navigate(url="https://data-site.com")

# 2. Wait for content
browser_wait_for(text="Results")

# 3. Extract structured data
data = browser_evaluate(
  function: `() => {
    return Array.from(document.querySelectorAll('.data-row')).map(row => ({
      id: row.dataset.id,
      title: row.querySelector('.title').textContent.trim(),
      value: parseFloat(row.querySelector('.value').textContent),
      timestamp: row.querySelector('.timestamp').getAttribute('datetime')
    }));
  }`
)

# 4. Save to file
# Write data to JSON file

# 5. Handle pagination
if has_next_page:
  browser_click(ref="next-page")
  # Repeat from step 2
```

---

## Troubleshooting Guide

### Common Issues

**1. Element not found:**
```bash
# ❌ Problem: Ref from old snapshot
browser_click(ref="ref_123")  # Error: ref not found

# ✅ Solution: Take fresh snapshot
browser_snapshot()
# Use new ref from output
browser_click(ref="ref_456")
```

**2. Timeout errors:**
```bash
# ❌ Problem: Page not fully loaded
browser_click(ref="ref_1")  # Error: element not ready

# ✅ Solution: Wait for specific condition
browser_wait_for(text="Page loaded")
browser_click(ref="ref_1")
```

**3. Dialog blocking interaction:**
```bash
# ❌ Problem: Alert dialog prevents clicks
browser_click(ref="ref_1")  # Error: dialog open

# ✅ Solution: Handle dialog first
browser_handle_dialog(accept=true)
browser_click(ref="ref_1")
```

**4. File upload not working:**
```bash
# ❌ Problem: File chooser not triggered
browser_file_upload(paths=["/path/to/file.pdf"])  # Error: no file chooser

# ✅ Solution: Click upload button first
browser_click(ref="upload-button")
# This opens file chooser
browser_file_upload(paths=["/path/to/file.pdf"])
```

### Debug Checklist

When automation fails, check in this order:

1. **Console errors:** `browser_console_messages(level="error")`
2. **Network failures:** `browser_network_requests(includeStatic=false)`
3. **Visual state:** `browser_take_screenshot(fullPage=true)`
4. **Page structure:** `browser_snapshot()`
5. **JavaScript errors:** Custom error listener (see Debugging Tools)

---

## Best Practices Summary

1. **Minimize snapshots:** Use `browser_evaluate()` for simple checks
2. **Batch operations:** Use `browser_fill_form()` and `browser_run_code()`
3. **Wait intelligently:** Wait for specific text/elements, not arbitrary times
4. **Handle errors:** Check console logs and network requests
5. **Save session state:** Export cookies/storage for reuse
6. **Use refs efficiently:** Take one snapshot, use refs for multiple operations
7. **Debug with files:** Save console logs, network requests, screenshots
8. **Choose the right tool:** MCP for exploration, Direct Playwright for production

---

## Further Resources

- **Playwright Documentation:** https://playwright.dev/docs/intro
- **Playwright MCP GitHub:** https://github.com/executeautomation/playwright-mcp-server
- **Browser DevTools:** Use Chrome/Firefox DevTools for selector discovery
- **Claude Code Docs:** https://docs.anthropic.com/claude/docs/claude-code

For basic usage, see `basics.md`. For workflow patterns, see `workflows.md`.
