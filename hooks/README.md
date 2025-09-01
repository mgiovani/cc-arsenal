# Hooks

Security, quality, and compliance automation hooks for Claude Code.

## Structure

```
hooks/
├── security/      # Authentication and data protection
│   ├── auth_checker.py      # Authentication validation
│   └── file_protection.py   # Sensitive file protection
├── quality/       # Code standards and validation
│   └── pre_commit_validate.py  # Pre-commit quality checks
└── compliance/    # Regulatory and audit requirements
    ├── audit_enforcer.py    # Audit trail generation
    └── migration_safety.py  # Safe database migrations
```

## Available Hooks

### Security Hooks
- **auth_checker**: Validates authentication for sensitive operations
- **file_protection**: Prevents modification of sensitive files

### Quality Hooks
- **pre_commit_validate**: Enforces code quality before commits

### Compliance Hooks
- **audit_enforcer**: Maintains audit trails for compliance
- **migration_safety**: Ensures safe database migrations

## Installation

Hooks are automatically symlinked to `~/.claude/hooks/` when running:
```bash
uv run scripts/setup/install.py
```

## Configuration

Hooks can be configured via `~/.claude/hook-config.yaml`:
```yaml
file_protection:
  enabled: true
  protected_patterns:
    - "*.env*"
    - "secrets.*"

audit_enforcer:
  enabled: true
  compliance_standards:
    - "GDPR"
    - "SOX"
```

## Development

Hooks are Python scripts that receive JSON input via stdin and return JSON responses:

```python
#!/usr/bin/env python3
import sys
import json

def main():
    event_data = json.loads(sys.stdin.read())
    # Hook logic here
    result = {"allowed": True, "message": "OK"}
    print(json.dumps(result))
    sys.exit(0 if result["allowed"] else 1)

if __name__ == "__main__":
    main()
```
