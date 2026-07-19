#!/usr/bin/env python3
"""Selective installation wizard for Claude Code Arsenal.

Allows users to interactively choose which components to symlink
to their ~/.claude directory, without modifying settings.json.
"""

import sys
from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

# Import from install.py to reuse proven architecture
from scripts.setup.install import (
    ConflictManager,
    ConflictResolution,
    FileDiscovery,
    InstallationConfig,
    InstallationItem,
    SymlinkManager,
)

console = Console()

# Constants
MAX_PREVIEW_ITEMS = 3  # Max items to show in component preview


def get_repo_root() -> Path:
    """Get the repository root directory."""
    # This script is in scripts/setup/, so go up 2 levels
    return Path(__file__).parent.parent.parent


def organize_by_category(
    items: list[InstallationItem],
) -> dict[str, dict[str, list[InstallationItem]]]:
    """Organize installation items by category and subcategory.

    Returns:
        Dict structure: {category: {subcategory: [items]}}
        Example: {'skills': {'docs-adr': [item1, item2], 'git-commit': [item3]}}
    """
    organized: dict[str, dict[str, list[InstallationItem]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for item in items:
        # Extract subcategory from path (e.g., "skills/docs-adr/SKILL.md" -> "docs-adr")
        parts = Path(item.name).parts
        if len(parts) > 1:
            subcategory = parts[0]
            organized[item.category][subcategory].append(item)
        else:
            # No subcategory, use "other"
            organized[item.category]['other'].append(item)

    return organized


def display_component_tree(
    organized: dict[str, dict[str, list[InstallationItem]]],
) -> None:
    """Display available components in a tree structure."""
    table = Table(title='CC-Arsenal Components')
    table.add_column('Category', style='cyan', no_wrap=True)
    table.add_column('Component', style='green')
    table.add_column('Count', style='yellow', justify='right')

    for category in sorted(organized.keys()):
        subcategories = organized[category]
        category_total = sum(len(items) for items in subcategories.values())

        # Add category header
        table.add_row(f'[bold]{category}[/bold]', '', str(category_total))

        # Add subcategories
        for subcat in sorted(subcategories.keys()):
            items = subcategories[subcat]
            preview_items = items[:MAX_PREVIEW_ITEMS]
            item_names = ', '.join(sorted(Path(item.name).stem for item in preview_items))
            if len(items) > MAX_PREVIEW_ITEMS:
                remaining = len(items) - MAX_PREVIEW_ITEMS
                item_names += f', ... (+{remaining} more)'
            table.add_row('', f'  {subcat}: {item_names}', str(len(items)))

    console.print(table)


def select_components(
    organized: dict[str, dict[str, list[InstallationItem]]],
) -> list[InstallationItem]:
    """Interactively select which components to install."""
    selected: list[InstallationItem] = []

    console.print('\n🔧 [bold]Select Components to Install[/bold]')
    console.print('Choose which components to symlink to ~/.claude/\n')

    for category in sorted(organized.keys()):
        console.print(f'📁 [bold cyan]{category.title()}[/bold cyan]')
        subcategories = organized[category]

        for subcat in sorted(subcategories.keys()):
            items = subcategories[subcat]
            subcat_display = subcat if subcat != 'other' else f'{category} (root)'

            # Ask about entire subcategory
            if Confirm.ask(
                f'  Install all {len(items)} items from [green]{subcat_display}[/green]?',
                default=True,
            ):
                selected.extend(items)
            else:
                # Ask about individual items
                for item in items:
                    item_name = Path(item.name).stem
                    if Confirm.ask(
                        f'    Install [green]{item_name}[/green]?', default=False
                    ):
                        selected.append(item)

        console.print()  # Blank line between categories

    return selected


def preview_installation(selected: list[InstallationItem]) -> None:
    """Show what will be installed."""
    console.print('\n📋 [bold]Installation Preview[/bold]')

    # Group by category
    by_category: dict[str, list[InstallationItem]] = defaultdict(list)
    for item in selected:
        by_category[item.category].append(item)

    for category in sorted(by_category.keys()):
        items = by_category[category]
        console.print(f'\n[cyan]{category}[/cyan] ({len(items)} items)')
        for item in sorted(items, key=lambda x: x.name):
            status = '🔄' if item.existing_is_symlink else '✨'
            console.print(f'  {status} {item.name}')


@click.command()
@click.option(
    '--dry-run',
    is_flag=True,
    help='Preview selection without creating symlinks',
)
def main(dry_run: bool) -> None:
    """Configure Claude Code Arsenal with selective component installation."""
    title = '⚙️  [bold blue]Claude Code Arsenal - Selective Installation[/bold blue]'
    console.print(title)
    console.print(
        'This wizard lets you choose which components to symlink to ~/.claude/\n'
    )

    # Set up configuration
    repo_root = get_repo_root()
    config = InstallationConfig(
        repo_root=repo_root,
        conflict_resolution=ConflictResolution.INTERACTIVE,
        backup_enabled=True,
    )

    # Check if ~/.claude exists
    if not config.claude_dir.exists():
        console.print(f'❌ [red]Claude directory not found at {config.claude_dir}[/red]')
        console.print('Create it first or run with `make install` for full installation')
        sys.exit(1)

    # Discover available components
    console.print('🔍 Discovering available components...')
    discovery = FileDiscovery(config)
    all_items = discovery.discover_installable_files()

    if not all_items:
        console.print('❌ [red]No installable components found[/red]')
        sys.exit(1)

    # Organize and display
    organized = organize_by_category(all_items)
    display_component_tree(organized)

    # Interactive selection
    selected_items = select_components(organized)

    if not selected_items:
        console.print('\n⚠️  [yellow]No components selected. Exiting.[/yellow]')
        sys.exit(0)

    # Preview
    preview_installation(selected_items)

    # Summary
    console.print(f'\n📊 [bold]Summary:[/bold] {len(selected_items)} components selected')

    if dry_run:
        console.print('\n🏁 [yellow]Dry run complete - no changes made[/yellow]')
        return

    # Confirm
    if not Confirm.ask('\nProceed with installation?', default=True):
        console.print('Installation cancelled')
        return

    # Handle conflicts
    conflict_manager = ConflictManager(config)
    conflicts = conflict_manager.analyze_conflicts(selected_items)
    resolutions = conflict_manager.resolve_conflicts_interactive(
        conflicts['existing_files']
    )

    # Install selected components
    console.print('\n🚀 Installing selected components...')
    symlink_manager = SymlinkManager(config)
    try:
        symlink_manager.install_files(selected_items, resolutions)
        console.print('\n✅ [bold green]Installation complete![/bold green]')
        console.print(
            f'🔗 {len(selected_items)} components symlinked to {config.claude_dir}'
        )
        console.print('\n💡 [yellow]Note:[/yellow] Your settings.json was not modified')
        console.print(
            '   To enable/disable components, edit ~/.claude/settings.json manually'
        )
        console.print('\n🔄 Please restart Claude Code to see changes')
    except (OSError, RuntimeError) as e:
        console.print(f'\n❌ [red]Installation failed: {e}[/red]')
        sys.exit(1)


if __name__ == '__main__':
    main()
