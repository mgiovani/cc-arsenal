# Browser Agent Command Reference

This reference documents all available browser automation commands for the agent-browser skill. Commands are organized by category for easy navigation.

## Table of Contents

1. [Navigation Commands](#navigation-commands)
2. [Snapshot & Inspection](#snapshot--inspection)
3. [Interaction Commands](#interaction-commands)
4. [Find Commands](#find-commands)
5. [Wait Commands](#wait-commands)
6. [Screenshot Commands](#screenshot-commands)
7. [Settings & Configuration](#settings--configuration)
8. [Advanced Commands](#advanced-commands)
9. [Tab Management](#tab-management)
10. [Network & Console](#network--console)

---

## Navigation Commands

### browser_navigate

Navigate to a specific URL.

**Syntax:**
```json
{
  "url": "https://example.com"
}
```

**Parameters:**
- `url` (string, required): The URL to navigate to. Must be a fully qualified URL including protocol.

**Examples:**
```javascript
// Navigate to a website
{ "url": "https://github.com" }

// Navigate to localhost
{ "url": "http://localhost:3000" }

// Navigate with query parameters
{ "url": "https://example.com/search?q=test" }
```

**Use Cases:**
- Starting a new browsing session
- Navigating to specific pages
- Testing different URLs
- Loading web applications

**Notes:**
- The browser will wait for the page to load before returning
- Failed navigations will return an error
- Redirects are followed automatically

---

### browser_navigate_back

Navigate back to the previous page in browser history.

**Syntax:**
```json
{}
```

**Parameters:**
None

**Examples:**
```javascript
// Go back one page
{}
```

**Use Cases:**
- Returning to previous page after navigation
- Testing browser history
- Multi-page workflows

**Notes:**
- Does nothing if there's no previous page
- Waits for navigation to complete

---

### browser_close

Close the current browser page/session.

**Syntax:**
```json
{}
```

**Parameters:**
None

**Examples:**
```javascript
// Close the browser
{}
```

**Use Cases:**
- Cleaning up after browsing session
- Ending automation workflows
- Resource cleanup

**Notes:**
- Closes the entire browser context
- All tabs will be closed
- Cannot be undone

---

## Snapshot & Inspection

### browser_snapshot

Capture an accessibility snapshot of the current page. This is the primary command for understanding page structure and finding elements to interact with.

**Syntax:**
```json
{
  "filename": "snapshot.md"  // optional
}
```

**Parameters:**
- `filename` (string, optional): Save snapshot to a markdown file instead of returning it in the response.

**Response Format:**

The snapshot returns a hierarchical representation of the page using accessibility roles:

```markdown
[1] button "Submit"
[2] link "Home"
[3] textbox "Email"
[4] heading "Welcome"
[5] navigation
    [6] link "Products"
    [7] link "About"
```

**Understanding the Ref System:**

Each element has a numeric reference (e.g., `[1]`, `[2]`) that you use in interaction commands:
- **Purpose**: Exact element identification for automation
- **Usage**: Pass the ref number to `browser_click`, `browser_type`, etc.
- **Stability**: Refs are stable within a single snapshot but change after page updates
- **Format**: Always use the number without brackets when passing to commands

**Output Interpretation:**

```markdown
[ref] role "accessible_name" additional_info
```

- `ref`: Numeric reference for automation
- `role`: ARIA role (button, link, textbox, etc.)
- `accessible_name`: Human-readable label or text
- `additional_info`: Value, state, or other properties

**Common Roles:**
- `button`: Clickable buttons
- `link`: Hyperlinks
- `textbox`: Input fields
- `combobox`: Dropdowns/select elements
- `checkbox`: Checkboxes
- `radio`: Radio buttons
- `heading`: Headings (h1-h6)
- `navigation`: Navigation containers
- `banner`: Header areas
- `contentinfo`: Footer areas

**Examples:**

```javascript
// Get snapshot as response
{}

// Save snapshot to file
{ "filename": "page-snapshot.md" }
```

**Use Cases:**
- Understanding page structure before interactions
- Finding elements to click or fill
- Debugging automation failures
- Verifying page state
- Documenting page accessibility

**Best Practices:**
- Always take a snapshot before attempting interactions
- Use snapshots to find correct refs for elements
- Re-snapshot after page changes (AJAX, navigation, etc.)
- Prefer semantic roles over generic divs/spans
- Look for accessible names that match user-visible text

**Notes:**
- Better than screenshots for automation (provides actionable refs)
- Respects accessibility tree structure
- Lighter weight than full HTML inspection
- Essential for reliable element selection

---

### browser_evaluate

Execute JavaScript in the browser context.

**Syntax:**
```json
{
  "function": "() => { /* code */ }",
  "element": "Submit button",  // optional
  "ref": "1"  // optional, required if element provided
}
```

**Parameters:**
- `function` (string, required): JavaScript function to execute. Use `() => {}` for page context or `(element) => {}` when element is provided.
- `element` (string, optional): Human-readable element description for permission to interact
- `ref` (string, optional): Element reference from snapshot (required if element is provided)

**Examples:**

```javascript
// Get page title
{
  "function": "() => document.title"
}

// Get element text
{
  "function": "(element) => element.textContent",
  "element": "Submit button",
  "ref": "1"
}

// Execute complex logic
{
  "function": "() => { return { url: window.location.href, title: document.title }; }"
}

// Modify page state
{
  "function": "() => { localStorage.setItem('theme', 'dark'); return true; }"
}
```

**Use Cases:**
- Reading page state
- Getting computed values
- Accessing browser APIs
- Modifying DOM or page state
- Complex data extraction

**Notes:**
- Returns the function's return value
- Has access to full browser context
- Can access element directly when ref is provided
- Use for tasks that aren't covered by other commands

---

## Interaction Commands

### browser_click

Perform a click on an element.

**Syntax:**
```json
{
  "ref": "1",
  "element": "Submit button",
  "button": "left",  // optional
  "modifiers": ["Control"],  // optional
  "doubleClick": false  // optional
}
```

**Parameters:**
- `ref` (string, required): Element reference from snapshot
- `element` (string, required): Human-readable element description
- `button` (string, optional): Mouse button - "left" (default), "right", or "middle"
- `modifiers` (array, optional): Keyboard modifiers - "Alt", "Control", "ControlOrMeta", "Meta", "Shift"
- `doubleClick` (boolean, optional): Perform double-click instead of single click

**Examples:**

```javascript
// Simple click
{
  "ref": "1",
  "element": "Submit button"
}

// Right-click
{
  "ref": "2",
  "element": "Context menu trigger",
  "button": "right"
}

// Ctrl+Click (open in new tab)
{
  "ref": "3",
  "element": "External link",
  "modifiers": ["Control"]
}

// Double-click
{
  "ref": "4",
  "element": "File to open",
  "doubleClick": true
}
```

**Use Cases:**
- Clicking buttons
- Following links
- Opening context menus
- Double-clicking to select
- Modified clicks for special behaviors

**Best Practices:**
- Always get a fresh snapshot before clicking
- Use descriptive element names
- Verify the element exists in snapshot
- Consider wait commands if elements load dynamically

---

### browser_type

Type text into an editable element.

**Syntax:**
```json
{
  "ref": "1",
  "text": "hello@example.com",
  "element": "Email input",
  "slowly": false,  // optional
  "submit": false  // optional
}
```

**Parameters:**
- `ref` (string, required): Element reference from snapshot
- `text` (string, required): Text to type
- `element` (string, optional): Human-readable element description
- `slowly` (boolean, optional): Type one character at a time (useful for triggering key handlers)
- `submit` (boolean, optional): Press Enter after typing

**Examples:**

```javascript
// Type email
{
  "ref": "3",
  "text": "user@example.com",
  "element": "Email input"
}

// Type and submit
{
  "ref": "4",
  "text": "search query",
  "element": "Search box",
  "submit": true
}

// Type slowly to trigger autocomplete
{
  "ref": "5",
  "text": "New York",
  "element": "City input",
  "slowly": true
}
```

**Use Cases:**
- Filling form fields
- Entering search queries
- Inputting credentials
- Triggering autocomplete
- Testing input validation

**Notes:**
- Clears existing text before typing by default
- Use `slowly: true` for inputs with live validation or autocomplete
- `submit: true` is equivalent to pressing Enter after typing

---

### browser_fill_form

Fill multiple form fields in one command.

**Syntax:**
```json
{
  "fields": [
    {
      "name": "Email",
      "type": "textbox",
      "ref": "3",
      "value": "user@example.com"
    },
    {
      "name": "Subscribe",
      "type": "checkbox",
      "ref": "4",
      "value": "true"
    }
  ]
}
```

**Parameters:**
- `fields` (array, required): Array of field objects to fill

**Field Object:**
- `name` (string, required): Human-readable field name
- `type` (string, required): Field type - "textbox", "checkbox", "radio", "combobox", "slider"
- `ref` (string, required): Element reference from snapshot
- `value` (string, required): Value to set (use "true"/"false" for checkboxes)

**Examples:**

```javascript
// Fill login form
{
  "fields": [
    {
      "name": "Username",
      "type": "textbox",
      "ref": "1",
      "value": "john.doe"
    },
    {
      "name": "Password",
      "type": "textbox",
      "ref": "2",
      "value": "secret123"
    },
    {
      "name": "Remember me",
      "type": "checkbox",
      "ref": "3",
      "value": "true"
    }
  ]
}

// Fill signup form
{
  "fields": [
    {
      "name": "Email",
      "type": "textbox",
      "ref": "5",
      "value": "user@example.com"
    },
    {
      "name": "Country",
      "type": "combobox",
      "ref": "6",
      "value": "United States"
    },
    {
      "name": "Age range",
      "type": "radio",
      "ref": "7",
      "value": "18-25"
    }
  ]
}
```

**Use Cases:**
- Filling multi-field forms efficiently
- Registration forms
- Checkout flows
- Survey responses
- Batch data entry

**Notes:**
- More efficient than individual type commands
- All fields are filled before submitting
- Checkbox values must be "true" or "false" strings
- Combobox values should match option text exactly

---

### browser_press_key

Press a keyboard key.

**Syntax:**
```json
{
  "key": "Enter"
}
```

**Parameters:**
- `key` (string, required): Key name or character (e.g., "Enter", "ArrowLeft", "a")

**Common Keys:**
- Navigation: "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "PageUp", "PageDown"
- Editing: "Backspace", "Delete", "Enter", "Tab", "Escape"
- Modifiers: "Shift", "Control", "Alt", "Meta"
- Function: "F1" through "F12"
- Characters: "a", "b", "1", "2", etc.

**Examples:**

```javascript
// Submit form
{ "key": "Enter" }

// Navigate dropdown
{ "key": "ArrowDown" }

// Close dialog
{ "key": "Escape" }

// Select all
{ "key": "Control+a" }
```

**Use Cases:**
- Submitting forms
- Navigating menus/dropdowns
- Keyboard shortcuts
- Closing modals
- Tab navigation

---

### browser_hover

Hover over an element.

**Syntax:**
```json
{
  "ref": "1",
  "element": "Menu item"
}
```

**Parameters:**
- `ref` (string, required): Element reference from snapshot
- `element` (string, required): Human-readable element description

**Examples:**

```javascript
// Hover to show tooltip
{
  "ref": "5",
  "element": "Help icon"
}

// Hover to reveal submenu
{
  "ref": "6",
  "element": "Products menu"
}
```

**Use Cases:**
- Revealing tooltips
- Opening dropdown menus
- Triggering hover effects
- Testing hover states

**Notes:**
- Mouse will remain over element until next action
- Useful for multi-step hover interactions

---

### browser_select_option

Select an option in a dropdown.

**Syntax:**
```json
{
  "ref": "1",
  "element": "Country dropdown",
  "values": ["United States"]
}
```

**Parameters:**
- `ref` (string, required): Element reference from snapshot
- `element` (string, required): Human-readable element description
- `values` (array, required): Array of option values/labels to select

**Examples:**

```javascript
// Select single option
{
  "ref": "3",
  "element": "Country",
  "values": ["United States"]
}

// Select multiple options (multi-select)
{
  "ref": "4",
  "element": "Interests",
  "values": ["Technology", "Design", "Business"]
}
```

**Use Cases:**
- Selecting from dropdowns
- Multi-select lists
- Form completion
- Filtering options

**Notes:**
- For single-select, use array with one value
- Values should match visible option text
- Case-sensitive matching

---

### browser_drag

Perform drag and drop between two elements.

**Syntax:**
```json
{
  "startRef": "1",
  "startElement": "Draggable item",
  "endRef": "2",
  "endElement": "Drop zone"
}
```

**Parameters:**
- `startRef` (string, required): Source element reference from snapshot
- `startElement` (string, required): Human-readable source element description
- `endRef` (string, required): Target element reference from snapshot
- `endElement` (string, required): Human-readable target element description

**Examples:**

```javascript
// Drag file to upload
{
  "startRef": "5",
  "startElement": "File icon",
  "endRef": "6",
  "endElement": "Upload dropzone"
}

// Reorder list items
{
  "startRef": "7",
  "startElement": "Task 1",
  "endRef": "8",
  "endElement": "Position 2"
}
```

**Use Cases:**
- File uploads via drag-drop
- Reordering lists
- Kanban boards
- Visual editors
- Drag-to-select

---

### browser_file_upload

Upload files to file input.

**Syntax:**
```json
{
  "paths": ["/path/to/file1.pdf", "/path/to/file2.jpg"]
}
```

**Parameters:**
- `paths` (array, optional): Absolute paths to files to upload. If omitted, cancels file chooser.

**Examples:**

```javascript
// Upload single file
{
  "paths": ["/home/user/document.pdf"]
}

// Upload multiple files
{
  "paths": [
    "/home/user/photo1.jpg",
    "/home/user/photo2.jpg",
    "/home/user/photo3.jpg"
  ]
}

// Cancel file chooser
{
  "paths": []
}
```

**Use Cases:**
- Uploading documents
- Profile picture uploads
- Batch file uploads
- Testing file input handling

**Notes:**
- Paths must be absolute
- Files must exist on disk
- Omit paths to cancel file selection

---

## Find Commands

Find commands provide semantic alternatives to numeric refs for element selection. They are more readable but may be less precise than snapshot refs.

### Find by Role

Use ARIA roles to find elements.

**Common Roles:**
- `button`: Clickable buttons
- `link`: Hyperlinks
- `textbox`: Input fields
- `heading`: Headings (h1-h6)
- `checkbox`: Checkboxes
- `radio`: Radio buttons
- `combobox`: Select dropdowns
- `dialog`: Modal dialogs
- `navigation`: Navigation areas

**Usage in Commands:**

Instead of using refs, you can specify elements semantically in most interaction commands. However, the Playwright MCP tools primarily use the ref-based approach for reliability.

**Best Practice:**
Use `browser_snapshot` to get refs rather than relying on semantic selectors. Refs are more stable and precise.

---

### Find by Text

While the Playwright MCP doesn't expose direct "find by text" commands, the snapshot provides accessible names that include text content. Use snapshot to locate elements by their visible text.

**Example Workflow:**
1. Take snapshot
2. Search snapshot output for text
3. Use corresponding ref in interaction command

---

### Find by Label

Form fields often have associated labels. In snapshots, the accessible name typically includes the label text.

**Example:**
```markdown
[3] textbox "Email address"  # "Email address" is from the label
```

Use the ref `"3"` to interact with this labeled field.

---

### Find by Test ID

The snapshot doesn't directly expose test IDs, but you can use `browser_evaluate` to find elements by test ID:

```javascript
{
  "function": "() => document.querySelector('[data-testid=\"submit-button\"]').textContent"
}
```

**Best Practice:**
Prefer snapshot refs over test IDs for reliability.

---

## Wait Commands

### browser_wait_for

Wait for specific conditions before proceeding.

**Syntax:**
```json
{
  "text": "Success",  // optional
  "textGone": "Loading...",  // optional
  "time": 2.5  // optional, in seconds
}
```

**Parameters:**
- `text` (string, optional): Wait for this text to appear on the page
- `textGone` (string, optional): Wait for this text to disappear from the page
- `time` (number, optional): Wait for specified seconds

**Examples:**

```javascript
// Wait for success message
{
  "text": "Order confirmed"
}

// Wait for loading to finish
{
  "textGone": "Loading..."
}

// Wait 2 seconds
{
  "time": 2
}

// Wait for text change
{
  "textGone": "Processing...",
  "text": "Complete"
}
```

**Use Cases:**
- Waiting for AJAX to complete
- Waiting for success messages
- Waiting for loading spinners to disappear
- Adding delays between actions
- Waiting for dynamic content

**Notes:**
- Can specify multiple conditions
- All conditions must be met
- Default timeout is typically 30 seconds
- Use `time` for fixed delays, text conditions for dynamic content

---

## Screenshot Commands

### browser_take_screenshot

Capture a screenshot of the page or specific element.

**Syntax:**
```json
{
  "type": "png",
  "filename": "page.png",
  "fullPage": false,
  "element": "Main content",  // optional
  "ref": "5"  // optional
}
```

**Parameters:**
- `type` (string, required): Image format - "png" or "jpeg"
- `filename` (string, optional): File name to save. Defaults to `page-{timestamp}.{png|jpeg}`. Prefer relative names.
- `fullPage` (boolean, optional): Capture full scrollable page instead of viewport. Cannot be used with element screenshots.
- `element` (string, optional): Human-readable element description. If provided, `ref` is required.
- `ref` (string, optional): Element reference from snapshot. If provided, `element` is required.

**Examples:**

```javascript
// Viewport screenshot (PNG)
{
  "type": "png"
}

// Full page screenshot
{
  "type": "png",
  "fullPage": true,
  "filename": "full-page.png"
}

// Element screenshot
{
  "type": "png",
  "element": "Product card",
  "ref": "8",
  "filename": "product.png"
}

// JPEG for smaller size
{
  "type": "jpeg",
  "filename": "page.jpg"
}
```

**Use Cases:**
- Visual regression testing
- Bug reports
- Documentation
- Proof of completion
- Capturing specific components

**Format Comparison:**
- **PNG**: Lossless, larger files, better for UI/text
- **JPEG**: Lossy, smaller files, better for photos

**Best Practices:**
- Use PNG for UI screenshots
- Use JPEG for photo-heavy pages
- Use `fullPage` for documentation
- Use element screenshots to focus on specific areas
- Use relative filenames to stay in output directory

---

## Settings & Configuration

### browser_resize

Resize the browser viewport.

**Syntax:**
```json
{
  "width": 1920,
  "height": 1080
}
```

**Parameters:**
- `width` (number, required): Viewport width in pixels
- `height` (number, required): Viewport height in pixels

**Common Sizes:**
- Desktop: 1920x1080, 1366x768, 1440x900
- Tablet: 768x1024, 1024x768
- Mobile: 375x667 (iPhone), 360x640 (Android)

**Examples:**

```javascript
// Desktop HD
{
  "width": 1920,
  "height": 1080
}

// Tablet portrait
{
  "width": 768,
  "height": 1024
}

// Mobile
{
  "width": 375,
  "height": 667
}
```

**Use Cases:**
- Testing responsive designs
- Capturing screenshots at specific sizes
- Simulating different devices
- Testing viewport-dependent features

**Notes:**
- Page will re-render after resize
- May trigger responsive breakpoints
- Consider taking new snapshot after resize

---

### browser_handle_dialog

Handle browser dialogs (alert, confirm, prompt).

**Syntax:**
```json
{
  "accept": true,
  "promptText": "User input"  // optional, only for prompts
}
```

**Parameters:**
- `accept` (boolean, required): Whether to accept (OK) or dismiss (Cancel) the dialog
- `promptText` (string, optional): Text to enter in prompt dialogs

**Examples:**

```javascript
// Accept alert
{
  "accept": true
}

// Dismiss confirm
{
  "accept": false
}

// Enter text in prompt
{
  "accept": true,
  "promptText": "John Doe"
}
```

**Use Cases:**
- Handling confirmation dialogs
- Responding to alerts
- Testing dialog behavior
- Automating dialog-dependent flows

**Notes:**
- Must be called when dialog is active
- Blocks further automation until handled
- Prompt text is only used for prompt() dialogs

---

### browser_install

Install the browser specified in configuration.

**Syntax:**
```json
{}
```

**Parameters:**
None

**Examples:**
```javascript
// Install browser
{}
```

**Use Cases:**
- Initial setup
- Fixing missing browser errors
- Installing after updates

**Notes:**
- Only needed once per system
- Called automatically if browser is missing
- Downloads and installs Playwright browser binaries

---

## Advanced Commands

### browser_run_code

Run arbitrary Playwright code snippets.

**Syntax:**
```json
{
  "code": "async (page) => { /* Playwright code */ }"
}
```

**Parameters:**
- `code` (string, required): JavaScript function with Playwright code. Receives `page` object.

**Examples:**

```javascript
// Click using Playwright API
{
  "code": "async (page) => { await page.getByRole('button', { name: 'Submit' }).click(); }"
}

// Complex interaction
{
  "code": "async (page) => { const title = await page.title(); await page.screenshot({ path: `${title}.png` }); return title; }"
}

// Multiple actions
{
  "code": "async (page) => { await page.fill('#email', 'user@example.com'); await page.fill('#password', 'secret'); await page.click('button[type=submit]'); }"
}
```

**Use Cases:**
- Advanced Playwright features not exposed by other commands
- Complex multi-step interactions
- Direct access to Playwright API
- Custom automation logic

**Notes:**
- Full Playwright API available
- Return values are captured
- Useful for edge cases
- Requires Playwright knowledge

---

## Tab Management

### browser_tabs

Manage browser tabs (list, create, close, select).

**Syntax:**
```json
{
  "action": "list"  // "list", "new", "close", "select"
  "index": 0  // optional, for close/select
}
```

**Parameters:**
- `action` (string, required): Operation to perform
  - `"list"`: List all open tabs
  - `"new"`: Open new tab
  - `"close"`: Close tab (current if index omitted)
  - `"select"`: Switch to tab by index
- `index` (number, optional): Tab index for close/select operations (0-based)

**Examples:**

```javascript
// List all tabs
{
  "action": "list"
}

// Open new tab
{
  "action": "new"
}

// Close current tab
{
  "action": "close"
}

// Close specific tab
{
  "action": "close",
  "index": 2
}

// Switch to tab
{
  "action": "select",
  "index": 1
}
```

**Use Cases:**
- Multi-tab workflows
- Comparing pages side-by-side
- Managing multiple sessions
- Testing tab-specific behavior

**Notes:**
- Tab indices are 0-based
- Closing last tab closes browser
- New tabs start with about:blank

---

## Network & Console

### browser_console_messages

Retrieve console messages from the browser.

**Syntax:**
```json
{
  "level": "info",
  "filename": "console.txt"  // optional
}
```

**Parameters:**
- `level` (string, required): Minimum severity level - "error", "warning", "info", "debug". Each level includes more severe levels.
- `filename` (string, optional): Save messages to file instead of returning in response

**Examples:**

```javascript
// Get all messages
{
  "level": "debug"
}

// Get warnings and errors
{
  "level": "warning"
}

// Get only errors
{
  "level": "error"
}

// Save to file
{
  "level": "info",
  "filename": "console-output.txt"
}
```

**Use Cases:**
- Debugging JavaScript errors
- Checking console output
- Verifying logging behavior
- Detecting client-side errors

**Notes:**
- Returns logs from last 24 hours
- Level hierarchy: error > warning > info > debug
- Useful for debugging automation failures

---

### browser_network_requests

Get network requests made by the page.

**Syntax:**
```json
{
  "includeStatic": false,
  "filename": "network.txt"  // optional
}
```

**Parameters:**
- `includeStatic` (boolean, required): Whether to include successful static resources (images, fonts, scripts)
- `filename` (string, optional): Save requests to file instead of returning in response

**Examples:**

```javascript
// Get API requests only
{
  "includeStatic": false
}

// Get all requests
{
  "includeStatic": true
}

// Save to file
{
  "includeStatic": false,
  "filename": "api-calls.txt"
}
```

**Use Cases:**
- Analyzing API calls
- Debugging network issues
- Verifying request behavior
- Performance analysis

**Notes:**
- Returns requests since page load
- Includes request/response details
- Static resources can be noisy (images, CSS, JS)

---

## Common Workflows

### Login Flow

```javascript
// 1. Navigate to login page
{ "url": "https://example.com/login" }

// 2. Take snapshot to find form fields
{}

// 3. Fill login form (assuming refs 1, 2 from snapshot)
{
  "fields": [
    { "name": "Email", "type": "textbox", "ref": "1", "value": "user@example.com" },
    { "name": "Password", "type": "textbox", "ref": "2", "value": "secret123" }
  ]
}

// 4. Click submit button (assuming ref 3)
{
  "ref": "3",
  "element": "Submit button"
}

// 5. Wait for success
{
  "text": "Welcome back"
}
```

### Form Filling

```javascript
// 1. Navigate
{ "url": "https://example.com/signup" }

// 2. Snapshot
{}

// 3. Fill all fields at once
{
  "fields": [
    { "name": "Full Name", "type": "textbox", "ref": "1", "value": "John Doe" },
    { "name": "Email", "type": "textbox", "ref": "2", "value": "john@example.com" },
    { "name": "Country", "type": "combobox", "ref": "3", "value": "United States" },
    { "name": "Terms", "type": "checkbox", "ref": "4", "value": "true" }
  ]
}

// 4. Submit
{
  "ref": "5",
  "element": "Create Account"
}
```

### Screenshot Documentation

```javascript
// 1. Navigate
{ "url": "https://example.com/product" }

// 2. Full page screenshot
{
  "type": "png",
  "fullPage": true,
  "filename": "product-page-full.png"
}

// 3. Snapshot to find product card
{}

// 4. Element screenshot (assuming ref 10)
{
  "type": "png",
  "element": "Product card",
  "ref": "10",
  "filename": "product-card.png"
}
```

### Debugging Workflow

```javascript
// 1. Navigate
{ "url": "https://example.com" }

// 2. Check console for errors
{
  "level": "error",
  "filename": "errors.txt"
}

// 3. Check network requests
{
  "includeStatic": false,
  "filename": "api-calls.txt"
}

// 4. Take screenshot for visual check
{
  "type": "png",
  "filename": "debug-screenshot.png"
}

// 5. Snapshot for structure
{
  "filename": "page-structure.md"
}
```

### Responsive Testing

```javascript
// Test desktop
{
  "width": 1920,
  "height": 1080
}
{ "url": "https://example.com" }
{
  "type": "png",
  "filename": "desktop.png"
}

// Test tablet
{
  "width": 768,
  "height": 1024
}
{ "url": "https://example.com" }
{
  "type": "png",
  "filename": "tablet.png"
}

// Test mobile
{
  "width": 375,
  "height": 667
}
{ "url": "https://example.com" }
{
  "type": "png",
  "filename": "mobile.png"
}
```

---

## Best Practices

### Element Selection
1. **Always snapshot first** - Get current page state before interactions
2. **Use refs for reliability** - More stable than semantic selectors
3. **Re-snapshot after changes** - AJAX, navigation, or DOM updates require fresh snapshot
4. **Verify element exists** - Check snapshot before attempting interaction

### Error Handling
1. **Use wait commands** - Wait for elements before interacting
2. **Check console messages** - Debug with `browser_console_messages`
3. **Inspect network** - Verify API calls with `browser_network_requests`
4. **Take screenshots** - Visual confirmation of failures

### Performance
1. **Minimize snapshots** - Only snapshot when needed
2. **Use specific waits** - Wait for text/elements rather than fixed delays
3. **Batch form fills** - Use `browser_fill_form` instead of multiple `browser_type` calls
4. **Close tabs** - Clean up unused tabs to save resources

### Debugging
1. **Enable verbose logging** - Check console messages at debug level
2. **Save outputs to files** - Use filename parameters for large outputs
3. **Take screenshots before/after** - Visual debugging
4. **Inspect network traffic** - Verify API interactions

### Reliability
1. **Wait for dynamic content** - Use `browser_wait_for` for AJAX-loaded content
2. **Handle dialogs promptly** - Don't let alerts block automation
3. **Verify success** - Check for success messages or expected state
4. **Use try-catch patterns** - Plan for failures in complex workflows

---

## Command Quick Reference

| Category | Command | Purpose |
|----------|---------|---------|
| **Navigation** | `browser_navigate` | Go to URL |
| | `browser_navigate_back` | Browser back |
| | `browser_close` | Close browser |
| **Inspection** | `browser_snapshot` | Get page structure + refs |
| | `browser_evaluate` | Run JavaScript |
| **Interaction** | `browser_click` | Click element |
| | `browser_type` | Type text |
| | `browser_fill_form` | Fill multiple fields |
| | `browser_press_key` | Press keyboard key |
| | `browser_hover` | Hover element |
| | `browser_select_option` | Select dropdown option |
| | `browser_drag` | Drag and drop |
| | `browser_file_upload` | Upload files |
| **Waiting** | `browser_wait_for` | Wait for conditions |
| **Screenshots** | `browser_take_screenshot` | Capture image |
| **Settings** | `browser_resize` | Set viewport size |
| | `browser_handle_dialog` | Handle alert/confirm/prompt |
| | `browser_install` | Install browser |
| **Advanced** | `browser_run_code` | Run Playwright code |
| **Tabs** | `browser_tabs` | Manage tabs |
| **Debug** | `browser_console_messages` | Get console logs |
| | `browser_network_requests` | Get network traffic |

---

## Accessibility Notes

All commands respect the accessibility tree:
- Elements must have accessible roles
- Use semantic HTML for best results
- Snapshots show ARIA roles and names
- Prefer labeled form fields
- Test with screen reader users in mind

---

## Version Information

This reference is based on the Playwright MCP plugin for Claude Code. Commands may vary slightly based on plugin version.

For the latest information, refer to the Playwright documentation and Claude Code plugin updates.
