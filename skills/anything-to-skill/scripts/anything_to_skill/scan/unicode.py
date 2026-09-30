from collections import defaultdict

from anything_to_skill.core.models import Finding
from anything_to_skill.core.sanitize import find_invisible


def scan(text: str) -> list[Finding]:
    """One hard finding per line holding invisible characters; callers downgrade to warn."""
    by_line: dict[int, list[int]] = defaultdict(list)
    for offset, codepoint in find_invisible(text):
        by_line[text.count('\n', 0, offset) + 1].append(codepoint)
    return [
        Finding(
            'invisible-unicode',
            'hidden characters ' + ' '.join(f'U+{cp:04X}' for cp in cps),
            line,
            'hard',
        )
        for line, cps in sorted(by_line.items())
    ]
