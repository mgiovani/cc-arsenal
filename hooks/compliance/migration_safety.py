#!/usr/bin/env python3
"""
Migration safety checker for Claude Code.
Warns about destructive database operations and ensures proper environment.
"""

import json
import sys
import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set


class MigrationSafetyChecker:
    """Checks database migrations for safety issues."""
    
    # Dangerous Alembic operations
    DANGEROUS_OPERATIONS = [
        'drop_table',
        'drop_column', 
        'drop_index',
        'drop_constraint',
        'drop_sequence',
        'truncate_table',
        'execute.*DROP',
        'execute.*TRUNCATE',
        'execute.*DELETE.*FROM',
    ]
    
    # Operations that need backup confirmation
    BACKUP_REQUIRED_OPERATIONS = [
        'alter_column',
        'drop_',
        'execute.*ALTER',
        'execute.*UPDATE.*SET',
        'bulk_insert',
        'bulk_update',
    ]
    
    # Production environment indicators
    PRODUCTION_INDICATORS = [
        'prod',
        'production', 
        'prd',
        'live',
        'master',
        'main'
    ]
    
    # Database URLs that suggest production
    PRODUCTION_DB_PATTERNS = [
        r'postgresql://.*prod.*',
        r'postgresql://.*production.*',
        r'postgresql://.*live.*',
        r'mysql://.*prod.*',
        r'rds\.amazonaws\.com',
        r'\.prod\.',
        r'\.production\.',
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []
        
    def check_migration_command(self, command: str) -> List[Dict]:
        """Check a migration command for safety issues."""
        # Check for dangerous migration commands
        if 'alembic' in command:
            self.check_alembic_command(command)
            
        # Check for direct database commands
        if any(db_cmd in command.lower() for db_cmd in ['psql', 'mysql', 'sqlite']):
            self.check_direct_db_command(command)
            
        # Check environment
        self.check_database_environment()
        
        return self.violations
    
    def check_alembic_command(self, command: str):
        """Check Alembic command for safety."""
        # Check for destructive upgrades
        if 'upgrade' in command:
            self.check_upgrade_safety(command)
            
        # Check for downgrades
        if 'downgrade' in command:
            self.check_downgrade_safety(command)
            
        # Check for auto-generated migrations
        if 'revision' in command and '--autogenerate' in command:
            self.violations.append({
                'type': 'warning',
                'command': command,
                'message': 'Auto-generated migration - review carefully before applying',
                'suggestion': 'Review migration file and test in dev environment first'
            })
    
    def check_upgrade_safety(self, command: str):
        """Check upgrade command safety."""
        # Check for head upgrades in production-like environments
        if 'heads' in command or 'head' in command:
            if self.is_production_environment():
                self.violations.append({
                    'type': 'critical',
                    'command': command,
                    'message': 'Upgrading to head in production environment detected',
                    'suggestion': 'Use specific revision instead of head, ensure backup exists'
                })
            else:
                self.violations.append({
                    'type': 'warning',
                    'command': command,
                    'message': 'Upgrading to head - ensure migrations are tested',
                    'suggestion': 'Test migrations in dev/staging first'
                })
    
    def check_downgrade_safety(self, command: str):
        """Check downgrade command safety."""
        self.violations.append({
            'type': 'high',
            'command': command,
            'message': 'Database downgrade detected - potentially destructive',
            'suggestion': 'Ensure you have backups and understand data loss implications'
        })
    
    def check_direct_db_command(self, command: str):
        """Check direct database command safety."""
        # Check for destructive SQL
        dangerous_sql = ['DROP', 'TRUNCATE', 'DELETE', 'UPDATE']
        for sql in dangerous_sql:
            if sql.lower() in command.lower():
                self.violations.append({
                    'type': 'critical',
                    'command': command,
                    'message': f'Direct {sql} operation detected',
                    'suggestion': 'Use migrations instead of direct SQL for safety'
                })
                
        # Warn about direct database access
        if self.is_production_environment():
            self.violations.append({
                'type': 'high',
                'command': command,
                'message': 'Direct database access in production environment',
                'suggestion': 'Ensure you have proper authorization and backups'
            })
    
    def check_database_environment(self):
        """Check current database environment."""
        # Check environment variables
        db_url = os.environ.get('DATABASE_URL', '')
        
        if any(re.search(pattern, db_url, re.IGNORECASE) for pattern in self.PRODUCTION_DB_PATTERNS):
            self.violations.append({
                'type': 'warning',
                'message': 'Production database URL detected in environment',
                'suggestion': 'Verify you intended to run against production database'
            })
    
    def is_production_environment(self) -> bool:
        """Check if current environment is production-like."""
        # Check environment variables
        env_vars = ['ENV', 'ENVIRONMENT', 'STAGE', 'NODE_ENV', 'FLASK_ENV', 'FASTAPI_ENV']
        
        for var in env_vars:
            value = os.environ.get(var, '').lower()
            if any(prod in value for prod in self.PRODUCTION_INDICATORS):
                return True
                
        # Check database URL
        db_url = os.environ.get('DATABASE_URL', '').lower()
        if any(prod in db_url for prod in self.PRODUCTION_INDICATORS):
            return True
            
        return False
    
    def check_migration_file(self, file_path: Path) -> List[Dict]:
        """Check a migration file for dangerous operations."""
        if not file_path.exists():
            return []
            
        try:
            content = file_path.read_text(encoding='utf-8')
            self.check_migration_content(file_path, content)
        except Exception as e:
            self.violations.append({
                'type': 'error',
                'file': str(file_path),
                'message': f'Error reading migration file: {str(e)}'
            })
            
        return self.violations
    
    def check_migration_content(self, file_path: Path, content: str):
        """Check migration file content for dangerous operations."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            # Check for dangerous operations
            for operation in self.DANGEROUS_OPERATIONS:
                if re.search(operation, line_lower):
                    self.violations.append({
                        'type': 'critical',
                        'file': str(file_path),
                        'line': line_num,
                        'operation': operation,
                        'message': f'Dangerous operation {operation} detected',
                        'suggestion': 'Review carefully and ensure backups exist',
                        'context': line.strip()
                    })
                    
            # Check for backup-required operations
            for operation in self.BACKUP_REQUIRED_OPERATIONS:
                if re.search(operation, line_lower):
                    self.violations.append({
                        'type': 'warning',
                        'file': str(file_path),
                        'line': line_num,
                        'operation': operation,
                        'message': f'Operation {operation} may require backup',
                        'suggestion': 'Ensure database backup exists before applying',
                        'context': line.strip()
                    })


def main():
    """Main hook entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get tool information
    tool_name = input_data.get("tool_name", "")
    
    # Use current working directory as project root
    project_root = Path.cwd()
        
    checker = MigrationSafetyChecker(project_root)
    
    violations = []
    
    # Check based on tool type
    if tool_name == "Bash":
        # Check bash commands for migration operations
        tool_input = input_data.get("tool_input", {})
        command = tool_input.get("command", "")
        
        if any(cmd in command.lower() for cmd in ['alembic', 'migrate', 'psql', 'mysql']):
            violations = checker.check_migration_command(command)
            
    elif tool_name in ["Edit", "MultiEdit", "Write"]:
        # Check migration files
        tool_input = input_data.get("tool_input", {})
        file_path_str = tool_input.get("file_path", "")
        
        if file_path_str and ('migration' in file_path_str or 'alembic' in file_path_str):
            file_path = Path(file_path_str)
            violations = checker.check_migration_file(file_path)
    
    if not violations:
        sys.exit(0)
    
    # Log results
    log_file = Path.home() / ".claude/logs/migration_safety.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
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
    
    # Separate violations by severity
    critical_violations = [v for v in violations if v.get('type') == 'critical']
    high_violations = [v for v in violations if v.get('type') == 'high']
    warning_violations = [v for v in violations if v.get('type') == 'warning']
    other_violations = [v for v in violations if v.get('type') not in ['critical', 'high', 'warning']]
    
    # Show warnings (non-blocking)
    non_blocking = warning_violations + other_violations
    if non_blocking:
        print("⚠️  DATABASE MIGRATION WARNINGS:", file=sys.stderr)
        for violation in non_blocking:
            print(f"   {violation.get('message', 'Unknown warning')}", file=sys.stderr)
            if 'suggestion' in violation:
                print(f"   💡 {violation['suggestion']}", file=sys.stderr)
            if 'context' in violation:
                print(f"   📄 {violation['context']}", file=sys.stderr)
        print("", file=sys.stderr)
    
    # Block on critical and high violations
    blocking_violations = critical_violations + high_violations  
    if blocking_violations:
        print("🚫 DANGEROUS DATABASE OPERATION DETECTED", file=sys.stderr)
        print("", file=sys.stderr)
        
        for violation in blocking_violations:
            severity_emoji = "🚨" if violation.get('type') == 'critical' else "⚠️"
            print(f"{severity_emoji} {violation.get('message', 'Unknown violation')}", file=sys.stderr)
            
            if 'command' in violation:
                print(f"   Command: {violation['command']}", file=sys.stderr)
            if 'file' in violation:
                print(f"   File: {violation.get('file')}:{violation.get('line', 0)}", file=sys.stderr)
            if 'operation' in violation:
                print(f"   Operation: {violation['operation']}", file=sys.stderr)
            if 'context' in violation:
                print(f"   Context: {violation['context']}", file=sys.stderr)
            if 'suggestion' in violation:
                print(f"   💡 Fix: {violation['suggestion']}", file=sys.stderr)
            print("", file=sys.stderr)
        
        print("🗄️  Database operations require careful review and backups!", file=sys.stderr)
        print("💾 Ensure you have recent backups before proceeding", file=sys.stderr)
        print(f"📋 Details logged to: {log_file}", file=sys.stderr)
        
        sys.exit(2)  # Block the operation
    
    # Success with warnings
    if non_blocking:
        print(f"✅ Database safety check completed with warnings (logged to {log_file})")
    
    sys.exit(0)


if __name__ == "__main__":
    main()