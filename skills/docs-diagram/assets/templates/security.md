# {{PROJECT_NAME}} - Security Architecture

**Last Updated:** {{DATE}}

## Overview

{{OVERVIEW}}

[One paragraph: the trust boundaries, auth model, and data protection approach.]

## Security Data Flow

```mermaid
{{DIAGRAM_CONTENT}}
```

## Controls

- **Authentication** — {{AUTH_APPROACH}}
- **Authorization** — {{AUTHZ_APPROACH}}
- **Encryption in transit** — {{ENCRYPTION_TRANSIT}}
- **Encryption at rest** — {{ENCRYPTION_REST}}

## Trust Boundaries

- {{TRUST_BOUNDARY_1}}
- {{TRUST_BOUNDARY_2}}

## Related

- [Data Model](data-model.md) — entity relationships (generate with `docs-diagram er`)

---

*Generated from auth/middleware code. Regenerate with docs-diagram after security-relevant changes.*
