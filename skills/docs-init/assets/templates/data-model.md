# {{PROJECT_NAME}} - Data Model

**Last Updated:** {{DATE}}

## Overview

{{OVERVIEW}}

**Database:** {{DATABASE_TYPE}} ({{DATABASE_VERSION}})

## Entity Relationship Diagram

```mermaid
erDiagram
{{ER_DIAGRAM_CONTENT}}
```

## Entity Definitions

<!-- One subsection per real table/model found in the codebase (models/, schema
     files, migrations). Duplicate this block per entity. -->

### {{ENTITY_NAME}}

{{ENTITY_DESCRIPTION}}

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| {{ATTR_NAME}} | {{ATTR_TYPE}} | {{ATTR_CONSTRAINTS}} | {{ATTR_DESC}} |

**Relationships:** {{ENTITY_RELATIONSHIPS}}

## Notes

{{NOTES}}

## Related Documentation

- [Architecture Overview](architecture.md)
- [Data Security](security.md)

---

*This document should be regenerated from the actual models when the schema changes.*
