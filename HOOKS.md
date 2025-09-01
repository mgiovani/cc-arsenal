# Claude Code Arsenal Hooks Reference

This document provides a comprehensive overview of all available Claude hooks in the Claude Code Arsenal. Hooks are Python scripts that execute automatically in response to Claude Code events, providing security, validation, and compliance automation capabilities.

## Quick Start

1. **Installation**: Run `uv run scripts/setup/install.py` to symlink hooks to your `~/.claude` directory
2. **Configuration**: Hooks are automatically enabled; customize via Claude Code settings
3. **Usage**: Hooks run automatically on specified events (tool calls, file operations, etc.)

## Hook Categories

### 🔒 Security Hooks
*Protect sensitive data and enforce security policies*

#### auth_checker.py
**Location**: `hooks/security/auth_checker.py`
**Trigger**: Before file operations and API calls
**Purpose**: Validates authentication and authorization for sensitive operations
**Features**:
- API key and token validation
- Permission-based access control
- Audit logging for security events
- Rate limiting and abuse prevention

**Configuration**:
```python
SECURITY_SETTINGS = {
    "require_auth": True,
    "log_security_events": True,
    "rate_limit_requests": 100,
    "blocked_patterns": ["api_key=", "password=", "secret="]
}
```

#### file_protection.py
**Location**: `hooks/security/file_protection.py`
**Trigger**: Before file write operations
**Purpose**: Prevents modification of sensitive files and directories
**Protected Files**:
- Environment files (`.env`, `.env.production`)
- Security configurations (`secrets.yaml`, `config.prod.yaml`)
- Lock files (`package-lock.json`, `poetry.lock`)
- System directories (`.git/`, `.aws/`, `node_modules/`)

**Features**:
- Configurable protection patterns
- Whitelist exceptions for authorized operations
- Backup creation before allowed modifications
- Detailed logging of protection events

### ✅ Quality Assurance Hooks
*Enforce code quality standards and best practices*

#### pre_commit_validate.py
**Location**: `hooks/quality/pre_commit_validate.py`
**Trigger**: Before git commit operations
**Purpose**: Validates code quality and enforces standards before commits
**Validations**:
- Code formatting (Black, Prettier, etc.)
- Linting (ESLint, Flake8, Ruff)
- Type checking (TypeScript, mypy)
- Test execution and coverage
- Documentation completeness

**Configuration**:
```python
QUALITY_CONFIG = {
    "min_test_coverage": 80,
    "require_type_hints": True,
    "enforce_docs": True,
    "allowed_todo_patterns": ["TODO:", "FIXME:", "XXX:"],
    "max_complexity": 10
}
```

**Features**:
- Language-specific validation rules
- Configurable quality thresholds
- Automatic fixing of common issues
- Detailed quality reports

### 📋 Compliance Hooks
*Ensure regulatory compliance and audit requirements*

#### audit_enforcer.py
**Location**: `hooks/compliance/audit_enforcer.py`
**Trigger**: On all significant operations
**Purpose**: Maintains comprehensive audit trails and enforces compliance policies
**Compliance Features**:
- GDPR data handling validation
- SOX compliance for financial data
- HIPAA compliance for healthcare data
- Custom compliance rule enforcement

**Audit Logging**:
```python
AUDIT_CONFIG = {
    "log_all_operations": True,
    "retention_period": "7_years",
    "encryption_required": True,
    "anonymize_pii": True,
    "compliance_standards": ["GDPR", "SOX", "HIPAA"]
}
```

#### migration_safety.py
**Location**: `hooks/compliance/migration_safety.py`
**Trigger**: Before database and infrastructure changes
**Purpose**: Ensures safe database migrations and infrastructure changes
**Safety Features**:
- Backup verification before migrations
- Rollback plan validation
- Production safety checks
- Change impact analysis

### 🏥 Project-Specific Hooks
*Domain-specific validation and compliance*

#### pre_commit_medical.py
**Location**: `hooks/project-specific/pre_commit_medical.py`
**Trigger**: Before commits in medical/healthcare projects
**Purpose**: Enforces healthcare-specific compliance and safety standards
**Medical Compliance**:
- HIPAA privacy validation
- FDA software validation requirements
- Clinical data integrity checks
- Medical device software standards

**Features**:
- PHI (Protected Health Information) detection
- Clinical workflow validation
- Regulatory documentation requirements
- Medical device classification compliance

## Hook Configuration

### Global Hook Settings
Configure hooks in your Claude Code settings:

```json
{
  "hooks": {
    "enabled": true,
    "security_level": "high",
    "audit_mode": true,
    "custom_config_path": "~/.claude/hook-config.yaml"
  }
}
```

### Hook-Specific Configuration
Each hook can be configured via YAML files:

```yaml
# ~/.claude/hook-config.yaml
file_protection:
  enabled: true
  strict_mode: true
  protected_patterns:
    - "*.env*"
    - "secrets.*"
    - "config.prod.*"
  exceptions:
    - "config.dev.yaml"
    - "test.env"

audit_enforcer:
  enabled: true
  compliance_standards:
    - "GDPR"
    - "SOX"
  log_level: "INFO"
  retention_days: 2555  # 7 years
```

## Hook Development Guidelines

### Hook File Structure
```python
#!/usr/bin/env python3
"""
Hook description and purpose.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

class HookName:
    """Hook implementation class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize hook with configuration."""
        self.config = config or self._load_default_config()
    
    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hook logic."""
        # Implementation here
        return {
            "allowed": True,
            "message": "Operation permitted",
            "metadata": {}
        }
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {}

def main() -> None:
    """Hook entry point."""
    try:
        event_data = json.loads(sys.stdin.read())
        hook = HookName()
        result = hook.execute(event_data)
        print(json.dumps(result))
        sys.exit(0 if result["allowed"] else 1)
    except Exception as e:
        error_result = {
            "allowed": False,
            "message": f"Hook error: {e}",
            "metadata": {"error": str(e)}
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Best Practices
- **Performance**: Keep hooks fast to avoid slowing down operations
- **Reliability**: Include robust error handling and fallback behavior
- **Security**: Validate all inputs and sanitize outputs
- **Logging**: Provide detailed logging for debugging and audit purposes
- **Configuration**: Make hooks configurable for different environments

## Hook Event Types

### File Operation Events
- `file_read_pre`: Before file read operations
- `file_write_pre`: Before file write operations
- `file_delete_pre`: Before file deletion
- `file_execute_pre`: Before file execution

### Git Operation Events
- `git_commit_pre`: Before git commit
- `git_push_pre`: Before git push
- `git_merge_pre`: Before git merge
- `git_checkout_pre`: Before branch checkout

### Tool Execution Events
- `tool_call_pre`: Before any tool execution
- `tool_call_post`: After tool execution
- `bash_command_pre`: Before bash command execution
- `api_call_pre`: Before external API calls

### Custom Events
- `project_deploy_pre`: Before deployment operations
- `database_migrate_pre`: Before database migrations
- `security_scan_post`: After security scans

## Advanced Hook Features

### Multi-Hook Chains
Hooks can be chained for complex workflows:
```python
HOOK_CHAINS = {
    "file_write_pre": [
        "file_protection.py",
        "security_scanner.py", 
        "compliance_validator.py"
    ]
}
```

### Conditional Hook Execution
Hooks can be executed conditionally:
```python
CONDITIONS = {
    "production_only": lambda ctx: ctx.get("environment") == "production",
    "sensitive_files": lambda ctx: any(pattern in ctx.get("file_path", "") 
                                    for pattern in [".env", "secret", "key"]),
}
```

### Hook Metadata and Context
Hooks receive rich context information:
```python
{
    "event_type": "file_write_pre",
    "file_path": "/path/to/file.py",
    "operation": "write",
    "content_preview": "first 100 chars...",
    "user_context": {"project": "my-app", "branch": "main"},
    "environment": "development",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Troubleshooting

### Hook Execution Failures
- Check Python environment and dependencies
- Verify hook file permissions (executable)
- Review hook configuration syntax
- Monitor Claude Code logs for detailed errors

### Performance Issues
- Profile hook execution time with timing logs
- Optimize file I/O operations in hooks
- Consider async execution for non-blocking hooks
- Cache frequently accessed data

### Configuration Problems
- Validate YAML/JSON configuration syntax
- Ensure configuration files are readable
- Check file paths and permissions
- Test configuration with hook validation tools

## Contributing New Hooks

1. **Identify Need**: Determine what safety/compliance gap the hook addresses
2. **Choose Category**: Select appropriate category (security/quality/compliance/project-specific)
3. **Implement Hook**: Follow the standard hook structure and patterns
4. **Add Configuration**: Create configurable options for different environments
5. **Test Thoroughly**: Validate with various scenarios and edge cases
6. **Document Usage**: Provide clear configuration and usage examples
7. **Submit PR**: Include hook in appropriate category directory

### Hook Categories Guidelines
- **security/**: Authentication, authorization, data protection, access control
- **quality/**: Code standards, testing, linting, documentation
- **compliance/**: Regulatory requirements, audit trails, data governance
- **project-specific/**: Domain-specific rules (healthcare, finance, etc.)

## Integration with Claude Code

Hooks integrate seamlessly with Claude Code through:
- **Event System**: Automatic triggering on specified events
- **Configuration**: Settings management through Claude Code preferences
- **Logging**: Integration with Claude Code logging infrastructure
- **Error Handling**: Graceful handling of hook failures

## Support

For issues, questions, or contributions:
- **Issues**: Open an issue on GitHub with hook-specific details
- **Discussions**: Use GitHub Discussions for hook development questions
- **Documentation**: Check the `docs/` directory for detailed hook guides

---

*This document is auto-generated from hook metadata. Last updated: $(date)*