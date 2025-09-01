#!/usr/bin/env python3
"""
File protection hook for Claude Code.
Blocks modifications to sensitive files like .env, production configs, etc.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import ClassVar


class FileProtector:
    """Protects sensitive files from accidental modification."""

    # Files that should never be modified
    PROTECTED_FILES: ClassVar[set[str]] = {
        '.env',
        '.env.production',
        '.env.prod',
        '.env.staging',
        '.env.stg',
        'secrets.yaml',
        'secrets.yml',
        'config.prod.yaml',
        'config.production.yaml',
        'docker-compose.prod.yml',
        'docker-compose.production.yml',
        'Dockerfile.prod',
        'Dockerfile.production',
        'package-lock.json',  # Should use package manager
        'poetry.lock',  # Should use poetry commands
        'yarn.lock',  # Should use yarn commands
        'pnpm-lock.yaml',  # Should use pnpm commands
    }

    # Directories that should be protected
    PROTECTED_DIRS: ClassVar[set[str]] = {
        '.git/',
        '.aws/',
        'node_modules/',
        '__pycache__/',
        '.pytest_cache/',
        'htmlcov/',
        'coverage/',
        '.coverage/',
        'dist/',
        'build/',
        'egg-info/',
        '.tox/',
        '.venv/',
        'venv/',
        '.env/',
        'logs/',
    }

    # Patterns for sensitive files
    SENSITIVE_PATTERNS: ClassVar[list[str]] = [
        r'.*\.key$',  # Private keys
        r'.*\.pem$',  # Certificates
        r'.*\.p12$',  # Certificate bundles
        r'.*\.pfx$',  # Certificate bundles
        r'.*\.crt$',  # Certificates
        r'.*\.cert$',  # Certificates
        r'.*\.keystore$',  # Java keystores
        r'.*\.jks$',  # Java keystores
        r'.*\.backup$',  # Backup files
        r'.*\.bak$',  # Backup files
        r'.*\.log$',  # Log files
        r'.*\.pid$',  # Process ID files
        r'.*\.lock$',  # Lock files (except package managers)
        r'.*\.tmp$',  # Temporary files
        r'.*\.cache$',  # Cache files
        r'secrets.*\.ya?ml$',  # Secret configuration files
        r'config.*prod.*\.ya?ml$',  # Production configs
        r'.*credentials.*\.json$',  # Credential files
        r'.*service-account.*\.json$',  # Service account keys
    ]

    # Files that are OK to modify but need special attention
    WARNING_FILES: ClassVar[set[str]] = {
        'requirements.txt',
        'pyproject.toml',
        'setup.py',
        'setup.cfg',
        'Dockerfile',
        'docker-compose.yml',
        'docker-compose.yaml',
        'alembic.ini',
        'pytest.ini',
        'tox.ini',
        '.pre-commit-config.yaml',
        '.github/workflows/',
        '.gitignore',
        'MANIFEST.in',
    }

    def __init__(self) -> None:
        self.violations = []

    def check_file_protection(self, file_path: str, operation: str) -> bool:
        """Check if file should be protected."""
        file_path = file_path.strip()

        # Convert to Path for easier handling
        path = Path(file_path)
        filename = path.name

        # Check exact filename matches
        if filename in self.PROTECTED_FILES:
            self.violations.append(
                {
                    'type': 'protected_file',
                    'file': file_path,
                    'operation': operation,
                    'reason': f'File "{filename}" is protected from direct modification',
                }
            )
            return False

        # Check directory protection
        for protected_dir in self.PROTECTED_DIRS:
            if protected_dir in file_path or file_path.startswith(protected_dir):
                self.violations.append(
                    {
                        'type': 'protected_directory',
                        'file': file_path,
                        'operation': operation,
                        'reason': (
                            f'Directory "{protected_dir}" is protected from modification'
                        ),
                    }
                )
                return False

        # Check sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if re.match(pattern, filename, re.IGNORECASE):
                self.violations.append(
                    {
                        'type': 'sensitive_pattern',
                        'file': file_path,
                        'operation': operation,
                        'reason': f'File matches sensitive pattern: {pattern}',
                    }
                )
                return False

        # Check warning files (allow but warn)
        if filename in self.WARNING_FILES or any(
            warning in file_path for warning in self.WARNING_FILES
        ):
            self.violations.append(
                {
                    'type': 'warning',
                    'file': file_path,
                    'operation': operation,
                    'reason': f'File "{filename}" requires careful modification',
                }
            )

        return True

    def get_protection_suggestions(self, filename: str) -> str:
        """Get suggestions for protected files."""
        suggestions = {
            '.env': 'Use environment variables or update .env.sample instead',
            'package-lock.json': 'Use "npm install" or "npm update" instead',
            'poetry.lock': 'Use "poetry install" or "poetry update" instead',
            'yarn.lock': 'Use "yarn install" or "yarn add/remove" instead',
            'pnpm-lock.yaml': 'Use "pnpm install" or "pnpm add/remove" instead',
            '.git/': 'Use git commands instead of direct file modification',
            'node_modules/': 'Use package manager commands instead',
            '__pycache__/': 'Delete cache files or use "python -B" to ignore',
            '.pytest_cache/': 'Use "pytest --cache-clear" to clear cache',
        }

        for pattern, suggestion in suggestions.items():
            if pattern in filename:
                return suggestion

        return 'Review if this file should really be modified directly'


def main() -> None:
    """Main hook entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    # Get tool information
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Only run on file modification tools
    if tool_name not in ['Edit', 'MultiEdit', 'Write']:
        sys.exit(0)

    # Get file path
    file_path = tool_input.get('file_path', '')
    if not file_path:
        sys.exit(0)

    # Initialize protector
    protector = FileProtector()

    # Check file protection
    is_allowed = protector.check_file_protection(file_path, tool_name)

    # Log the check
    log_file = Path.home() / '.claude/logs/file_protection.json'
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'timestamp': datetime.now(datetime.UTC).isoformat(),
        'tool': tool_name,
        'file': file_path,
        'allowed': is_allowed,
        'violations': protector.violations,
    }

    # Append to log
    if log_file.exists():
        with log_file.open() as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with log_file.open('w') as f:
        json.dump(logs, f, indent=2)

    # Handle violations
    blocking_violations = [v for v in protector.violations if v['type'] != 'warning']
    warning_violations = [v for v in protector.violations if v['type'] == 'warning']

    # Show warnings first (non-blocking)
    if warning_violations:
        for violation in warning_violations:
            protector.get_protection_suggestions(violation['file'])

    # Block if there are blocking violations
    if blocking_violations:
        for violation in blocking_violations:
            protector.get_protection_suggestions(violation['file'])

        sys.exit(2)  # Block the operation

    # Success (warnings are allowed)
    if warning_violations:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
