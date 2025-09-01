#!/usr/bin/env python3
"""
Configuration wizard for Claude template repository.
Helps users set up their preferred agents and commands.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


def get_claude_dir() -> Path:
    """Get the user's ~/.claude directory."""
    return Path.home() / ".claude"


def get_available_agents() -> Dict[str, List[str]]:
    """Get available agents organized by category."""
    claude_dir = get_claude_dir()
    agents_dir = claude_dir / "agents"
    
    if not agents_dir.exists():
        return {}
    
    agents = {}
    for category_dir in agents_dir.iterdir():
        if category_dir.is_dir():
            category_agents = []
            for agent_file in category_dir.glob("*.md"):
                category_agents.append(agent_file.stem)
            if category_agents:
                agents[category_dir.name] = category_agents
    
    return agents


def get_available_commands() -> Dict[str, List[str]]:
    """Get available commands organized by category."""
    claude_dir = get_claude_dir()
    commands_dir = claude_dir / "commands"
    
    if not commands_dir.exists():
        return {}
    
    commands = {}
    for category_dir in commands_dir.iterdir():
        if category_dir.is_dir():
            category_commands = []
            for command_file in category_dir.glob("*.md"):
                category_commands.append(command_file.stem)
            if category_commands:
                commands[category_dir.name] = category_commands
    
    return commands


def create_settings_config(selected_agents: List[str], selected_commands: List[str]) -> Dict[str, Any]:
    """Create a settings.json configuration."""
    return {
        "version": "1.0",
        "agents": {
            "enabled": selected_agents,
            "default_tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
        },
        "commands": {
            "enabled": selected_commands
        },
        "hooks": {
            "enabled": True,
            "security_level": "medium"
        },
        "ui": {
            "theme": "dark",
            "show_agent_descriptions": True
        }
    }


def display_available_items(items: Dict[str, List[str]], item_type: str) -> None:
    """Display available agents or commands in a table."""
    table = Table(title=f"Available {item_type.title()}")
    table.add_column("Category", style="cyan")
    table.add_column("Items", style="green")
    
    for category, item_list in items.items():
        table.add_row(category, ", ".join(item_list))
    
    console.print(table)


def select_items(items: Dict[str, List[str]], item_type: str) -> List[str]:
    """Allow user to select which items to enable."""
    selected = []
    
    console.print(f"\n🔧 Configure {item_type}")
    
    for category, item_list in items.items():
        console.print(f"\n📁 [bold]{category.title()}[/bold]")
        for item in item_list:
            if Confirm.ask(f"  Enable {item}?", default=True):
                selected.append(f"{category}/{item}")
    
    return selected


@click.command()
@click.option("--quick", is_flag=True, help="Quick setup with defaults")
def main(quick: bool) -> None:
    """Configure Claude template settings."""
    console.print("⚙️  [bold blue]Claude Configuration Wizard[/bold blue]")
    
    claude_dir = get_claude_dir()
    
    if not claude_dir.exists():
        console.print("❌ Claude directory not found. Please run `claude-install` first.")
        return
    
    # Get available items
    agents = get_available_agents()
    commands = get_available_commands()
    
    if not agents and not commands:
        console.print("❌ No agents or commands found. Check your installation.")
        return
    
    if quick:
        # Quick setup - enable everything
        selected_agents = [f"{cat}/{agent}" for cat, agent_list in agents.items() for agent in agent_list]
        selected_commands = [f"{cat}/{cmd}" for cat, cmd_list in commands.items() for cmd in cmd_list]
        console.print("🚀 Quick setup: enabling all agents and commands")
    else:
        # Interactive setup
        if agents:
            display_available_items(agents, "agents")
            selected_agents = select_items(agents, "agents")
        else:
            selected_agents = []
        
        if commands:
            display_available_items(commands, "commands")
            selected_commands = select_items(commands, "commands")
        else:
            selected_commands = []
    
    # Create configuration
    config = create_settings_config(selected_agents, selected_commands)
    
    # Write settings file
    settings_file = claude_dir / "settings.json"
    with open(settings_file, "w") as f:
        json.dump(config, f, indent=2)
    
    console.print(f"✅ Configuration saved to {settings_file}")
    
    # Summary
    console.print(f"\n📊 Configuration Summary:")
    console.print(f"   • {len(selected_agents)} agents enabled")
    console.print(f"   • {len(selected_commands)} commands enabled")
    
    console.print("\n🔄 Please restart Claude Code to apply changes.")


if __name__ == "__main__":
    main()