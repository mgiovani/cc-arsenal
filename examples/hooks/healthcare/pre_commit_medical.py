#!/usr/bin/env python3
"""
Pre-commit medical data validator for Claude Code hooks.
Scans for PII/PHI patterns, credentials, and sensitive data before commits.
"""

import json
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict


class MedicalDataValidator:
    """Validates code changes for medical compliance and data protection."""
    
    # PII/PHI patterns to detect
    SENSITIVE_PATTERNS = [
        # Social Security Numbers
        (r'\b\d{3}-\d{2}-\d{4}\b', 'Social Security Number detected'),
        (r'\b\d{9}\b', 'Potential SSN (9 digits) detected'),
        
        # Medical Record Numbers
        (r'\bMRN\s*[:=]\s*[A-Z0-9]+\b', 'Medical Record Number detected'),
        (r'\bpatient_id\s*[:=]\s*["\'][^"\']+["\']', 'Patient ID in code detected'),
        
        # Date of Birth patterns
        (r'\bdob\s*[:=]\s*["\']?\d{1,2}[/-]\d{1,2}[/-]\d{2,4}["\']?', 'Date of Birth detected'),
        (r'\bdate_of_birth\s*[:=]', 'Date of Birth field detected'),
        
        # Names (common patterns)
        (r'\bpatient_name\s*[:=]\s*["\'][A-Za-z\s]+["\']', 'Patient name detected'),
        (r'\bfirst_name\s*[:=]\s*["\'][A-Za-z]+["\']', 'First name detected'),
        (r'\blast_name\s*[:=]\s*["\'][A-Za-z]+["\']', 'Last name detected'),
        
        # Phone numbers
        (r'\b\d{3}-\d{3}-\d{4}\b', 'Phone number detected'),
        (r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', 'Phone number detected'),
        
        # Email addresses (if not clearly test/dev)
        (r'\b[A-Za-z0-9._%+-]+@(?!(?:test|dev|example|localhost|127\.0\.0\.1))[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
         'Real email address detected (use test/dev emails instead)'),
         
        # Credentials and API keys
        (r'(?:password|pwd|secret|key|token)\s*[:=]\s*["\'][^"\']{8,}["\']', 
         'Potential credential detected'),
        (r'(?:AKIA|ASIA)[0-9A-Z]{16}', 'AWS Access Key detected'),
        (r'[A-Za-z0-9/+=]{40}', 'Potential AWS Secret Key detected'),
        
        # Database connection strings with real data
        (r'postgresql://(?!test|dev)[^@]+@[^/]+/(?!test)[^?]+', 
         'Production database connection string detected'),
         
        # Real-looking addresses
        (r'\b\d+\s+[A-Za-z\s]+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd|boulevard)\b', 
         'Street address detected'),
    ]
    
    # File extensions to scan
    SCANNABLE_EXTENSIONS = {'.py', '.sql', '.json', '.yaml', '.yml', '.md', '.txt', '.env'}
    
    # Files that should never contain sensitive data
    PROTECTED_FILES = {'.env', '.env.local', '.env.production', 'secrets.yaml', 'config.prod.yaml'}
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []
        
    def scan_staged_files(self) -> List[Dict]:
        """Scan all staged files for violations."""
        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode != 0:
                return []
                
            staged_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            for file_path in staged_files:
                full_path = self.project_root / file_path
                if self.should_scan_file(full_path):
                    self.scan_file(full_path, file_path)
                    
        except Exception as e:
            self.violations.append({
                'type': 'error',
                'message': f'Error scanning staged files: {str(e)}',
                'file': 'git',
                'line': 0
            })
            
        return self.violations
    
    def should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned."""
        if not file_path.exists() or not file_path.is_file():
            return False
            
        # Check extension
        if file_path.suffix.lower() not in self.SCANNABLE_EXTENSIONS:
            return False
            
        # Skip binary files, logs, etc.
        skip_patterns = [
            '__pycache__', '.git/', '.venv/', 'node_modules/',
            '.pytest_cache/', 'logs/', '.log'
        ]
        
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in skip_patterns)
    
    def scan_file(self, file_path: Path, relative_path: str):
        """Scan a single file for violations."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                self.scan_line(line, relative_path, line_num)
                
        except Exception as e:
            self.violations.append({
                'type': 'error',
                'message': f'Error reading file: {str(e)}',
                'file': relative_path,
                'line': 0
            })
    
    def scan_line(self, line: str, file_path: str, line_num: int):
        """Scan a single line for violations."""
        # Skip comments and docstrings (basic detection)
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            return
            
        for pattern, message in self.SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Additional context checks
                if self.is_likely_test_data(line, match.group()):
                    continue
                    
                self.violations.append({
                    'type': 'privacy',
                    'message': message,
                    'file': file_path,
                    'line': line_num,
                    'match': match.group(),
                    'context': line.strip()
                })
    
    def is_likely_test_data(self, line: str, match: str) -> bool:
        """Check if the match is likely test data."""
        test_indicators = [
            'test', 'mock', 'fake', 'example', 'sample', 'dummy',
            '123-45-6789',  # Common test SSN
            'john.doe', 'jane.doe', 'test@'
        ]
        
        line_lower = line.lower()
        return any(indicator in line_lower for indicator in test_indicators)


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
    
    if not ("git commit" in command or "git add" in command):
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
    
    # Run validation
    validator = MedicalDataValidator(project_root)
    violations = validator.scan_staged_files()
    
    # Log results
    log_file = Path.home() / ".claude/logs/medical_validation.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'command': command,
        'violations': len(violations),
        'details': violations
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
    
    # Block if violations found
    if violations:
        print("🚨 MEDICAL DATA VIOLATION DETECTED 🚨", file=sys.stderr)
        print("", file=sys.stderr)
        
        for violation in violations:
            if violation['type'] == 'privacy':
                print(f"❌ {violation['message']}", file=sys.stderr)
                print(f"   File: {violation['file']}:{violation['line']}", file=sys.stderr)
                print(f"   Found: {violation.get('match', 'N/A')}", file=sys.stderr)
                print(f"   Context: {violation.get('context', 'N/A')[:100]}...", file=sys.stderr)
                print("", file=sys.stderr)
        
        print("🔒 COMMIT BLOCKED for medical compliance.", file=sys.stderr)
        print("Please remove sensitive data and use test/mock data instead.", file=sys.stderr)
        print(f"📋 Full details logged to: {log_file}", file=sys.stderr)
        
        sys.exit(2)  # Block the commit
    
    # Success
    if violations == []:  # Explicitly check if scan ran
        print("✅ Medical data validation passed")
    
    sys.exit(0)


if __name__ == "__main__":
    main()