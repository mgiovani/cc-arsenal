import re

from anything_to_skill.core.models import Finding

_PATTERNS = {
    'private-key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'aws-access-key': r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b',
    'github-token': r'\bgh[pousr]_[A-Za-z0-9]{36,}\b',
    'slack-token': r'\bxox[abprs]-[A-Za-z0-9-]{10,}',
    'api-key': r'\bsk-[A-Za-z0-9_-]{20,}',
    'assigned-secret': (
        r'(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d)\b\s*[:=]\s*[\'"]?'
        r'(?=[A-Za-z0-9/+_.-]{16,})(?=\S*\d)[A-Za-z0-9/+_.-]+'
    ),
}
_COMPILED = {rule: re.compile(rx) for rule, rx in _PATTERNS.items()}


def scan(text: str) -> list[Finding]:
    """Credential-shaped strings; warn only, and never echo the match into the report."""
    return sorted(
        (
            Finding(
                f'secret:{rule}',
                'credential-like text; check the source before sharing the skill',
                text.count('\n', 0, m.start()) + 1,
                'warn',
            )
            for rule, rx in _COMPILED.items()
            for m in rx.finditer(text)
        ),
        key=lambda f: f.line or 0,
    )
