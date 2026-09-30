from collections import Counter
from typing import Any

SEP = ' — '


def _kind(entry: dict[str, Any], kinds: dict[int, str] | None) -> str:
    votes = Counter(kinds[u] for u in entry['units'] if kinds and u in kinds)
    return votes.most_common(1)[0][0] if votes else entry['kind']


def render_index(plan: dict[str, Any], kinds: dict[int, str] | None = None) -> str:
    """references/INDEX.md: one `path - summary (~Nk tok) [kind]` line per file.

    `kinds` (unit id to kind, e.g. from judge.json) overrides the kind stored in the plan.
    """
    lines = ['# Reference index', '']
    for section in plan['sections']:
        lines += [f'## {section["title"]}', '']
        lines += [
            f'{f["path"]}{SEP}{f["summary"]} (~{f["tokens"] / 1000:.1f}k tok) [{_kind(f, kinds)}]'
            for f in section['files']
        ]
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'
