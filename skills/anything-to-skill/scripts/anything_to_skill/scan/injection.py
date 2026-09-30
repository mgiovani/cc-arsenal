import re

from anything_to_skill.core.models import Finding

_LEAD = r'(?:all\s+|any\s+|the\s+|your\s+)?'
_PATTERNS = {
    'override-instructions': (
        r'\b(?:ignore|disregard|forget|override)\s+'
        + _LEAD
        + r'(?:previous|prior|above|earlier|preceding|system|safety)\s+'
        r'(?:instructions?|prompts?|rules|context|guidelines)'
    ),
    'role-reassign': r'\byou\s+are\s+now\s+(?:a|an)\s+\w+',
    'prompt-exfil': (
        r'\b(?:reveal|print|show|output|repeat|leak)\s+(?:your|the)\s+'
        r'(?:system\s+prompt|hidden\s+instructions|initial\s+instructions)'
    ),
    'conceal-from-user': r'\bdo\s+not\s+(?:tell|inform|alert)\s+the\s+user',
    'new-instructions': r'\bnew\s+instructions?\s*:',
    'chat-template-token': (
        r'<\s*/?\s*(?:system|assistant|im_start|im_end)\s*>|<\|im_(?:start|end)\|>|\[/?INST\]'
    ),
    'hidden-comment-instruction': (
        r'<!--(?:(?!-->)[\s\S])*?\b(?:ignore|instructions?|assistant|system\s+prompt|you\s+must)\b'
        r'(?:(?!-->)[\s\S])*?-->'
    ),
    'pipe-to-shell': r'\b(?:curl|wget)\s[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b',
    'secret-exfil': (
        r'\b(?:send|post|upload|exfiltrate|leak)\s+(?:the\s+|your\s+|all\s+)?'
        r'(?:contents?|secrets?|api\s+keys?|credentials|tokens?|\.env|environment\s+variables?)'
        r'\s+to\s+\S+'
    ),
}
_COMPILED = {rule: re.compile(rx, re.IGNORECASE) for rule, rx in _PATTERNS.items()}


def scan(text: str) -> list[Finding]:
    """Prompt-injection phrase heuristics; hard by default, callers downgrade for references."""
    found = [
        Finding(
            f'injection:{rule}',
            f'suspicious text: {" ".join(m.group().split())[:80]!r}',
            text.count('\n', 0, m.start()) + 1,
            'hard',
        )
        for rule, rx in _COMPILED.items()
        for m in rx.finditer(text)
    ]
    return sorted(found, key=lambda f: f.line or 0)
