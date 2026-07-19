# {{PROJECT_NAME}} - Security

**Last Updated:** {{DATE}}

## Overview

This document outlines data security policies, access controls, and encryption
strategies for {{PROJECT_NAME}}, based on what the codebase actually implements.

## Data Classification

<!-- One row per data category the codebase evidences (user PII table, payment
     fields, internal logs, etc). Delete rows with no evidence. -->

| Category | Description | Access Control |
|----------|--------------|-----------------|
| {{DATA_CATEGORY}} | {{CATEGORY_DESCRIPTION}} | {{CATEGORY_ACCESS}} |

## Authentication and Authorization

{{AUTH_STRATEGY}}

[The real mechanism found in code: session cookies, JWT, OAuth provider, RBAC
middleware, etc.]

## Encryption

**Data at rest:** {{ENCRYPTION_AT_REST}}

**Data in transit:** {{ENCRYPTION_IN_TRANSIT}}

## Compliance

<!-- Only include a regulation if the codebase shows real evidence of it
     (GDPR consent flows, HIPAA PHI handling, a documented DPA, etc).
     Delete this entire section if no compliance work is evidenced. -->

{{COMPLIANCE_REQUIREMENTS}}

## Incident Response

{{INCIDENT_RESPONSE}}

[Link to a runbook if one exists; otherwise note that none exists yet.]

## Security Testing

{{SECURITY_TESTING}}

[Only what's evidenced: a dependabot/CI security scan step, a SAST tool config.
Omit speculative pentest schedules.]

## References

- [Data Model Documentation](data-model.md)
- [Architecture Overview](architecture.md)

---

*This document may contain sensitive security information. Restrict access appropriately.*
