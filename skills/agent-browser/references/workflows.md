# Browser Automation Workflows

Practical patterns and real-world scenarios for browser automation using agent-browser.

## Table of Contents

1. [Form Submission Patterns](#form-submission-patterns)
2. [Web Scraping Workflows](#web-scraping-workflows)
3. [Authentication & Session Management](#authentication--session-management)
4. [Data Extraction](#data-extraction)
5. [Multi-Step Form Wizards](#multi-step-form-wizards)
6. [E-Commerce Checkout Flows](#e-commerce-checkout-flows)

---

## Form Submission Patterns

### Simple Contact Form

**Scenario:** Submit a contact form with name, email, and message fields.

**Workflow:**

```markdown
1. Navigate to contact page
2. Take snapshot to identify form fields
3. Fill all fields using browser_fill_form
4. Click submit button
5. Wait for confirmation message
6. Take screenshot of success page
```

**Commands:**

```javascript
// Step 1: Navigate
browser_navigate({ url: "https://example.com/contact" })

// Step 2: Get field references
browser_snapshot()

// Step 3: Fill form (after identifying refs from snapshot)
browser_fill_form({
  fields: [
    {
      name: "Full Name",
      type: "textbox",
      ref: "ref-1234",
      value: "John Doe"
    },
    {
      name: "Email Address",
      type: "textbox",
      ref: "ref-5678",
      value: "john@example.com"
    },
    {
      name: "Message",
      type: "textbox",
      ref: "ref-9012",
      value: "I'd like to inquire about your services"
    }
  ]
})

// Step 4: Submit
browser_click({ element: "Submit button", ref: "ref-3456" })

// Step 5: Wait for confirmation
browser_wait_for({ text: "Thank you for contacting us" })

// Step 6: Capture result
browser_take_screenshot({ filename: "contact-confirmation.png" })
```

**Common Pitfalls:**

- Not waiting for page load after navigation (form fields won't be visible)
- Using wrong field type (e.g., "text" instead of "textbox")
- Submitting before all fields are filled (causes validation errors)

**Best Practices:**

- Always take snapshot before interacting with form
- Use descriptive field names for clarity
- Group related fields in single fill_form call for atomic operations
- Wait for confirmation message rather than fixed timeout

### Form with File Upload

**Scenario:** Job application form with resume upload.

**Workflow:**

```javascript
// Navigate to application page
browser_navigate({ url: "https://careers.example.com/apply" })

// Fill basic information
browser_snapshot()
browser_fill_form({
  fields: [
    { name: "First Name", type: "textbox", ref: "ref-101", value: "Jane" },
    { name: "Last Name", type: "textbox", ref: "ref-102", value: "Smith" },
    { name: "Email", type: "textbox", ref: "ref-103", value: "jane@example.com" }
  ]
})

// Upload resume (after clicking upload button triggers file chooser)
browser_click({ element: "Upload Resume button", ref: "ref-104" })
browser_file_upload({
  paths: ["/home/user/documents/resume.pdf"]
})

// Submit application
browser_click({ element: "Submit Application", ref: "ref-105" })
browser_wait_for({ text: "Application submitted successfully" })
```

**Best Practices:**

- Use absolute paths for file uploads
- Ensure file exists before starting workflow
- Handle file chooser cancellation with empty paths array
- Wait for upload completion indicator before submitting

### Dynamic Forms with Conditional Fields

**Scenario:** Registration form where selecting "Other" in country dropdown reveals additional fields.

**Workflow:**

```javascript
// Fill initial fields
browser_fill_form({
  fields: [
    { name: "Email", type: "textbox", ref: "ref-201", value: "user@example.com" },
    { name: "Country", type: "combobox", ref: "ref-202", value: "Other" }
  ]
})

// Wait for conditional field to appear
browser_wait_for({ text: "Please specify your country" })

// Take new snapshot to get reference for new field
browser_snapshot()

// Fill conditional field
browser_type({
  element: "Country specification field",
  ref: "ref-203",
  text: "Antarctica"
})
```

**Common Pitfalls:**

- Not waiting for conditional fields to render
- Using stale refs from initial snapshot
- Assuming field visibility without checking

---

## Web Scraping Workflows

### Extract Article Content

**Scenario:** Scrape blog post title, author, date, and content.

**Workflow:**

```javascript
// Navigate to article
browser_navigate({ url: "https://blog.example.com/post/123" })

// Get page structure
browser_snapshot({ filename: "article-structure.md" })

// Extract structured data using JavaScript
const articleData = browser_evaluate({
  element: "article content",
  function: `() => {
    return {
      title: document.querySelector('h1.post-title')?.innerText,
      author: document.querySelector('.author-name')?.innerText,
      date: document.querySelector('time')?.getAttribute('datetime'),
      content: document.querySelector('.post-content')?.innerText,
      tags: Array.from(document.querySelectorAll('.tag')).map(t => t.innerText)
    };
  }`
})
```

**Best Practices:**

- Use CSS selectors specific to target site
- Handle missing elements with optional chaining (?.)
- Extract structured data in single evaluate call to reduce round trips
- Save snapshots for debugging selector issues

### Multi-Page Scraping with Pagination

**Scenario:** Scrape all products from e-commerce category with pagination.

**Workflow:**

```javascript
const products = [];
let hasNextPage = true;
let currentPage = 1;

while (hasNextPage) {
  console.log(`Scraping page ${currentPage}...`);

  // Get products on current page
  const pageProducts = browser_evaluate({
    element: "product list",
    function: `() => {
      return Array.from(document.querySelectorAll('.product-card')).map(card => ({
        name: card.querySelector('.product-name')?.innerText,
        price: card.querySelector('.product-price')?.innerText,
        url: card.querySelector('a')?.href,
        image: card.querySelector('img')?.src
      }));
    }`
  });

  products.push(...pageProducts);

  // Check for next page
  browser_snapshot();
  const nextButton = /* identify from snapshot */;

  if (nextButton && !nextButton.disabled) {
    browser_click({ element: "Next page button", ref: nextButton.ref });
    browser_wait_for({ time: 2 }); // Wait for page load
    currentPage++;
  } else {
    hasNextPage = false;
  }
}

// Save results
console.log(`Scraped ${products.length} products across ${currentPage} pages`);
```

**Common Pitfalls:**

- Not checking if next button is disabled
- Infinite loops when pagination detection fails
- Rate limiting from too-fast requests

**Best Practices:**

- Add delays between page loads
- Implement max page limit as safety mechanism
- Save intermediate results in case of failures
- Check for "disabled" or "inactive" state on pagination buttons

### Scraping with Infinite Scroll

**Scenario:** Extract posts from social media feed with infinite scroll.

**Workflow:**

```javascript
let previousHeight = 0;
let unchangedCount = 0;
const maxUnchanged = 3;

while (unchangedCount < maxUnchanged) {
  // Scroll to bottom
  browser_evaluate({
    element: "page body",
    function: `() => {
      window.scrollTo(0, document.body.scrollHeight);
    }`
  });

  // Wait for content to load
  browser_wait_for({ time: 2 });

  // Check if new content loaded
  const currentHeight = browser_evaluate({
    element: "page body",
    function: `() => document.body.scrollHeight`
  });

  if (currentHeight === previousHeight) {
    unchangedCount++;
  } else {
    unchangedCount = 0;
    previousHeight = currentHeight;
  }
}

// Extract all posts after scrolling complete
const posts = browser_evaluate({
  element: "feed container",
  function: `() => {
    return Array.from(document.querySelectorAll('.post')).map(post => ({
      author: post.querySelector('.author')?.innerText,
      content: post.querySelector('.content')?.innerText,
      timestamp: post.querySelector('.timestamp')?.innerText,
      likes: post.querySelector('.likes')?.innerText
    }));
  }`
});
```

**Best Practices:**

- Detect scroll completion by checking page height stability
- Implement maximum unchanged count to prevent infinite loops
- Wait between scrolls for content to load
- Extract data once at the end rather than incrementally

---

## Authentication & Session Management

### Basic Login Flow

**Scenario:** Login to web application and maintain session.

**Workflow:**

```javascript
// Navigate to login page
browser_navigate({ url: "https://app.example.com/login" })

// Fill credentials
browser_snapshot()
browser_fill_form({
  fields: [
    {
      name: "Username",
      type: "textbox",
      ref: "ref-301",
      value: "user@example.com"
    },
    {
      name: "Password",
      type: "textbox",
      ref: "ref-302",
      value: "SecurePassword123!"
    }
  ]
})

// Submit login
browser_click({ element: "Login button", ref: "ref-303" })

// Wait for dashboard
browser_wait_for({ text: "Welcome" })

// Verify successful login
browser_take_screenshot({ filename: "logged-in-dashboard.png" })

// Now perform authenticated actions
browser_navigate({ url: "https://app.example.com/settings" })
// ... continue workflow
```

**Security Best Practices:**

- Never hardcode credentials in scripts
- Use environment variables for sensitive data
- Clear browser data after sensitive operations
- Implement session timeout handling

### Session Persistence Across Tasks

**Scenario:** Login once and reuse session for multiple operations.

**Workflow:**

```javascript
// Initial login (run once)
function performLogin() {
  browser_navigate({ url: "https://app.example.com/login" });
  browser_fill_form({
    fields: [
      { name: "Email", type: "textbox", ref: "ref-401", value: process.env.APP_EMAIL },
      { name: "Password", type: "textbox", ref: "ref-402", value: process.env.APP_PASSWORD }
    ]
  });
  browser_click({ element: "Login", ref: "ref-403" });
  browser_wait_for({ text: "Dashboard" });
}

// Check if already logged in
browser_navigate({ url: "https://app.example.com/dashboard" });
browser_snapshot();

// If not logged in (redirected to login page)
if (/* snapshot shows login page */) {
  performLogin();
}

// Perform authenticated operations
// Session is maintained across subsequent navigate calls
browser_navigate({ url: "https://app.example.com/reports" });
// ... extract data
```

**Best Practices:**

- Check authentication state before re-logging in
- Don't close browser between related operations
- Handle session expiry gracefully
- Use browser_tabs to manage multiple authenticated sessions

### OAuth/Social Login

**Scenario:** Login using "Continue with Google" button.

**Workflow:**

```javascript
// Click social login button
browser_navigate({ url: "https://app.example.com/login" });
browser_snapshot();
browser_click({ element: "Continue with Google button", ref: "ref-501" });

// Wait for OAuth popup/redirect
browser_wait_for({ text: "Sign in with Google" });

// Fill Google credentials
browser_snapshot();
browser_type({
  element: "Email field",
  ref: "ref-502",
  text: "user@gmail.com",
  submit: true
});

browser_wait_for({ text: "Welcome" });
browser_type({
  element: "Password field",
  ref: "ref-503",
  text: process.env.GOOGLE_PASSWORD,
  submit: true
});

// Handle consent screen if appears
browser_wait_for({ time: 2 });
browser_snapshot();

if (/* snapshot shows consent screen */) {
  browser_click({ element: "Continue button", ref: "ref-504" });
}

// Wait for redirect back to app
browser_wait_for({ text: "Dashboard" });
```

**Common Pitfalls:**

- OAuth popups may be blocked by popup blockers
- Consent screens don't always appear
- Account selection if multiple Google accounts

**Best Practices:**

- Handle both popup and redirect OAuth flows
- Implement conditional consent screen handling
- Add extra wait times for external service redirects

---

## Data Extraction

### Extract Table Data

**Scenario:** Export pricing table to structured format.

**Workflow:**

```javascript
browser_navigate({ url: "https://example.com/pricing" });

// Extract table data
const pricingData = browser_evaluate({
  element: "pricing table",
  function: `() => {
    const table = document.querySelector('table.pricing');
    const headers = Array.from(table.querySelectorAll('thead th'))
      .map(th => th.innerText.trim());

    const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
      const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
      return Object.fromEntries(
        headers.map((header, i) => [header, cells[i]])
      );
    });

    return rows;
  }`
});

// Result: Array of objects like:
// [
//   { "Plan": "Starter", "Price": "$9/mo", "Features": "10 users" },
//   { "Plan": "Pro", "Price": "$29/mo", "Features": "50 users" },
// ]
```

**Best Practices:**

- Use thead/tbody structure when available
- Handle tables with rowspan/colspan carefully
- Extract headers dynamically for flexibility
- Return structured JSON for easy processing

### Extract List Items with Metadata

**Scenario:** Scrape job listings with title, company, location, and posted date.

**Workflow:**

```javascript
browser_navigate({ url: "https://jobs.example.com/search?q=developer" });

// Wait for results to load
browser_wait_for({ text: "results found" });

// Extract job listings
const jobs = browser_evaluate({
  element: "job listings container",
  function: `() => {
    return Array.from(document.querySelectorAll('.job-card')).map((card, index) => {
      const titleEl = card.querySelector('.job-title');
      const companyEl = card.querySelector('.company-name');
      const locationEl = card.querySelector('.location');
      const dateEl = card.querySelector('.posted-date');
      const salaryEl = card.querySelector('.salary');

      return {
        id: index + 1,
        title: titleEl?.innerText?.trim() || 'N/A',
        company: companyEl?.innerText?.trim() || 'N/A',
        location: locationEl?.innerText?.trim() || 'N/A',
        postedDate: dateEl?.innerText?.trim() || 'N/A',
        salary: salaryEl?.innerText?.trim() || 'Not disclosed',
        url: card.querySelector('a')?.href || '',
        isRemote: card.classList.contains('remote') ||
                  locationEl?.innerText?.includes('Remote') || false
      };
    });
  }`
});

console.log(`Found ${jobs.length} job listings`);
```

**Best Practices:**

- Provide fallback values for missing data
- Extract Boolean flags from classes or text content
- Include URLs for follow-up navigation
- Number items for reference

### Extract Data Across Multiple Detail Pages

**Scenario:** Get summary from listing page, then visit each item for full details.

**Workflow:**

```javascript
// Get list of product URLs
browser_navigate({ url: "https://shop.example.com/category/electronics" });

const productUrls = browser_evaluate({
  element: "product grid",
  function: `() => {
    return Array.from(document.querySelectorAll('.product-card a'))
      .map(a => a.href);
  }`
});

// Visit each product page for details
const products = [];

for (const url of productUrls.slice(0, 10)) { // Limit to first 10
  browser_navigate({ url });
  browser_wait_for({ time: 1 });

  const details = browser_evaluate({
    element: "product details",
    function: `() => {
      return {
        name: document.querySelector('h1.product-name')?.innerText,
        price: document.querySelector('.price')?.innerText,
        description: document.querySelector('.description')?.innerText,
        specs: Array.from(document.querySelectorAll('.spec-row')).map(row => ({
          label: row.querySelector('.spec-label')?.innerText,
          value: row.querySelector('.spec-value')?.innerText
        })),
        images: Array.from(document.querySelectorAll('.product-image img'))
          .map(img => img.src),
        inStock: !document.querySelector('.out-of-stock')
      };
    }`
  });

  products.push(details);

  // Be polite to server
  browser_wait_for({ time: 1 });
}
```

**Common Pitfalls:**

- Not rate limiting detail page requests
- Memory issues with too many pages
- Navigation errors breaking entire loop

**Best Practices:**

- Implement retry logic for failed navigations
- Save progress incrementally
- Add rate limiting between requests
- Use slice() to test on subset first

---

## Multi-Step Form Wizards

### Registration Wizard (3 Steps)

**Scenario:** Multi-page registration with account, profile, and preferences steps.

**Workflow:**

```javascript
// Step 1: Account Information
browser_navigate({ url: "https://app.example.com/signup" });
browser_snapshot();

browser_fill_form({
  fields: [
    { name: "Email", type: "textbox", ref: "ref-601", value: "newuser@example.com" },
    { name: "Password", type: "textbox", ref: "ref-602", value: "SecurePass123!" },
    { name: "Confirm Password", type: "textbox", ref: "ref-603", value: "SecurePass123!" }
  ]
});

browser_click({ element: "Next button", ref: "ref-604" });
browser_wait_for({ text: "Step 2" });

// Step 2: Profile Information
browser_snapshot();

browser_fill_form({
  fields: [
    { name: "First Name", type: "textbox", ref: "ref-605", value: "John" },
    { name: "Last Name", type: "textbox", ref: "ref-606", value: "Doe" },
    { name: "Phone", type: "textbox", ref: "ref-607", value: "+1234567890" }
  ]
});

browser_click({ element: "Next button", ref: "ref-608" });
browser_wait_for({ text: "Step 3" });

// Step 3: Preferences
browser_snapshot();

browser_fill_form({
  fields: [
    {
      name: "Email notifications",
      type: "checkbox",
      ref: "ref-609",
      value: "true"
    },
    {
      name: "Language",
      type: "combobox",
      ref: "ref-610",
      value: "English"
    }
  ]
});

browser_click({ element: "Complete Registration", ref: "ref-611" });
browser_wait_for({ text: "Welcome to the platform" });

// Verify registration success
browser_take_screenshot({ filename: "registration-complete.png" });
```

**Best Practices:**

- Take snapshot at each step to get fresh refs
- Wait for step transition indicators
- Validate current step before proceeding
- Handle back navigation if needed
- Save progress indicators for debugging

### Survey with Conditional Logic

**Scenario:** Survey where answers trigger different follow-up questions.

**Workflow:**

```javascript
browser_navigate({ url: "https://survey.example.com/start" });

// Question 1: Are you a current customer?
browser_snapshot();
browser_click({ element: "Yes radio button", ref: "ref-701" });
browser_click({ element: "Next", ref: "ref-702" });

// Question 2: (Only for current customers) How satisfied are you?
browser_wait_for({ text: "How satisfied" });
browser_snapshot();
browser_click({ element: "Very satisfied", ref: "ref-703" });
browser_click({ element: "Next", ref: "ref-704" });

// Question 3: (Conditional) Would you recommend us?
browser_wait_for({ text: "recommend" });
browser_snapshot();

// Use slider for rating
browser_fill_form({
  fields: [{
    name: "Recommendation score",
    type: "slider",
    ref: "ref-705",
    value: "9"
  }]
});

browser_click({ element: "Submit Survey", ref: "ref-706" });
browser_wait_for({ text: "Thank you" });
```

**Common Pitfalls:**

- Assuming question sequence (conditional logic changes flow)
- Not waiting for conditional questions to appear
- Using refs from previous questions

**Best Practices:**

- Snapshot at each question to handle conditional flow
- Use wait_for with question text to confirm correct question loaded
- Implement decision tree logic matching survey structure

---

## E-Commerce Checkout Flows

### Complete Purchase Flow

**Scenario:** Add item to cart, proceed through checkout, complete purchase.

**Workflow:**

```javascript
// Browse and add to cart
browser_navigate({ url: "https://shop.example.com/product/laptop-123" });
browser_snapshot();

browser_click({ element: "Add to Cart button", ref: "ref-801" });
browser_wait_for({ text: "Added to cart" });

// Go to cart
browser_click({ element: "View Cart", ref: "ref-802" });
browser_wait_for({ text: "Shopping Cart" });

// Proceed to checkout
browser_snapshot();
browser_click({ element: "Proceed to Checkout", ref: "ref-803" });
browser_wait_for({ text: "Checkout" });

// Shipping information
browser_snapshot();
browser_fill_form({
  fields: [
    { name: "Full Name", type: "textbox", ref: "ref-804", value: "John Doe" },
    { name: "Address", type: "textbox", ref: "ref-805", value: "123 Main St" },
    { name: "City", type: "textbox", ref: "ref-806", value: "New York" },
    { name: "State", type: "combobox", ref: "ref-807", value: "NY" },
    { name: "ZIP Code", type: "textbox", ref: "ref-808", value: "10001" }
  ]
});

browser_click({ element: "Continue to Payment", ref: "ref-809" });
browser_wait_for({ text: "Payment Information" });

// Payment information (use test card for demo)
browser_snapshot();
browser_fill_form({
  fields: [
    { name: "Card Number", type: "textbox", ref: "ref-810", value: "4242424242424242" },
    { name: "Expiry", type: "textbox", ref: "ref-811", value: "12/25" },
    { name: "CVV", type: "textbox", ref: "ref-812", value: "123" },
    { name: "Cardholder Name", type: "textbox", ref: "ref-813", value: "John Doe" }
  ]
});

// Review and place order
browser_click({ element: "Review Order", ref: "ref-814" });
browser_wait_for({ text: "Order Summary" });

browser_snapshot();
browser_click({ element: "Place Order", ref: "ref-815" });
browser_wait_for({ text: "Order Confirmed" });

// Extract order number
const orderNumber = browser_evaluate({
  element: "order confirmation",
  function: `() => {
    return document.querySelector('.order-number')?.innerText;
  }`
});

browser_take_screenshot({ filename: `order-${orderNumber}.png` });
console.log(`Order completed: ${orderNumber}`);
```

**Security Considerations:**

- Never use real payment information in automated tests
- Use payment gateway test/sandbox mode
- Clear sensitive data after completion
- Implement proper error handling for payment failures

### Shopping Cart Management

**Scenario:** Add multiple items, update quantities, apply coupon, checkout.

**Workflow:**

```javascript
// Add first item
browser_navigate({ url: "https://shop.example.com/product/item1" });
browser_click({ element: "Add to Cart", ref: "ref-901" });
browser_wait_for({ text: "Added" });

// Add second item
browser_navigate({ url: "https://shop.example.com/product/item2" });
browser_click({ element: "Add to Cart", ref: "ref-902" });
browser_wait_for({ text: "Added" });

// Go to cart
browser_navigate({ url: "https://shop.example.com/cart" });
browser_snapshot();

// Update quantity of first item
browser_click({ element: "Increase quantity for Item 1", ref: "ref-903" });
browser_wait_for({ time: 1 }); // Wait for price recalculation

// Apply coupon code
browser_type({
  element: "Coupon code field",
  ref: "ref-904",
  text: "SAVE20"
});
browser_click({ element: "Apply Coupon", ref: "ref-905" });
browser_wait_for({ text: "Coupon applied" });

// Verify discount applied
const cartTotal = browser_evaluate({
  element: "cart summary",
  function: `() => {
    return {
      subtotal: document.querySelector('.subtotal')?.innerText,
      discount: document.querySelector('.discount')?.innerText,
      total: document.querySelector('.total')?.innerText
    };
  }`
});

console.log('Cart totals:', cartTotal);

// Proceed to checkout
browser_click({ element: "Checkout", ref: "ref-906" });
```

**Best Practices:**

- Wait for price recalculations after quantity changes
- Verify coupon application success
- Extract and verify totals before checkout
- Handle invalid coupon codes gracefully

### Guest vs. Registered Checkout

**Scenario:** Handle both checkout paths based on user state.

**Workflow:**

```javascript
browser_navigate({ url: "https://shop.example.com/checkout" });
browser_snapshot();

// Check if login option appears
const checkoutType = browser_evaluate({
  element: "checkout options",
  function: `() => {
    return {
      hasGuestCheckout: !!document.querySelector('.guest-checkout'),
      hasLoginOption: !!document.querySelector('.login-option'),
      hasRegisteredUser: !!document.querySelector('.welcome-back')
    };
  }`
});

if (checkoutType.hasRegisteredUser) {
  // Already logged in, proceed directly
  console.log('Continuing as registered user');

} else if (checkoutType.hasLoginOption) {
  // Choose guest checkout
  browser_click({ element: "Continue as Guest", ref: "ref-1001" });
  browser_wait_for({ text: "Guest Checkout" });

  // Fill guest information
  browser_fill_form({
    fields: [
      { name: "Email", type: "textbox", ref: "ref-1002", value: "guest@example.com" },
      { name: "First Name", type: "textbox", ref: "ref-1003", value: "Guest" },
      { name: "Last Name", type: "textbox", ref: "ref-1004", value: "User" }
    ]
  });
}

// Continue with common checkout flow...
```

**Best Practices:**

- Detect checkout type dynamically
- Handle all three scenarios: guest, login, already logged in
- Provide appropriate user information based on checkout type
- Test both paths regularly

---

## Advanced Patterns

### Handling Dialogs and Alerts

**Scenario:** Confirm action that triggers browser alert.

**Workflow:**

```javascript
// Click delete button that triggers confirmation dialog
browser_click({ element: "Delete Account", ref: "ref-1101" });

// Handle confirmation dialog
browser_handle_dialog({ accept: true });

// Or for prompt dialogs
browser_handle_dialog({
  accept: true,
  promptText: "DELETE" // Type required confirmation text
});

browser_wait_for({ text: "Account deleted" });
```

### Multiple Tabs Management

**Scenario:** Open link in new tab, extract data, return to original tab.

**Workflow:**

```javascript
// List current tabs
browser_tabs({ action: "list" });
// Current tabs: [{ index: 0, title: "Home Page", url: "...", active: true }]

// Open new tab
browser_tabs({ action: "new" });
// New tab opened at index 1

// Navigate in new tab
browser_navigate({ url: "https://example.com/report" });
const reportData = browser_evaluate({
  element: "report",
  function: `() => document.querySelector('.report-data')?.innerText`
});

// Switch back to original tab
browser_tabs({ action: "select", index: 0 });

// Close the report tab
browser_tabs({ action: "close", index: 1 });
```

### Network Monitoring

**Scenario:** Track API calls made during page interaction.

**Workflow:**

```javascript
// Navigate to page
browser_navigate({ url: "https://app.example.com/dashboard" });

// Perform actions that trigger API calls
browser_click({ element: "Load More", ref: "ref-1201" });
browser_wait_for({ time: 2 });

// Get network requests
browser_network_requests({
  includeStatic: false,
  filename: "api-calls.txt"
});

// Analyze for specific endpoints
const requests = /* parse from file */;
const apiCalls = requests.filter(r => r.url.includes('/api/'));
console.log(`Made ${apiCalls.length} API calls`);
```

### Console Error Monitoring

**Scenario:** Check for JavaScript errors during workflow.

**Workflow:**

```javascript
// Perform user actions
browser_navigate({ url: "https://app.example.com" });
browser_click({ element: "Complex Feature", ref: "ref-1301" });

// Check console for errors
browser_console_messages({
  level: "error",
  filename: "console-errors.txt"
});

// If errors found, take screenshot for debugging
const errors = /* read from file */;
if (errors.length > 0) {
  console.log(`Found ${errors.length} console errors`);
  browser_take_screenshot({ filename: "error-state.png" });
}
```

---

## Troubleshooting Common Issues

### Element Not Found

**Problem:** Reference invalid or element not visible.

**Solution:**
```javascript
// Always take fresh snapshot before interacting
browser_snapshot();

// Wait for element to appear if it's dynamically loaded
browser_wait_for({ text: "Expected element text" });

// Then get fresh refs and interact
browser_snapshot();
browser_click({ element: "...", ref: "new-ref" });
```

### Form Submission Fails Validation

**Problem:** Required fields not filled or validation fails.

**Solution:**
```javascript
// Fill all required fields in single call
browser_fill_form({ fields: [...] });

// Check for validation messages
browser_snapshot();

// If validation error appears, fix and resubmit
if (/* snapshot shows error */) {
  browser_fill_form({
    fields: [{ /* corrected field */ }]
  });
}
```

### Page Load Timeout

**Problem:** Navigation takes too long.

**Solution:**
```javascript
// Use wait_for with time instead of relying on implicit wait
browser_navigate({ url: "..." });
browser_wait_for({ time: 5 }); // Give page time to load

// Or wait for specific content
browser_wait_for({ text: "Page loaded indicator" });
```

### Session Expired During Workflow

**Problem:** Authentication expires mid-workflow.

**Solution:**
```javascript
function ensureAuthenticated() {
  browser_snapshot();

  // Check if redirected to login
  if (/* snapshot shows login page */) {
    performLogin();
    // Return to intended page
    browser_navigate({ url: targetUrl });
  }
}

// Call before critical operations
ensureAuthenticated();
browser_click({ element: "Submit", ref: "..." });
```

---

## Performance Optimization

### Reduce Snapshot Calls

**Bad:**
```javascript
browser_snapshot();
browser_click({ element: "Button 1", ref: "ref-1" });
browser_snapshot();
browser_click({ element: "Button 2", ref: "ref-2" });
browser_snapshot();
browser_click({ element: "Button 3", ref: "ref-3" });
```

**Good:**
```javascript
// Single snapshot for all refs on same page
browser_snapshot();
browser_click({ element: "Button 1", ref: "ref-1" });
browser_click({ element: "Button 2", ref: "ref-2" });
browser_click({ element: "Button 3", ref: "ref-3" });
```

### Batch Data Extraction

**Bad:**
```javascript
const title = browser_evaluate({ function: `() => document.querySelector('.title').innerText` });
const author = browser_evaluate({ function: `() => document.querySelector('.author').innerText` });
const date = browser_evaluate({ function: `() => document.querySelector('.date').innerText` });
```

**Good:**
```javascript
const data = browser_evaluate({
  element: "article",
  function: `() => ({
    title: document.querySelector('.title').innerText,
    author: document.querySelector('.author').innerText,
    date: document.querySelector('.date').innerText
  })`
});
```

### Smart Waiting

**Bad:**
```javascript
browser_click({ element: "Submit", ref: "..." });
browser_wait_for({ time: 5 }); // Always wait 5 seconds
```

**Good:**
```javascript
browser_click({ element: "Submit", ref: "..." });
browser_wait_for({ text: "Success message" }); // Wait only as long as needed
```

---

## Conclusion

These workflows cover common automation patterns. Key principles:

1. **Always snapshot before interacting** - Get fresh refs
2. **Wait for state changes** - Use text-based waits when possible
3. **Extract data efficiently** - Batch operations in evaluate calls
4. **Handle errors gracefully** - Check for validation, session expiry
5. **Be respectful** - Add delays for scraping, don't overwhelm servers

For more details, see:
- `commands-reference.md` - Complete command documentation
- `best-practices.md` - Detailed guidelines and patterns
