# Acceptance Criteria Guide

How to write testable, unambiguous Given/When/Then acceptance criteria.

## Why Given/When/Then

Given/When/Then (also called Gherkin-style) criteria are:
- **Testable**: Each criterion can be directly translated into a test case
- **Unambiguous**: Context, trigger, and expected outcome are explicit
- **Verifiable**: Pass/fail determination requires no judgment

A criterion that requires subjective judgment ("the page loads fast", "the UI looks clean") is not an acceptance criterion — it's a preference. Convert it into something measurable.

## Structure

```
Given [initial context or state]
When [user action or system event]
Then [expected observable outcome]
```

**Optional extensions:**
```
Given [context]
And [additional context]
When [action]
And [additional action]
Then [outcome]
And [additional outcome]
```

## The Three Parts

### Given — Context

Establishes the preconditions. Be specific about:
- User authentication state ("I am logged in as an admin")
- Data state ("I have 3 active projects")
- Page/location ("I am on the user settings page")
- System state ("the payment gateway is unavailable")

**Vague:** `Given I am using the app`
**Specific:** `Given I am logged in and have no projects in my account`

### When — Action or Event

The trigger that causes the system to respond. Be specific about:
- What the user does ("I click the Submit button", "I type 'abc' in the search field")
- What system event occurs ("the payment webhook is received", "the session expires")
- What API call is made ("I send POST /api/projects with {name: 'My Project'}")

**Vague:** `When something happens`
**Specific:** `When I click the "Delete Account" button and confirm in the confirmation dialog`

### Then — Outcome

The observable result. Be specific about:
- What the user sees ("I see the error message 'Email already registered'")
- What state changes ("the project no longer appears in my project list")
- What happens in the system ("a confirmation email is sent to my email address")
- What navigation occurs ("I am redirected to /dashboard")

**Vague:** `Then it works correctly`
**Specific:** `Then I see a success toast notification "Project created" and the new project appears at the top of my project list`

## 15 Criteria Examples by Category

### Form Validation

```
Given I am on the registration form
When I submit the form with the email field empty
Then I see the error "Email is required" below the email field
And the form is not submitted
```

```
Given I am on the registration form
When I enter "notanemail" in the email field and submit
Then I see the error "Please enter a valid email address"
```

```
Given I am on the password reset form
When I enter a password shorter than 8 characters
Then I see the error "Password must be at least 8 characters" before I submit
```

### Authentication & Authorization

```
Given I am not logged in
When I navigate to /dashboard
Then I am redirected to /login with a message "Please sign in to continue"
```

```
Given I am logged in as a regular user
When I navigate to /admin
Then I see a 403 error page "Access denied"
```

```
Given my session has expired
When I attempt to perform any action
Then I see a modal "Your session has expired. Please sign in again."
And clicking "Sign in" redirects me to /login
```

### Data Operations (CRUD)

```
Given I have an existing project named "Alpha"
When I click "Edit" and change the name to "Alpha v2" and save
Then the project list shows "Alpha v2" in place of "Alpha"
And a success notification "Project updated" appears
```

```
Given I have a project with 3 tasks
When I delete the project and confirm
Then the project no longer appears in my project list
And navigating to the deleted project's URL shows a 404 page
```

```
Given I have 25 projects
When I load the projects page
Then I see 20 projects
And a "Load more" button appears at the bottom
When I click "Load more"
Then 5 additional projects appear
And the "Load more" button disappears
```

### API Behavior

```
Given a valid API key in the Authorization header
When I send GET /api/projects
Then I receive a 200 response with a JSON array of projects
And each project has fields: id, name, createdAt, updatedAt
```

```
Given an invalid or missing API key
When I send GET /api/projects
Then I receive a 401 response with body {"error": "Unauthorized"}
```

### Error States & Edge Cases

```
Given the database is unavailable
When I attempt to load my project list
Then I see the error message "Service temporarily unavailable. Please try again."
And the page shows a "Retry" button
```

```
Given I am viewing a project shared with me
When the project owner deletes the project
Then on my next page load, I see "This project no longer exists"
```

### Emails & Notifications

```
Given I have just created an account
When registration completes successfully
Then I receive a welcome email within 60 seconds at my registered address
And the email subject is "Welcome to [App Name]"
```

### Real-time & Async

```
Given two users are viewing the same document
When User A edits a paragraph
Then User B sees the change within 2 seconds without refreshing
```

## Writing Criteria for Different Story Types

### Backend-only stories

Focus on API contract:
```
Given a POST /api/projects request with body {name: "Test", description: ""}
When the request is processed
Then the response is 201 with body {id: UUID, name: "Test", description: "", createdAt: ISO8601}
And the project is persisted in the database
```

### Frontend-only stories

Focus on user interaction and visual state:
```
Given the project list is loading
When data has not yet been received
Then I see a skeleton loading state (3 placeholder project cards)
```

### Database migration stories

Focus on data state:
```
Given existing users without a "role" column
When the migration runs
Then all existing users have role = "member"
And new users can be created with role = "admin" or "member"
```

## Common Mistakes and Fixes

| Mistake | Example | Fix |
|---|---|---|
| Vague outcome | "Then it works" | "Then I see a success message 'Saved'" |
| Missing context | "When I submit" | "Given I am on /settings, when I submit the form" |
| Multiple actions in When | "When I fill in the form, validate it, and submit" | Separate into multiple ACs or use "And" |
| Non-observable outcome | "Then the database is updated" | "Then the updated value appears on the page" |
| Subjective outcome | "Then the page looks professional" | Not an AC — remove or make measurable |
| Implementation detail in Then | "Then Postgres inserts a row" | "Then the user appears in the admin user list" |

## How Many Criteria Per Story

- **Minimum**: 2 criteria per story (happy path + most important error case)
- **Typical**: 3–6 criteria per story
- **Maximum**: 8–10 criteria (if more, consider splitting the story)

For each acceptance criterion, there should be at least one corresponding technical task and one test case.

## Mapping Criteria to Tasks and Tests

Every acceptance criterion should trace to:
1. **At least one task** in the Technical Tasks section (with `AC: N` reference)
2. **At least one test case** in the test suite

If an acceptance criterion has no corresponding task, it will not be implemented.
If an acceptance criterion has no corresponding test, it cannot be verified as done.
