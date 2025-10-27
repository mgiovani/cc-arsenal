#!/usr/bin/env python3
"""
Pre-commit validation workflow hook for Claude Code.
Runs validation checks before commits.

Exit codes:
- 0: Validation passed or hook skipped (not applicable)
- 2: Validation failed, blocks the commit (Claude sees stderr feedback)
- 1: Error in hook execution (non-blocking)
"""

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar


class PreCommitValidator:
    """Runs validation checks before commits."""

    # Maximum lines to show from stderr output
    MAX_STDERR_LINES: ClassVar[int] = 10

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.app_dir = project_root / 'app'
        self.issues = []
        self.success_count = 0

    def run_validation(self) -> bool:
        """Run all validation checks."""
        if not self.app_dir.exists():
            self.issues.append(
                {'check': 'setup', 'error': f'App directory not found: {self.app_dir}'}
            )
            return False

        checks = [
            ('lint', 'just lint'),
            ('unit-tests', 'just unit-test'),
            ('functional-tests', 'just functional-test'),
        ]

        all_passed = True

        for check_name, command in checks:
            try:
                result = subprocess.run(
                    command.split(),
                    check=False,
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    self.success_count += 1
                else:
                    all_passed = False
                    self.issues.append(
                        {
                            'check': check_name,
                            'command': command,
                            'exit_code': result.returncode,
                            'stdout': result.stdout.strip(),
                            'stderr': result.stderr.strip(),
                        }
                    )

            except subprocess.TimeoutExpired:
                all_passed = False
                self.issues.append(
                    {
                        'check': check_name,
                        'command': command,
                        'error': 'Command timed out after 5 minutes',
                    }
                )

            except (OSError, subprocess.SubprocessError) as e:
                all_passed = False
                self.issues.append(
                    {'check': check_name, 'command': command, 'error': str(e)}
                )

        return all_passed

    def get_staged_python_files(self) -> list[str]:
        """Get list of staged Python files."""
        try:
            result = subprocess.run(
                [
                    shutil.which('git'),
                    'diff',
                    '--cached',
                    '--name-only',
                    '--diff-filter=AM',
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                return []

            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return [f for f in files if f.endswith('.py')]

        except (OSError, subprocess.SubprocessError):
            return []

    def should_run_validation(self, staged_files: list[str]) -> bool:
        """Determine if validation should run based on staged files."""
        # Run validation if:
        # 1. Any Python files are being committed
        # 2. Any test files are being committed
        # 3. Any configuration files are being committed

        important_extensions = {'.py', '.yaml', '.yml', '.json', '.toml'}
        important_dirs = {'tests/', 'alembic/', 'migrations/'}

        for file_path in staged_files:
            # Check extensions
            if any(file_path.endswith(ext) for ext in important_extensions):
                return True

            # Check directories
            if any(dir_name in file_path for dir_name in important_dirs):
                return True

        return False


def _parse_input() -> tuple[str, str]:
    """Parse and validate input data."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')

    if not tool_name:
        print("Warning: No tool_name in hook input", file=sys.stderr)

    if tool_name == 'Bash' and not command:
        print("Warning: Bash tool call with no command", file=sys.stderr)

    return tool_name, command


def _should_run_for_command(tool_name: str, command: str) -> bool:
    """Determine if validation should run for given tool and command."""
    return tool_name == 'Bash' and 'git commit' in command


def _get_project_root() -> Path | None:
    """Get project root if we're in a git repository.

    Note: This hook is project-agnostic and works in any git repo.
    For project-specific validation, set the PROJECT_ROOT environment variable.
    """
    import os
    import subprocess

    # Check if PROJECT_ROOT env var is set for project-specific validation
    if project_root_env := os.getenv('PROJECT_ROOT'):
        return Path(project_root_env)

    # Otherwise, find git root of current directory
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def _get_staged_files(project_root: Path) -> list[str]:
    """Get list of staged files from git."""
    staged_files = []
    try:
        result = subprocess.run(
            [shutil.which('git'), 'diff', '--cached', '--name-only'],
            check=False,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if result.returncode == 0:
            staged_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return staged_files


def _log_results(
    validator: PreCommitValidator,
    staged_files: list[str],
    success: bool,
    start_time: datetime,
) -> None:
    """Log validation results to file."""
    log_file = Path.home() / '.claude/logs/pre_commit_validate.json'
    log_file.parent.mkdir(parents=True, exist_ok=True)

    duration = datetime.now(UTC) - start_time
    log_entry = {
        'timestamp': start_time.isoformat(),
        'duration_seconds': duration.total_seconds(),
        'staged_files': staged_files,
        'success': success,
        'successful_checks': validator.success_count,
        'issues': validator.issues,
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


def _handle_validation_failure(validator: PreCommitValidator) -> None:
    """Handle validation failure by processing and displaying issues."""
    print("\n❌ Pre-commit validation failed!\n", file=sys.stderr)

    for issue in validator.issues:
        check_name = issue.get('check', 'unknown')

        print(f"Failed check: {check_name}", file=sys.stderr)

        if 'error' in issue:
            print(f"  Error: {issue['error']}", file=sys.stderr)
        elif issue.get('stderr'):
            print("  Output:", file=sys.stderr)
            # Show first few lines of stderr
            stderr_lines = issue['stderr'].split('\n')[: validator.MAX_STDERR_LINES]
            for line in stderr_lines:
                if line.strip():
                    print(f"    {line}", file=sys.stderr)

            if len(issue['stderr'].split('\n')) > validator.MAX_STDERR_LINES:
                remaining = len(issue['stderr'].split('\n')) - validator.MAX_STDERR_LINES
                print(f"    ... ({remaining} more lines)", file=sys.stderr)

        print("", file=sys.stderr)  # Empty line between issues

    print(f"✓ Passed: {validator.success_count} checks", file=sys.stderr)
    print(f"✗ Failed: {len(validator.issues)} checks", file=sys.stderr)
    print("\nPlease fix the issues above before committing.", file=sys.stderr)


def main() -> None:
    """Main hook entry point."""
    # Parse input
    tool_name, command = _parse_input()

    # Check if we should run validation
    if not _should_run_for_command(tool_name, command):
        sys.exit(0)

    # Get project root
    project_root = _get_project_root()
    if project_root is None:
        sys.exit(0)

    # Initialize validator
    validator = PreCommitValidator(project_root)

    # Get staged files and check if validation should run
    staged_files = _get_staged_files(project_root)
    if not validator.should_run_validation(staged_files):
        sys.exit(0)

    # Run validation
    start_time = datetime.now(UTC)
    success = validator.run_validation()

    # Log results
    _log_results(validator, staged_files, success, start_time)

    # Handle success or failure
    if success:
        sys.exit(0)
    else:
        _handle_validation_failure(validator)
        sys.exit(2)  # Block the commit


if __name__ == '__main__':
    main()
