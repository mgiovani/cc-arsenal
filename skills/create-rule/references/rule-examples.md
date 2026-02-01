# Rule Examples

Concrete examples of well-structured memory rules for different use cases.

## Example 1: Simple Code Style Rule

**Command**: `/create-rule formatting "Use 2-space indentation and single quotes"`

Creates `.claude/rules/formatting.md`:

```markdown
# Code Formatting

Consistent formatting rules for the codebase.

## Guidelines

- Use 2-space indentation (no tabs)
- Use single quotes for strings (except when string contains single quote)
- Maximum line length: 100 characters
- Add trailing commas in multi-line arrays/objects

## Examples

### Good
```typescript
const config = {
  name: 'my-app',
  version: '1.0.0',
};
```

### Avoid
```typescript
const config = {
    name: "my-app",
    version: "1.0.0"
}
```
```

## Example 2: Path-Specific Rule

**Command**: `/create-rule api-errors "Standard error handling for API routes"`

Creates `.claude/rules/api-errors.md`:

```markdown
---
paths: src/api/**/*.ts, src/routes/**/*.ts
---

# API Error Handling

Standard error response format for all API endpoints.

## Guidelines

- Use the `ApiError` class for all error responses
- Include error code, message, and optional details
- Log errors with appropriate severity levels
- Never expose internal error details to clients

## Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
```

## Examples

### Good
```typescript
throw new ApiError('VALIDATION_ERROR', 'Invalid email format', { field: 'email' });
```

### Avoid
```typescript
throw new Error(err.stack); // Exposes internal details
```
```

## Example 3: User-Level Rule

**Command**: `/create-rule --user preferences "Personal coding preferences"`

Creates `~/.claude/rules/preferences.md`:

```markdown
# Personal Preferences

My personal coding preferences applied to all projects.

## Guidelines

- Prefer functional programming patterns over OOP
- Use descriptive variable names (no single letters except loop indices)
- Add TODO comments with my GitHub username: @myusername
- Prefer async/await over raw promises
```

## Writing Effective Rules Checklist

1. **BE SPECIFIC**: State exact expectations, not vague guidance
2. **USE IMPERATIVE LANGUAGE**: "Use X" not "You should use X"
3. **PROVIDE EXAMPLES**: Show code snippets of correct patterns
4. **KEEP RULES FOCUSED**: One file per topic
5. **USE PATH RESTRICTIONS SPARINGLY**: Only when rules truly apply to specific file types
6. **ORGANIZE WITH SUBDIRECTORIES**: `frontend/react.md`, `backend/api.md`
