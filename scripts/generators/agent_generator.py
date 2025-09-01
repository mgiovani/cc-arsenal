#!/usr/bin/env python3
"""Agent generator for Claude template repository.
Creates new agent files from a template.
"""

from pathlib import Path

import click
from jinja2 import Template
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()

AGENT_TEMPLATE = """---
name: {{ name }}
description: "{{ description }}"
tools: {{ tools }}
---

# {{ title }}

{{ long_description }}

## Your Expertise

{{ expertise }}

## Core Principles

{{ principles }}

## Workflow

{{ workflow }}

## Communication Style

{{ communication_style }}

## Proactive Behaviors

{{ proactive_behaviors }}
"""


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.parent


def get_categories() -> dict[str, str]:
    """Get available agent categories."""
    return {
        'development': 'Development-focused agents (coding, testing, debugging)',
        'architecture': 'System architecture and design agents',
        'product': 'Product management and business analysis agents',
        'ux': 'User experience and design agents',
        'orchestration': 'Workflow orchestration and project management',
    }


@click.command()
@click.option('--name', help="Agent name (e.g., 'code-reviewer')")
@click.option('--category', help='Agent category')
@click.option('--description', help='Short description')
def main(name: str, category: str, description: str) -> None:
    """Generate a new Claude agent from template."""
    console.print('🤖 [bold blue]Claude Agent Generator[/bold blue]')

    repo_root = get_repo_root()
    agents_dir = repo_root / 'agents'

    # Get agent details
    if not name:
        name = Prompt.ask("Agent name (e.g., 'code-reviewer')")

    # Validate name
    if not name.replace('-', '').replace('_', '').isalnum():
        console.print(
            '❌ Agent name must contain only letters, numbers, hyphens, and underscores'
        )
        return

    # Get category
    categories = get_categories()
    if not category:
        console.print('\n📁 Available categories:')
        for cat, desc in categories.items():
            console.print(f'  • {cat}: {desc}')

        category = Prompt.ask(
            'Select category', choices=list(categories.keys()), default='development'
        )

    if category not in categories:
        console.print(f'❌ Invalid category. Choose from: {list(categories.keys())}')
        return

    # Get description
    if not description:
        description = Prompt.ask('Short description')

    # Get additional details
    title = Prompt.ask('Agent title', default=name.replace('-', ' ').title())
    long_description = Prompt.ask('Detailed description', default=description)

    tools = Prompt.ask(
        'Tools (comma-separated)', default='Read, Write, Edit, Bash, Grep, Glob'
    )

    expertise = Prompt.ask('Key expertise areas', default='- Area 1\n- Area 2\n- Area 3')
    principles = Prompt.ask('Core principles', default='- Principle 1\n- Principle 2')
    workflow = Prompt.ask('Typical workflow', default='1. Step 1\n2. Step 2\n3. Step 3')
    communication_style = Prompt.ask(
        'Communication style',
        default='- Direct and technical\n- Problem-focused\n- Collaborative',
    )
    proactive_behaviors = Prompt.ask(
        'Proactive behaviors', default='- Behavior 1\n- Behavior 2'
    )

    # Create agent file
    category_dir = agents_dir / category
    category_dir.mkdir(exist_ok=True)

    agent_file = category_dir / f'{name}.md'

    if agent_file.exists() and not Confirm.ask(
        f'Agent {name} already exists. Overwrite?'
    ):
        console.print('❌ Generation cancelled')
        return

    # Generate content
    template = Template(AGENT_TEMPLATE)
    content = template.render(
        name=name,
        description=description,
        title=title,
        long_description=long_description,
        tools=tools,
        expertise=expertise,
        principles=principles,
        workflow=workflow,
        communication_style=communication_style,
        proactive_behaviors=proactive_behaviors,
    )

    # Write file
    agent_file.write_text(content)

    console.print(f'✅ Agent created: {agent_file}')
    console.print(f'📁 Category: {category}')
    console.print(f'🏷️  Name: {name}')
    console.print(f'📝 Description: {description}')


if __name__ == '__main__':
    main()
