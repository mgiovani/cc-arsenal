"""Regenerate the skill lists in README.md, AGENTS.md and docs/features.md.

Single source of truth: skills.sh.json for group membership, plus each
skills/*/SKILL.md frontmatter for name, metadata.summary and
disable-model-invocation. Group and skill ordering is computed alphabetically,
never curated, so skills.sh.json is itself rewritten in sorted order.

Note: total skill counts are maintained by SKILL_COUNT_RE over an explicit
allowlist rather than inline markers, which would litter four prose sentences.
docs/troubleshooting.md is deliberately excluded -- its `head -20
~/.claude/skills/...` shell examples sit near the word "skills" but are not counts.

Usage: python -m scripts.gen_skill_docs [--check]
"""

import argparse
import difflib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
GROUPS_PATH = ROOT / 'skills.sh.json'
SKILLS_DIR = ROOT / 'skills'
MARKETPLACE_PATH = ROOT / '.claude-plugin' / 'marketplace.json'

# The gap excludes / and " so a digit inside a JSON path like "./skills/x-10/"
# is never mistaken for a count of skills.
SKILL_COUNT_RE = re.compile(r'\b\d{2,3}\b(?=[^\n\"/]{0,30}?\bskills?\b)', re.I)
# A group heading, not just any heading -- see split_feature_bodies.
GROUP_HEADING_RE = re.compile(r'^#{2,3} .+\(\d+ skills?\)\s*$', re.M)
COUNT_FILES = (
    'README.md',
    'AGENTS.md',
    'docs/features.md',
    'docs/getting-started.md',
    'docs/onboarding.md',
    'CONTRIBUTING.md',
    '.claude-plugin/plugin.json',
    '.claude-plugin/marketplace.json',
)

GENERATED_HINT = (
    '<!-- generated: edit skills.sh.json or SKILL.md frontmatter, '
    'then run `make docs` -->'
)
SUMMARY_FALLBACK_LEN = 120
FRONTMATTER_PARTS = 3  # '', the YAML block, the body


def _plural(count: int) -> str:
    return f'{count} skill' if count == 1 else f'{count} skills'


AGENTS_INTRO = (
    'All skills use progressive disclosure '
    '(SKILL.md + optional references/scripts/assets directories).'
)
FEATURES_INTRO = (
    'Every skill is callable as `/<name>` in Claude Code. **(auto)** marks skills '
    'that *also* trigger automatically when Claude detects a relevant task; '
    '**(manual)** marks slash-only skills (`disable-model-invocation: true`).'
)


class Skill(NamedTuple):
    name: str
    summary: str
    manual: bool


class Group(NamedTuple):
    title: str
    description: str
    skills: tuple[Skill, ...]


def normalize(name: str) -> str:
    """Mirror skills.sh matching: case-insensitive, spaces/underscores are hyphens."""
    return re.sub(r'[\s_]+', '-', name.strip().lower())


def read_frontmatter(path: Path) -> dict[str, Any]:
    parts = path.read_text().split('---\n', 2)
    if len(parts) != FRONTMATTER_PARTS or parts[0] != '':
        raise SystemExit(f'error: {path}: missing or malformed YAML frontmatter')
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise SystemExit(f'error: {path}: invalid YAML frontmatter: {exc}') from exc
    if not isinstance(data, dict):
        raise SystemExit(f'error: {path}: frontmatter is not a mapping')
    return data


def summarize(description: str, override: str | None) -> str:
    if override:
        return override.strip()
    first = re.split(r'(?<=[.!?])\s', description.strip(), maxsplit=1)[0]
    if len(first) <= SUMMARY_FALLBACK_LEN:
        return first
    return first[:SUMMARY_FALLBACK_LEN].rsplit(' ', 1)[0] + '…'


def load_skills() -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    missing: list[str] = []
    for path in sorted(SKILLS_DIR.glob('*/SKILL.md')):
        dir_name = path.parent.name
        data = read_frontmatter(path)
        if data.get('name') != dir_name:
            raise SystemExit(
                f'error: {path}: frontmatter name {data.get("name")!r} '
                f'does not match directory {dir_name!r}'
            )
        description = data.get('description')
        if not isinstance(description, str) or not description.strip():
            raise SystemExit(f'error: {path}: frontmatter needs a non-empty description')
        metadata = data.get('metadata') or {}
        override = metadata.get('summary') if isinstance(metadata, dict) else None
        if not override:
            missing.append(dir_name)
        skills[dir_name] = Skill(
            name=dir_name,
            summary=summarize(description, override),
            manual=bool(data.get('disable-model-invocation')),
        )
    if missing:
        print(  # noqa: T201 -- CLI script, stdlib-only by design
            f'notice: {len(missing)} skill(s) missing metadata.summary: '
            f'{", ".join(missing)}'
        )
    return skills


def load_groups(skills: Mapping[str, Skill]) -> list[Group]:
    if not GROUPS_PATH.exists():
        raise SystemExit(f'error: {GROUPS_PATH.name} not found')
    try:
        config = json.loads(GROUPS_PATH.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f'error: invalid JSON in {GROUPS_PATH.name}: {exc}') from exc

    by_name = {normalize(name): name for name in skills}
    seen: dict[str, str] = {}
    groups: list[Group] = []
    for entry in config.get('groupings', []):
        title = entry['title']
        members: list[Skill] = []
        for raw in entry['skills']:
            key = normalize(raw)
            if key not in by_name:
                raise SystemExit(
                    f'error: {GROUPS_PATH.name}: group {title!r} lists unknown '
                    f'skill {raw!r}'
                )
            if key in seen:
                raise SystemExit(
                    f'error: {GROUPS_PATH.name}: skill {raw!r} is in both '
                    f'{seen[key]!r} and {title!r}'
                )
            seen[key] = title
            members.append(skills[by_name[key]])
        groups.append(
            Group(
                title=title,
                description=entry.get('description', ''),
                skills=tuple(sorted(members, key=lambda s: normalize(s.name))),
            )
        )

    ungrouped = sorted(set(skills) - {by_name[k] for k in seen})
    if ungrouped:
        raise SystemExit(
            f'error: {GROUPS_PATH.name}: not in any group: {", ".join(ungrouped)} '
            f'-- add them to a grouping'
        )
    return sorted(groups, key=lambda g: normalize(g.title))


def validate_marketplace(skills: Mapping[str, Skill]) -> None:
    config = json.loads(MARKETPLACE_PATH.read_text())
    covered: set[str] = set()
    for plugin in config['plugins']:
        listed = plugin.get('skills')
        if listed is None:
            continue
        for rel in listed:
            name = rel.strip('./').removeprefix('skills/')
            if name not in skills:
                raise SystemExit(
                    f'error: {MARKETPLACE_PATH.name}: plugin {plugin["name"]!r} '
                    f'lists unknown skill path {rel!r}'
                )
            covered.add(name)

    root = next(p for p in config['plugins'] if p['name'] == 'cc-arsenal')
    if 'skills' in root:
        raise SystemExit(
            f'error: {MARKETPLACE_PATH.name}: the cc-arsenal plugin must NOT have a '
            f'"skills" key -- unset means auto-load every skill'
        )
    uncovered = sorted(set(skills) - covered)
    if uncovered:
        raise SystemExit(
            f'error: {MARKETPLACE_PATH.name}: no plugin variant includes: '
            f'{", ".join(uncovered)}'
        )


def render_groups_json(groups: Sequence[Group]) -> str:
    config = json.loads(GROUPS_PATH.read_text())
    config['groupings'] = [
        {
            'title': group.title,
            'description': group.description,
            'skills': [skill.name for skill in group.skills],
        }
        for group in groups
    ]
    return json.dumps(config, indent=2) + '\n'


def render_readme(groups: Sequence[Group], total: int) -> str:
    lines = [GENERATED_HINT, '', f'**{total} Skills** organized by category:', '']
    for group in groups:
        lines += [
            '<details>',
            f'<summary><b>{group.title}</b> ({len(group.skills)}) — '
            f'{group.description}</summary>',
            '',
            '| Skill | What it does |',
            '|---|---|',
        ]
        lines += [
            f'| [`{s.name}`](skills/{s.name}/) | {s.summary} |' for s in group.skills
        ]
        lines += ['', '</details>', '']
    return '\n'.join(lines).rstrip('\n')


def render_agents(groups: Sequence[Group], total: int) -> str:
    lines = [
        GENERATED_HINT,
        '',
        f'## Available Skills ({total} total)',
        '',
        AGENTS_INTRO,
    ]
    for group in groups:
        lines += [
            '',
            f'### {group.title} ({_plural(len(group.skills))})',
            '',
            group.description,
            '',
        ]
        lines += [f'- **{s.name}**: {s.summary}' for s in group.skills]
    return '\n'.join(lines)


def split_feature_bodies(block: str) -> dict[str, str]:
    bodies: dict[str, str] = {}
    matches = list(re.finditer(r'^#### `/([a-z0-9-]+)` \((auto|manual)\)$', block, re.M))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        body = block[match.end() : end]
        # A group heading sitting between two skills belongs to the next group, not to
        # the body above it -- without this the heading is re-emitted twice per group.
        # Matched by group-heading shape, not by "is a heading": a skill body may
        # legitimately contain its own ### subheading, and truncating there would
        # delete hand-written prose permanently on the next run.
        heading = GROUP_HEADING_RE.search(body)
        if heading is not None:
            body = body[: heading.start()]
        bodies[match.group(1)] = body.strip('\n')
    return bodies


def render_features(
    groups: Sequence[Group], bodies: Mapping[str, str], total: int
) -> str:
    lines = [GENERATED_HINT, '', f'## Skills ({total} total)', '', FEATURES_INTRO]
    for group in groups:
        lines += ['', f'### {group.title} ({_plural(len(group.skills))})', '']
        lines.append(group.description)
        for skill in group.skills:
            tag = 'manual' if skill.manual else 'auto'
            lines += ['', f'#### `/{skill.name}` ({tag})']
            lines.append(bodies.get(skill.name) or skill.summary)
    return '\n'.join(lines)


def _block_re(block_id: str) -> re.Pattern[str]:
    marker = re.escape(block_id)
    return re.compile(
        rf'<!-- gen:{marker} start -->\n(.*?)\n<!-- gen:{marker} end -->', re.DOTALL
    )


def _require_markers(text: str, block_id: str, path: Path) -> re.Match[str]:
    starts = text.count(f'<!-- gen:{block_id} start -->')
    ends = text.count(f'<!-- gen:{block_id} end -->')
    if starts != 1 or ends != 1:
        raise SystemExit(
            f'error: {path.name}: {block_id}: expected 1 start and 1 end marker, '
            f'found {starts} and {ends}'
        )
    match = _block_re(block_id).search(text)
    if match is None:
        raise SystemExit(
            f'error: {path.name}: {block_id}: end marker precedes start marker'
        )
    return match


def replace_block(text: str, block_id: str, body: str, path: Path) -> str:
    match = _require_markers(text, block_id, path)
    return text[: match.start(1)] + body + text[match.end(1) :]


def apply_counts(text: str, total: int, path: Path, block_id: str | None = None) -> str:
    """Rewrite every skill-count phrase outside the generated block.

    Content inside the block is skipped: it is rendered fresh anyway, and it holds
    hand-written bodies this generator preserves verbatim -- a sentence like
    "one of 12 supported skill toolchains" there would otherwise be silently
    rewritten to the skill total, and then read back as the next run's baseline.
    """
    if block_id is None:
        spans = [(0, len(text))]
    else:
        match = _require_markers(text, block_id, path)
        spans = [(0, match.start(1)), (match.end(1), len(text))]

    pieces: list[str] = []
    cursor = 0
    count = 0
    for start, end in spans:
        pieces.append(text[cursor:start])
        chunk, found = SKILL_COUNT_RE.subn(str(total), text[start:end])
        pieces.append(chunk)
        count += found
        cursor = end
    pieces.append(text[cursor:])

    if count == 0:
        raise SystemExit(
            f'error: {path.name}: no skill count matched -- remove it from '
            f'COUNT_FILES or restore a "<N> skills" phrase'
        )
    return ''.join(pieces)


def build_targets(groups: Sequence[Group], total: int) -> dict[Path, str]:
    blocks = {
        ROOT / 'README.md': ('skills-readme', lambda _: render_readme(groups, total)),
        ROOT / 'AGENTS.md': ('skills-agents', lambda _: render_agents(groups, total)),
        ROOT / 'docs' / 'features.md': (
            'skills-features',
            lambda old: render_features(groups, split_feature_bodies(old), total),
        ),
    }
    targets: dict[Path, str] = {GROUPS_PATH: render_groups_json(groups)}
    for rel in COUNT_FILES:
        path = ROOT / rel
        text = path.read_text()
        entry = blocks.get(path)
        if entry is None:
            targets[path] = apply_counts(text, total, path)
            continue
        block_id, render = entry
        old = _require_markers(text, block_id, path).group(1)
        text = replace_block(text, block_id, render(old), path)
        targets[path] = apply_counts(text, total, path, block_id)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--check', action='store_true', help='exit non-zero if docs are out of date'
    )
    args = parser.parse_args()

    skills = load_skills()
    groups = load_groups(skills)
    validate_marketplace(skills)
    targets = build_targets(groups, len(skills))

    stale = [path for path, text in targets.items() if path.read_text() != text]
    if args.check:
        for path in stale:
            rel = path.relative_to(ROOT)
            diff = difflib.unified_diff(
                path.read_text().splitlines(),
                targets[path].splitlines(),
                fromfile=f'{rel} (on disk)',
                tofile=f'{rel} (generated)',
                lineterm='',
                n=1,
            )
            print('\n'.join(list(diff)[:40]))  # noqa: T201 -- CLI script
            print(f'drift: {rel}')  # noqa: T201 -- CLI script
        if stale:
            print(  # noqa: T201 -- CLI script
                f'{len(stale)} file(s) out of date -- run: make docs'
            )
            sys.exit(1)
        print('skill docs are up to date')  # noqa: T201 -- CLI script
        return

    for path in stale:
        path.write_text(targets[path])
        print(f'{path.relative_to(ROOT)}: updated')  # noqa: T201 -- CLI script
    if not stale:
        print('skill docs already up to date')  # noqa: T201 -- CLI script


if __name__ == '__main__':
    main()
