# Hooks

Security automation hooks for Claude Code.

## Structure

```
hooks/
└── security/      # Data protection
    └── file_protection.py   # Sensitive file protection
```

## Available Hooks

### Security Hooks
- **file_protection**: Prevents modification of sensitive files like .env, credentials, and other protected patterns

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
    - "credentials.*"
    - "*.key"
    - "*.pem"
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
