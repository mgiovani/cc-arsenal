#!/usr/bin/env python3
"""
Pre-commit validation workflow hook for Claude Code.
Runs the same validation checks as the /validate command before commits.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class PreCommitValidator:
    """Runs validation checks before commits."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.issues = []
        self.success_count = 0
        
    def run_validation(self) -> bool:
        """Run all validation checks."""
        if not self.app_dir.exists():
            self.issues.append({
                'check': 'setup',
                'error': f'App directory not found: {self.app_dir}'
            })
            return False
            
        checks = [
            ('lint', 'just lint'),
            ('unit-tests', 'just unit-test'),
            ('functional-tests', 'just functional-test')
        ]
        
        all_passed = True
        
        for check_name, command in checks:
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    self.success_count += 1
                else:
                    all_passed = False
                    self.issues.append({
                        'check': check_name,
                        'command': command,
                        'exit_code': result.returncode,
                        'stdout': result.stdout.strip(),
                        'stderr': result.stderr.strip()
                    })
                    
            except subprocess.TimeoutExpired:
                all_passed = False
                self.issues.append({
                    'check': check_name,
                    'command': command,
                    'error': 'Command timed out after 5 minutes'
                })
                
            except Exception as e:
                all_passed = False
                self.issues.append({
                    'check': check_name,
                    'command': command,
                    'error': str(e)
                })
                
        return all_passed
    
    def get_staged_python_files(self) -> List[str]:
        """Get list of staged Python files."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=AM'],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode != 0:
                return []
                
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            python_files = [f for f in files if f.endswith('.py')]
            
            return python_files
            
        except Exception:
            return []
    
    def should_run_validation(self, staged_files: List[str]) -> bool:
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


def main():
    """Main hook entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get tool information
    tool_name = input_data.get("tool_name", "")
    
    # Only run on git commit operations
    if tool_name != "Bash":
        sys.exit(0)
        
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    
    if "git commit" not in command:
        sys.exit(0)
    
    # Determine project root - only run if we're in the target project
    target_project = Path("/Users/giovani.moutinho/prenuvo/platform-finding-capture-backend")
    current_dir = Path.cwd()
    
    # Check if current directory is within the target project
    try:
        current_dir.relative_to(target_project)
        project_root = target_project
    except ValueError:
        # Not in target project, skip validation
        sys.exit(0)
    
    # Initialize validator
    validator = PreCommitValidator(project_root)
    
    # Get staged files
    staged_files = []
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, cwd=project_root
        )
        if result.returncode == 0:
            staged_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except Exception:
        pass
    
    # Check if validation should run
    if not validator.should_run_validation(staged_files):
        print("ℹ️  Skipping validation - no critical files changed")
        sys.exit(0)
    
    print("🔍 Running pre-commit validation checks...")
    print(f"📁 Checking {len(staged_files)} staged files")
    
    # Run validation
    start_time = datetime.now()
    success = validator.run_validation()
    duration = datetime.now() - start_time
    
    # Log results
    log_file = Path.home() / ".claude/logs/pre_commit_validate.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': start_time.isoformat(),
        'duration_seconds': duration.total_seconds(),
        'staged_files': staged_files,
        'success': success,
        'successful_checks': validator.success_count,
        'issues': validator.issues
    }
    
    # Append to log
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
        
    logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    if success:
        print(f"✅ All validation checks passed! ({duration.total_seconds():.1f}s)")
        print(f"📋 Details logged to: {log_file}")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - COMMIT BLOCKED", file=sys.stderr)
        print("", file=sys.stderr)
        
        for issue in validator.issues:
            check_name = issue.get('check', 'unknown')
            print(f"🔴 Failed: {check_name}", file=sys.stderr)
            
            if 'error' in issue:
                print(f"   Error: {issue['error']}", file=sys.stderr)
            else:
                if issue.get('stderr'):
                    # Show first few lines of stderr
                    stderr_lines = issue['stderr'].split('\n')[:10]
                    for line in stderr_lines:
                        if line.strip():
                            print(f"   {line}", file=sys.stderr)
                    
                    if len(issue['stderr'].split('\n')) > 10:
                        print("   ... (truncated)", file=sys.stderr)
                        
            print("", file=sys.stderr)
        
        print("🔧 To fix these issues:", file=sys.stderr)
        print("   1. Run: cd app && /validate", file=sys.stderr)  
        print("   2. Fix all reported issues", file=sys.stderr)
        print("   3. Try committing again", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"📋 Full details logged to: {log_file}", file=sys.stderr)
        
        sys.exit(2)  # Block the commit


if __name__ == "__main__":
    main()