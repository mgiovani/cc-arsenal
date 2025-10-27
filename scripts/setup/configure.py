#!/usr/bin/env python3
"""Configuration wizard for Claude template repository.
Helps users set up their preferred agents and commands.
"""

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

console = Console()


def get_repo_root() -> Path:
    """Get the repository root directory."""
    # This script is in scripts/setup/, so go up 2 levels
    return Path(__file__).parent.parent.parent


def get_claude_dir() -> Path:
    """Get the user's ~/.claude directory."""
    return Path.home() / '.claude'


def get_available_agents() -> dict[str, list[str]]:
    """Get available agents organized by category from the repository."""
    repo_root = get_repo_root()
    agents_dir = repo_root / 'agents'

    if not agents_dir.exists():
        return {}

    agents = {}
    for category_dir in agents_dir.iterdir():
        if category_dir.is_dir():
            category_agents = []
            for agent_file in category_dir.glob('*.md'):
                # Skip README files - they're documentation, not agents
                if agent_file.stem.upper() != 'README':
                    category_agents.append(agent_file.stem)
            if category_agents:
                agents[category_dir.name] = category_agents

    return agents


def get_available_commands() -> dict[str, list[str]]:
    """Get available commands organized by category from the repository."""
    repo_root = get_repo_root()
    commands_dir = repo_root / 'commands'

    if not commands_dir.exists():
        return {}

    commands = {}
    for category_dir in commands_dir.iterdir():
        if category_dir.is_dir():
            category_commands = []
            for command_file in category_dir.glob('*.md'):
                # Skip README files - they're documentation, not commands
                if command_file.stem.upper() != 'README':
                    category_commands.append(command_file.stem)
            if category_commands:
                commands[category_dir.name] = category_commands

    return commands


def get_available_skills() -> list[str]:
    """Get available skills from the repository."""
    repo_root = get_repo_root()
    skills_dir = repo_root / 'skills'

    if not skills_dir.exists():
        return []

    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / 'SKILL.md').exists():
            skills.append(skill_dir.name)

    return skills


def create_settings_config(
    selected_agents: list[str], selected_commands: list[str]
) -> dict[str, Any]:
    """Create a settings.json configuration."""
    return {
        'version': '1.0',
        'agents': {
            'enabled': selected_agents,
            'default_tools': ['Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob'],
        },
        'commands': {'enabled': selected_commands},
        'hooks': {'enabled': True, 'security_level': 'medium'},
        'ui': {'theme': 'dark', 'show_agent_descriptions': True},
    }


def display_available_items(items: dict[str, list[str]], item_type: str) -> None:
    """Display available agents or commands in a table."""
    table = Table(title=f'Available {item_type.title()}')
    table.add_column('Category', style='cyan')
    table.add_column('Items', style='green')

    for category, item_list in items.items():
        table.add_row(category, ', '.join(item_list))

    console.print(table)


def select_items(items: dict[str, list[str]], item_type: str) -> list[str]:
    """Allow user to select which items to enable."""
    selected = []

    console.print(f'\n🔧 Configure {item_type}')

    for category, item_list in items.items():
        console.print(f'\n📁 [bold]{category.title()}[/bold]')
        for item in item_list:
            if Confirm.ask(f'  Enable {item}?', default=True):
                selected.append(f'{category}/{item}')

    return selected


@click.command()
@click.option('--quick', is_flag=True, help='Quick setup with defaults')
def main(quick: bool) -> None:
    """Configure Claude template settings."""
    console.print('⚙️  [bold blue]Claude Configuration Wizard[/bold blue]')

    claude_dir = get_claude_dir()

    if not claude_dir.exists():
        console.print('❌ Claude directory not found. Please run `claude-install` first.')
        return

    # Get available items from repository
    agents = get_available_agents()
    commands = get_available_commands()
    skills = get_available_skills()

    if not agents and not commands and not skills:
        console.print('❌ No components found in repository. Check your installation.')
        return

    console.print('\n📦 [bold]CC-Arsenal Components:[/bold]')
    cmd_count = sum(len(v) for v in commands.values())
    console.print(f'   • Commands: {cmd_count} across {len(commands)} categories')
    console.print(f'   • Skills: {len(skills)}')
    if agents:
        agent_count = sum(len(v) for v in agents.values())
        console.print(f'   • Agents: {agent_count} across {len(agents)} categories')
    console.print()

    if quick:
        # Quick setup - enable everything
        selected_agents = [
            f'{cat}/{agent}' for cat, agent_list in agents.items() for agent in agent_list
        ]
        selected_commands = [
            f'{cat}/{cmd}' for cat, cmd_list in commands.items() for cmd in cmd_list
        ]
        console.print('🚀 Quick setup: enabling all agents and commands')
    else:
        # Interactive setup
        if agents:
            display_available_items(agents, 'agents')
            selected_agents = select_items(agents, 'agents')
        else:
            selected_agents = []

        if commands:
            display_available_items(commands, 'commands')
            selected_commands = select_items(commands, 'commands')
        else:
            selected_commands = []

    # Create configuration
    config = create_settings_config(selected_agents, selected_commands)

    # Write settings file
    settings_file = claude_dir / 'settings.json'
    with settings_file.open('w') as f:
        json.dump(config, f, indent=2)

    console.print(f'✅ Configuration saved to {settings_file}')

    # Summary
    console.print('\n📊 Configuration Summary:')
    console.print(f'   • {len(selected_agents)} agents enabled')
    console.print(f'   • {len(selected_commands)} commands enabled')

    console.print('\n🔄 Please restart Claude Code to apply changes.')


if __name__ == '__main__':
    main()
