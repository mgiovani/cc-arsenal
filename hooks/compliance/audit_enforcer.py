#!/usr/bin/env python3
"""
Audit log enforcer for Claude Code.
Ensures medical operations have proper audit logging.
"""

import json
import sys
import re
import ast
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class AuditEnforcer:
    """Enforces audit logging for medical operations."""

    # Operations that require audit logging
    AUDIT_REQUIRED_OPERATIONS = [
        "create_report",
        "update_report",
        "delete_report",
        "create_finding",
        "update_finding",
        "delete_finding",
        "update_quality_control",
        "create_quality_control",
        "update_report_organ",
        "create_report_organ",
        "update_patient",
        "create_patient",
        "update_study",
        "generate_pdf",
        "export_report",
        "update_rendered_summary",
        "create_rendered_summary",
    ]

    # Database operations that need audit logging
    DB_OPERATIONS_NEEDING_AUDIT = [
        "insert",
        "update",
        "delete",
        "merge",
        "bulk_insert_mappings",
        "bulk_update_mappings",
    ]

    # Patterns to identify sensitive functions
    SENSITIVE_FUNCTION_PATTERNS = [
        r"async def.*(?:create|update|delete|modify).*(?:report|finding|patient|study|organ|quality)",
        r"def.*(?:create|update|delete|modify).*(?:report|finding|patient|study|organ|quality)",
        r"async def.*(?:generate|export).*(?:pdf|report|summary)",
        r"def.*(?:generate|export).*(?:pdf|report|summary)",
    ]

    # Medical entities that need audit logging
    MEDICAL_ENTITIES = [
        "report",
        "finding",
        "patient",
        "study",
        "organ",
        "quality_control",
        "pdf",
        "summary",
        "medical",
        "condition",
    ]

    def __init__(self):
        self.violations = []

    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a Python file for audit logging violations."""
        if not file_path.exists() or not file_path.name.endswith(".py"):
            return []

        # Only check service and API files
        if not self.should_check_file(file_path):
            return []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse AST to analyze functions
            tree = ast.parse(content)
            self.analyze_ast(file_path, tree, content.split("\n"))

        except Exception as e:
            self.violations.append(
                {
                    "type": "error",
                    "file": str(file_path),
                    "message": f"Error analyzing file: {str(e)}",
                    "line": 0,
                }
            )

        return self.violations

    def should_check_file(self, file_path: Path) -> bool:
        """Check if file should be audited."""
        # Check service and API files
        check_files = ["services.py", "api.py", "crud.py", "endpoints.py"]
        if file_path.name in check_files:
            return True

        # Check if file is in medical domains
        path_str = str(file_path)
        for entity in self.MEDICAL_ENTITIES:
            if entity in path_str:
                return True

        return False

    def analyze_ast(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Analyze AST for audit logging violations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                self.check_function(file_path, node, lines)

    def check_function(
        self, file_path: Path, func_node: ast.FunctionDef, lines: List[str]
    ):
        """Check if function needs audit logging."""
        func_name = func_node.name

        # Check if function requires audit logging
        needs_audit = self.function_needs_audit(func_name, func_node)

        if needs_audit:
            has_audit = self.function_has_audit_logging(func_node, lines)

            if not has_audit:
                severity = self.get_violation_severity(func_name, func_node)

                self.violations.append(
                    {
                        "type": "missing_audit",
                        "severity": severity,
                        "file": str(file_path),
                        "function": func_name,
                        "line": func_node.lineno,
                        "message": f"Function {func_name} requires audit logging",
                        "suggestion": self.get_audit_suggestion(func_name, func_node),
                    }
                )

    def function_needs_audit(self, func_name: str, func_node: ast.FunctionDef) -> bool:
        """Check if function needs audit logging."""
        # Check function name patterns
        if any(
            operation in func_name.lower()
            for operation in self.AUDIT_REQUIRED_OPERATIONS
        ):
            return True

        # Check function signature patterns
        func_signature = f"{'async ' if isinstance(func_node, ast.AsyncFunctionDef) else ''}def {func_name}"
        for pattern in self.SENSITIVE_FUNCTION_PATTERNS:
            if re.match(pattern, func_signature, re.IGNORECASE):
                return True

        # Check if function has database operations
        if self.function_has_db_operations(func_node):
            return True

        return False

    def function_has_db_operations(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has database operations."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if node.attr in self.DB_OPERATIONS_NEEDING_AUDIT:
                    return True
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.DB_OPERATIONS_NEEDING_AUDIT:
                        return True
        return False

    def function_has_audit_logging(
        self, func_node: ast.FunctionDef, lines: List[str]
    ) -> bool:
        """Check if function has audit logging."""
        # Get function body lines
        start_line = func_node.lineno - 1
        end_line = (
            func_node.end_lineno if hasattr(func_node, "end_lineno") else len(lines)
        )

        function_lines = lines[start_line:end_line]
        function_content = "\n".join(function_lines)

        # Check for audit logging patterns
        audit_patterns = [
            r"log_audit\s*\(",
            r"logger\.audit\s*\(",
            r"audit_log_info",
            r"AuditLogInfo",
            r"await log_audit",
        ]

        return any(re.search(pattern, function_content) for pattern in audit_patterns)

    def get_violation_severity(self, func_name: str, func_node: ast.FunctionDef) -> str:
        """Get severity of audit violation."""
        # Critical for patient data operations
        critical_operations = ["patient", "report", "finding", "medical", "study"]

        if any(op in func_name.lower() for op in critical_operations):
            return "critical"

        # High for quality control and export operations
        high_operations = ["quality", "export", "generate", "pdf"]

        if any(op in func_name.lower() for op in high_operations):
            return "high"

        return "medium"

    def get_audit_suggestion(self, func_name: str, func_node: ast.FunctionDef) -> str:
        """Get audit logging suggestion."""
        if "create" in func_name.lower():
            return "Add audit logging with AuditAction.CREATE and log_audit() call"
        elif "update" in func_name.lower():
            return "Add audit logging with AuditAction.UPDATE and log_audit() call"
        elif "delete" in func_name.lower():
            return "Add audit logging with AuditAction.DELETE and log_audit() call"
        elif "export" in func_name.lower() or "generate" in func_name.lower():
            return "Add audit logging with AuditAction.READ and log_audit() call for data access"
        else:
            return "Add appropriate audit logging with log_audit() call"


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
    if not file_path_str or not file_path_str.endswith(".py"):
        sys.exit(0)

    file_path = Path(file_path_str)

    # Initialize enforcer
    enforcer = AuditEnforcer()
    violations = enforcer.check_file(file_path)

    # Log results
    log_file = Path.home() / ".claude/logs/audit_enforcer.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": file_path_str,
        "tool": tool_name,
        "violations": len(violations),
        "details": violations,
    }

    # Append to log
    if log_file.exists():
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    if not violations:
        sys.exit(0)

    # Separate violations by severity
    critical_violations = [v for v in violations if v.get("severity") == "critical"]
    high_violations = [v for v in violations if v.get("severity") == "high"]
    medium_violations = [v for v in violations if v.get("severity") == "medium"]
    other_violations = [v for v in violations if "severity" not in v]

    # Show medium and other violations as warnings (non-blocking)
    warning_violations = medium_violations + other_violations
    if warning_violations:
        print("⚠️  AUDIT LOGGING WARNINGS:", file=sys.stderr)
        for violation in warning_violations:
            print(f"   {violation.get('message', 'Unknown issue')}", file=sys.stderr)
            if "suggestion" in violation:
                print(f"   💡 {violation['suggestion']}", file=sys.stderr)
        print("", file=sys.stderr)

    # Block on critical and high violations
    blocking_violations = critical_violations + high_violations
    if blocking_violations:
        print(
            "🚫 AUDIT LOGGING VIOLATIONS - MEDICAL COMPLIANCE REQUIRED", file=sys.stderr
        )
        print("", file=sys.stderr)

        for violation in blocking_violations:
            severity_emoji = "🚨" if violation.get("severity") == "critical" else "⚠️"
            print(
                f"{severity_emoji} {violation.get('message', 'Unknown violation')}",
                file=sys.stderr,
            )
            print(
                f"   File: {violation.get('file')}:{violation.get('line', 0)}",
                file=sys.stderr,
            )
            print(
                f"   Function: {violation.get('function', 'unknown')}", file=sys.stderr
            )
            print(
                f"   Severity: {violation.get('severity', 'unknown').upper()}",
                file=sys.stderr,
            )
            if "suggestion" in violation:
                print(f"   💡 Fix: {violation['suggestion']}", file=sys.stderr)
            print("", file=sys.stderr)

        print(
            "🏥 Medical operations require audit logging for HIPAA compliance!",
            file=sys.stderr,
        )
        print("📋 Add AuditLogInfo dependency and log_audit() calls", file=sys.stderr)
        print(f"📋 Details logged to: {log_file}", file=sys.stderr)

        sys.exit(2)  # Block the operation

    # Success with warnings
    if warning_violations:
        print(f"✅ Audit logging check completed with warnings (logged to {log_file})")

    sys.exit(0)


if __name__ == "__main__":
    main()
