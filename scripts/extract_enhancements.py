#!/usr/bin/env python3
"""Extract Claude Code-specific content from SKILL.md to create ENHANCEMENT.md files."""

import re
from pathlib import Path
from typing import Any

import yaml

# 22 main skills from CLAUDE.md
MAIN_SKILLS = [
    'implement-feature',
    'fix-bug',
    'review-security',
    'inject-nextjs-docs',
    'project-planner',
    'docs-adr',
    'docs-check',
    'docs-diagram',
    'docs-init',
    'docs-rfc',
    'docs-update',
    'git-commit',
    'git-create-pr',
    'jira-daily',
    'jira-todo',
    'create-command',
    'create-rule',
    'team-implement',
    'agent-browser',
    'find-skills',
    'skill-creator',
    'jira-cli',
]


def extract_frontmatter_and_body(skill_md_path: Path) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and markdown body from SKILL.md."""
    content = skill_md_path.read_text()

    # Extract frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not frontmatter_match:
        return {}, content

    frontmatter_text = frontmatter_match.group(1)
    body = frontmatter_match.group(2)

    frontmatter = yaml.safe_load(frontmatter_text)
    return frontmatter, body


def extract_claude_code_sections(body: str) -> str:
    """Extract Claude Code-specific sections from markdown body."""
    # Split into sections by ## headers
    sections = re.split(r'\n(?=## )', body)

    claude_content = []
    seen_headers = set()

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract section header
        header_match = re.match(r'^## (.+?)(?:\n|$)', section)
        if not header_match:
            continue

        header = header_match.group(1).strip()

        # Skip if we've already seen this section
        if header in seen_headers:
            continue

        # Include Claude Code-specific sections
        is_claude_section = any(
            [
                'quality gate' in header.lower(),
                'task management' in header.lower(),
                'workflow' in section.lower()
                and ('subagent' in section.lower() or 'task tool' in section.lower()),
                'todowrite' in section.lower(),
                '$ARGUMENTS' in section,
                'hook' in header.lower(),
            ]
        )

        if is_claude_section:
            claude_content.append(section)
            seen_headers.add(header)

    return '\n\n'.join(claude_content)


def create_enhancement_md(
    skill_name: str, frontmatter: dict[str, Any], claude_content: str
) -> str:
    """Create ENHANCEMENT.md content."""

    # Extract Claude Code-specific frontmatter fields
    enhancement_frontmatter = {}
    cc_fields = [
        'disable-model-invocation',
        'argument-hint',
        'allowed-tools',
        'hooks',
        'context',
        'agent',
    ]

    for field in cc_fields:
        if field in frontmatter:
            enhancement_frontmatter[field] = frontmatter[field]

    # Build ENHANCEMENT.md
    lines = ['---']
    lines.append(f'# Enhancement for: {skill_name}')

    for key, value in enhancement_frontmatter.items():
        if isinstance(value, bool):
            lines.append(f'{key}: {str(value).lower()}')
        elif isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, list):
            # Format lists properly
            lines.append(f'{key}:')
            for item in value:
                lines.append(f'  - {item}')
        elif isinstance(value, dict):
            # Format dicts properly (like hooks)
            lines.append(f'{key}:')
            yaml_str = yaml.dump(value, default_flow_style=False, sort_keys=False)
            for line in yaml_str.strip().split('\n'):
                lines.append(f'  {line}')

    lines.append('---')
    lines.append('')
    lines.append('## Claude Code Enhanced Features')
    lines.append('')

    if claude_content:
        lines.append(
            'This skill includes the following Claude Code-specific enhancements:'
        )
        lines.append('')
        lines.append(claude_content)
    else:
        lines.append(
            "This skill integrates with Claude Code's tool ecosystem for enhanced automation."
        )
        lines.append('')
        if 'allowed-tools' in enhancement_frontmatter:
            lines.append(
                f'**Allowed Tools**: {", ".join(enhancement_frontmatter["allowed-tools"])}'
            )
            lines.append('')

    return '\n'.join(lines)


def main() -> None:
    """Extract enhancements for all 22 main skills."""
    skills_dir = Path('skills')
    enhancements_dir = Path('enhancements')

    if not enhancements_dir.exists():
        return

    processed = 0
    for skill_name in MAIN_SKILLS:
        skill_dir = skills_dir / skill_name
        skill_md = skill_dir / 'SKILL.md'

        if not skill_md.exists():
            continue

        # Extract frontmatter and body
        frontmatter, body = extract_frontmatter_and_body(skill_md)

        # Extract Claude Code-specific sections
        claude_sections = extract_claude_code_sections(body)

        # Create ENHANCEMENT.md content
        enhancement_content = create_enhancement_md(
            skill_name, frontmatter, claude_sections
        )

        # Write to enhancements directory
        enhancement_dir = enhancements_dir / skill_name
        enhancement_dir.mkdir(exist_ok=True)
        enhancement_file = enhancement_dir / 'ENHANCEMENT.md'

        enhancement_file.write_text(enhancement_content)
        processed += 1


if __name__ == '__main__':
    main()
