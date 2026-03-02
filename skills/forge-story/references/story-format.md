# Story Format Guide

Detailed guide with examples for writing well-structured user stories.

## Story File Naming

Story files live at: `docs/stories/<epic-id>/<story-id>.md`

**Convention:**
- Epic IDs: `epic-1`, `epic-2`, etc.
- Story IDs: `story-1.1`, `story-1.2`, `story-2.1`, etc.
- Files: `docs/stories/epic-1/story-1.1.md`

## Complete Story Example — Small Story (S)

```markdown
# Story 1.1: User Registration with Email

**Status**: ready
**Epic**: Authentication & User Management
**Priority**: High
**Size**: S
**Depends on**: none

## User Story

As a new visitor, I want to create an account with my email and password so that I can access the application's features.

## Acceptance Criteria

- [ ] Given I am on the registration page, when I submit a valid email and password (min 8 chars), then my account is created and I am redirected to the dashboard
- [ ] Given I submit an already-registered email, when the form is submitted, then I see the error "An account with this email already exists"
- [ ] Given I submit a password shorter than 8 characters, when the form is submitted, then I see the error "Password must be at least 8 characters"
- [ ] Given I submit an invalid email format, when the form is submitted, then I see the error "Please enter a valid email address"
- [ ] Given registration succeeds, then I receive a welcome email at the registered address

## Technical Tasks

- [ ] Task 1: Create registration API endpoint (AC: 1, 2, 3, 4)
  - [ ] POST /api/auth/register accepting {email, password}
  - [ ] Validate email format and uniqueness
  - [ ] Validate password length >= 8
  - [ ] Hash password with bcrypt before storage
  - [ ] Return {userId, email, token} on success
- [ ] Task 2: Create user record in database (AC: 1)
  - [ ] Insert into users table with {email, passwordHash, createdAt}
  - [ ] Generate unique userId
- [ ] Task 3: Send welcome email (AC: 5)
  - [ ] Trigger email service with user email and template "welcome"
- [ ] Task 4: Create registration form UI (AC: 1, 2, 3, 4)
  - [ ] Form with email + password fields
  - [ ] Client-side validation before submit
  - [ ] Display server error messages inline
  - [ ] Redirect to /dashboard on success
- [ ] Task 5: Write tests
  - [ ] Unit test: password hashing
  - [ ] Unit test: email validation
  - [ ] Integration test: POST /api/auth/register (success case)
  - [ ] Integration test: duplicate email rejection
  - [ ] Integration test: invalid password rejection

## Dev Notes

### Relevant Files
- Create: `src/api/auth/register.ts` — registration endpoint handler
- Create: `src/components/auth/RegisterForm.tsx` — registration UI component
- Modify: `src/db/schema.ts` — add users table if not exists
- [Source: docs/architecture/project-structure.md#api-routes]

### Data Models
Users table:
```sql
users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
)
```
[Source: docs/architecture/data-models.md#users]

### API Endpoints
POST /api/auth/register
- Request: { email: string, password: string }
- Success (201): { userId: string, email: string, token: string }
- Error (400): { error: string }
- Error (409): { error: "An account with this email already exists" }
[Source: docs/architecture/api-spec.md#auth]

### Technical Constraints
- Use bcrypt with cost factor 12 for password hashing
- JWT tokens expire after 7 days
- [Source: docs/architecture/security.md#passwords]

### Testing Requirements
- Unit tests: Jest/Vitest
- Integration tests: Supertest against test database
- Coverage requirement: 90% for auth module
- [Source: docs/architecture/testing-strategy.md]

## Notes

Email sending is handled by the existing EmailService class. Do not implement a new email provider.
```

## Complete Story Example — Medium Story (M)

```markdown
# Story 2.3: Project Dashboard with Recent Activity

**Status**: ready
**Epic**: Project Management
**Priority**: High
**Size**: M
**Depends on**: story-2.1 (project creation), story-1.2 (authentication)

## User Story

As an authenticated project member, I want to see a dashboard with my recent projects and their activity so that I can quickly resume work on what matters most.

## Acceptance Criteria

- [ ] Given I am logged in, when I visit /dashboard, then I see my 5 most recently active projects
- [ ] Given I have no projects, when I visit /dashboard, then I see an empty state with a "Create your first project" call-to-action
- [ ] Given a project has recent activity, when I view the dashboard, then I see the last activity timestamp and actor for each project
- [ ] Given I click a project card, when redirected, then I land on that project's main view
- [ ] Given I have more than 5 projects, when I scroll to the bottom, then I can load more projects (pagination)

## Technical Tasks

- [ ] Task 1: Create dashboard API endpoint (AC: 1, 2, 3, 5)
  - [ ] GET /api/dashboard/projects?limit=5&cursor=[id]
  - [ ] Join projects with latest activity record
  - [ ] Return cursor-based pagination metadata
- [ ] Task 2: Create DashboardPage component (AC: 1, 2, 4, 5)
  - [ ] Fetch projects on mount
  - [ ] Render ProjectCard for each project
  - [ ] Render EmptyState when no projects
  - [ ] Implement "Load more" with cursor pagination
- [ ] Task 3: Create ProjectCard component (AC: 1, 3, 4)
  - [ ] Display project name, description, last activity
  - [ ] Relative timestamp ("2 hours ago")
  - [ ] Link to project view
- [ ] Task 4: Write tests
  - [ ] Unit test: ProjectCard renders with activity
  - [ ] Unit test: EmptyState renders when no projects
  - [ ] Integration test: GET /api/dashboard/projects pagination
  - [ ] Integration test: GET /api/dashboard/projects empty result

## Dev Notes

### Relevant Files
- Create: `src/app/dashboard/page.tsx`
- Create: `src/components/dashboard/ProjectCard.tsx`
- Create: `src/components/dashboard/EmptyState.tsx`
- Create: `src/api/dashboard/projects.ts`
- [Source: docs/architecture/project-structure.md#pages]

### Data Models
[Include relevant schema excerpts with source citation]

### API Endpoints
[Include endpoint spec with source citation]

### Technical Constraints
[Include relevant constraints with source citation]

### Testing Requirements
[Include testing requirements with source citation]
```

## Story Sizing Examples

### S (Small, 1–3 hours)
- Add a single form field with validation
- Create a simple read-only API endpoint
- Add a static page with content
- Implement a password change form (with existing auth)

### M (Medium, 4–8 hours)
- Build a complete CRUD feature (list + create + edit + delete)
- Implement email notification for an existing event
- Add search/filter to an existing list view
- Create a dashboard with data from 1–2 sources

### L (Large, 1–2 days)
- Implement OAuth login (alongside existing email auth)
- Build a multi-step form with validation and persistence
- Create a real-time feature using WebSockets
- Implement file upload with processing pipeline

### XL (Too large — must split)
- "Implement the billing system" → Split into: plan selection UI, Stripe integration, invoice generation, subscription management
- "Build user profiles" → Split into: profile view page, edit profile form, avatar upload, public vs private settings

## Status Transitions

```
draft → ready → in-progress → done
         ↑
    (DoR checklist must pass)
```

- **draft**: Story written but not yet reviewed
- **ready**: DoR checklist passed, ready for a developer to pick up
- **in-progress**: Developer has started implementation
- **done**: All tasks complete, tests passing, DoD checklist passed

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| "As a user, I want to manage settings" | Too vague, not implementable | Split into specific settings features |
| AC: "The UI looks good" | Not testable | AC: "The button is disabled until all required fields are filled" |
| No Dev Notes | Developer must read all architecture docs | Extract relevant details into Dev Notes |
| XL story not split | Too risky, hard to review | Split at natural boundaries |
| Missing dependency | Developer blocked mid-implementation | Map all story dependencies upfront |
| Invented file paths | Developer confused, creates wrong structure | Only cite paths from architecture docs |
