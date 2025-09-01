#!/usr/bin/env python3
"""
Authentication decorator checker for Claude Code.
Ensures API endpoints have proper authentication decorators.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional


class AuthChecker:
    """Checks API endpoints for proper authentication decorators."""
    
    # Patterns that identify API endpoints
    ENDPOINT_PATTERNS = [
        r'@router\.(get|post|put|patch|delete|head|options|trace)\(',
        r'@app\.(get|post|put|patch|delete|head|options|trace)\(',
    ]
    
    # Required authentication patterns
    AUTH_PATTERNS = [
        r'@requires\(',           # Starlette requires decorator
        r'@Depends\([^)]*auth',   # FastAPI Depends with auth
        r'@Security\(',           # FastAPI Security
    ]
    
    # Public endpoints that don't need auth (by path patterns)
    PUBLIC_ENDPOINT_PATTERNS = [
        r'/health',
        r'/docs',
        r'/openapi',
        r'/redoc',
        r'/favicon',
        r'/static/',
        r'/metrics',
        r'/_internal/',
        r'/ping',
        r'/status',
    ]
    
    # Medical data patterns that definitely need auth
    SENSITIVE_PATHS = [
        r'/report',
        r'/finding',
        r'/patient',
        r'/study',
        r'/medical',
        r'/quality',
        r'/pdf',
        r'/organ',
        r'/condition',
        r'/activity',
    ]
    
    def __init__(self):
        self.violations = []
        
    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a Python file for authentication violations."""
        if not file_path.exists() or not file_path.name.endswith('.py'):
            return []
            
        # Only check API files
        if not self.is_api_file(file_path):
            return []
            
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            self.analyze_file_content(file_path, content, lines)
            
        except Exception as e:
            self.violations.append({
                'type': 'error',
                'file': str(file_path),
                'message': f'Error reading file: {str(e)}',
                'line': 0
            })
            
        return self.violations
    
    def is_api_file(self, file_path: Path) -> bool:
        """Check if file is an API file."""
        # Check filename patterns
        if file_path.name in ['api.py', 'endpoints.py', 'routes.py']:
            return True
            
        # Check if file contains router/app definitions
        try:
            content = file_path.read_text(encoding='utf-8')
            router_patterns = [
                r'router\s*=\s*APIRouter',
                r'app\s*=\s*FastAPI',
                r'from fastapi import.*APIRouter',
                r'@router\.',
                r'@app\.',
            ]
            
            return any(re.search(pattern, content) for pattern in router_patterns)
        except Exception:
            return False
    
    def analyze_file_content(self, file_path: Path, content: str, lines: List[str]):
        """Analyze file content for authentication issues."""
        in_function = False
        current_function = None
        function_start_line = 0
        auth_found = False
        endpoint_decorators = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for endpoint decorators
            endpoint_match = self.find_endpoint_decorator(stripped)
            if endpoint_match:
                endpoint_decorators.append({
                    'line': line_num,
                    'method': endpoint_match['method'],
                    'path': endpoint_match['path'],
                    'decorator': stripped
                })
                continue
                
            # Check for auth decorators
            if self.has_auth_decorator(stripped):
                auth_found = True
                continue
                
            # Check for function definitions
            func_match = re.match(r'async def\s+(\w+)|def\s+(\w+)', stripped)
            if func_match:
                # Process previous function if any
                if in_function and endpoint_decorators:
                    self.check_function_auth(
                        file_path, current_function, function_start_line,
                        endpoint_decorators, auth_found
                    )
                
                # Start new function
                current_function = func_match.group(1) or func_match.group(2)
                function_start_line = line_num
                in_function = True
                auth_found = False
                endpoint_decorators = []
                
        # Process last function
        if in_function and endpoint_decorators:
            self.check_function_auth(
                file_path, current_function, function_start_line,
                endpoint_decorators, auth_found
            )
    
    def find_endpoint_decorator(self, line: str) -> Optional[Dict]:
        """Find endpoint decorator in line."""
        for pattern in self.ENDPOINT_PATTERNS:
            match = re.search(pattern, line)
            if match:
                method = match.group(1)
                
                # Extract path from decorator
                path_match = re.search(r'[\'"]([^\'\"]+)[\'"]', line)
                path = path_match.group(1) if path_match else 'unknown'
                
                return {
                    'method': method,
                    'path': path
                }
        return None
    
    def has_auth_decorator(self, line: str) -> bool:
        """Check if line contains authentication decorator."""
        return any(re.search(pattern, line) for pattern in self.AUTH_PATTERNS)
    
    def check_function_auth(self, file_path: Path, function_name: str, 
                          line_num: int, endpoint_decorators: List[Dict], 
                          has_auth: bool):
        """Check if function has proper authentication."""
        for endpoint in endpoint_decorators:
            path = endpoint['path']
            method = endpoint['method'].upper()
            
            # Check if endpoint is public
            if self.is_public_endpoint(path):
                continue
                
            # Check if endpoint handles sensitive data
            is_sensitive = self.is_sensitive_endpoint(path)
            
            if not has_auth:
                severity = 'critical' if is_sensitive else 'warning'
                self.violations.append({
                    'type': 'missing_auth',
                    'severity': severity,
                    'file': str(file_path),
                    'function': function_name,
                    'line': line_num,
                    'endpoint': f"{method} {path}",
                    'message': f'Endpoint {method} {path} lacks authentication decorator',
                    'suggestion': self.get_auth_suggestion(path, method)
                })
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint should be public."""
        return any(re.search(pattern, path) for pattern in self.PUBLIC_ENDPOINT_PATTERNS)
    
    def is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint handles sensitive medical data."""
        return any(pattern in path.lower() for pattern in self.SENSITIVE_PATHS)
    
    def get_auth_suggestion(self, path: str, method: str) -> str:
        """Get authentication suggestion for endpoint."""
        if self.is_sensitive_endpoint(path):
            if 'report' in path.lower():
                if method in ['GET']:
                    return "Add @requires(report_read_permissions)"
                else:
                    return "Add @requires(report_write_permissions)"
            elif 'finding' in path.lower():
                return "Add @requires(finding_permissions)"
            elif 'quality' in path.lower():
                return "Add @requires(quality_control_permissions)"
            else:
                return "Add @requires([Roles.ADMIN, Roles.RADIOLOGIST, Roles.STAFF])"
        else:
            return "Add @requires([Roles.ADMIN]) or appropriate permissions"


def main():
    """Main hook entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get tool information
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only run on Python file modifications
    if tool_name not in ["Edit", "MultiEdit", "Write"]:
        sys.exit(0)
    
    # Get file path
    file_path_str = tool_input.get("file_path", "")
    if not file_path_str or not file_path_str.endswith('.py'):
        sys.exit(0)
        
    file_path = Path(file_path_str)
    
    # Initialize checker
    checker = AuthChecker()
    violations = checker.check_file(file_path)
    
    # Log results
    log_file = Path.home() / ".claude/logs/auth_checker.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'file': file_path_str,
        'tool': tool_name,
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
    
    if not violations:
        sys.exit(0)
    
    # Separate critical and warning violations
    critical_violations = [v for v in violations if v.get('severity') == 'critical']
    warning_violations = [v for v in violations if v.get('severity') != 'critical']
    
    # Show warnings (non-blocking)
    if warning_violations:
        print("⚠️  AUTHENTICATION WARNINGS:", file=sys.stderr)
        for violation in warning_violations:
            print(f"   {violation.get('message', 'Unknown issue')}", file=sys.stderr)
            if 'suggestion' in violation:
                print(f"   💡 {violation['suggestion']}", file=sys.stderr)
        print("", file=sys.stderr)
    
    # Block on critical violations  
    if critical_violations:
        print("🚫 CRITICAL AUTHENTICATION VIOLATIONS", file=sys.stderr)
        print("", file=sys.stderr)
        
        for violation in critical_violations:
            print(f"❌ {violation.get('message', 'Unknown critical issue')}", file=sys.stderr)
            print(f"   File: {violation.get('file')}:{violation.get('line', 0)}", file=sys.stderr)
            print(f"   Function: {violation.get('function', 'unknown')}", file=sys.stderr)
            if 'suggestion' in violation:
                print(f"   💡 Fix: {violation['suggestion']}", file=sys.stderr)
            print("", file=sys.stderr)
        
        print("🔒 Medical endpoints require authentication for HIPAA compliance!", file=sys.stderr)
        print(f"📋 Details logged to: {log_file}", file=sys.stderr)
        
        sys.exit(2)  # Block the operation
    
    # Success with warnings
    if warning_violations:
        print(f"✅ Authentication check completed with warnings (logged to {log_file})")
    
    sys.exit(0)


if __name__ == "__main__":
    main()