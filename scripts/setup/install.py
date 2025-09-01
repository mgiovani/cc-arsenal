#!/usr/bin/env python3
"""Professional installation script for Claude template repository.

This module provides a robust installation system that creates individual file symlinks
from ~/.claude to the template repository, with conflict detection, backup functionality,
and selective installation capabilities.
"""

import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

import click
from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Configure rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


class ConflictResolution(str, Enum):
    """Strategies for handling file conflicts."""
    SKIP = "skip"
    BACKUP = "backup"
    OVERWRITE = "overwrite"
    INTERACTIVE = "interactive"


class InstallationItem(BaseModel):
    """Represents a single file to be installed."""
    source_path: Path
    target_path: Path
    category: str
    name: str
    conflicts: bool = False
    existing_is_symlink: bool = False

    def __hash__(self) -> int:
        """Make InstallationItem hashable for use as dict keys."""
        return hash((str(self.source_path), str(self.target_path), self.category, self.name))

    def __eq__(self, other: object) -> bool:
        """Define equality for InstallationItem."""
        if not isinstance(other, InstallationItem):
            return False
        return (
            self.source_path == other.source_path
            and self.target_path == other.target_path
            and self.category == other.category
            and self.name == other.name
        )


class InstallationConfig(BaseModel):
    """Configuration model for installation parameters."""

    claude_dir: Path = Field(default_factory=lambda: Path.home() / ".claude")
    repo_root: Path = Field(...)
    backup_enabled: bool = Field(default=True)
    force_install: bool = Field(default=False)
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.INTERACTIVE)
    required_dirs: List[str] = Field(default=["agents", "commands", "hooks"])

    @field_validator("repo_root")
    @classmethod
    def validate_repo_root(cls, v: Path) -> Path:
        """Validate that repo_root exists and contains required directories."""
        if not v.exists():
            msg = f"Repository root does not exist: {v}"
            raise ValueError(msg)
        return v

    @field_validator("claude_dir")
    @classmethod
    def validate_claude_dir(cls, v: Path) -> Path:
        """Ensure claude_dir is absolute path."""
        return v.expanduser().resolve()


class FileDiscovery:
    """Discovers and catalogs all installable files."""

    def __init__(self, config: InstallationConfig) -> None:
        """Initialize file discovery with configuration."""
        self.config = config

    def discover_installable_files(self) -> List[InstallationItem]:
        """Discover all files that can be installed."""
        items = []
        
        for directory in self.config.required_dirs:
            source_dir = self.config.repo_root / directory
            if not source_dir.exists():
                continue
                
            # Recursively find all .md and .py files
            for source_file in source_dir.rglob("*"):
                if source_file.is_file() and source_file.suffix in {".md", ".py"}:
                    # Calculate relative path from source directory
                    relative_path = source_file.relative_to(source_dir)
                    target_path = self.config.claude_dir / directory / relative_path
                    
                    item = InstallationItem(
                        source_path=source_file,
                        target_path=target_path,
                        category=directory,
                        name=str(relative_path)
                    )
                    
                    # Check for conflicts
                    if target_path.exists():
                        item.conflicts = True
                        item.existing_is_symlink = target_path.is_symlink()
                    
                    items.append(item)
        
        return items


class ConflictManager:
    """Manages file conflicts and resolution strategies."""

    def __init__(self, config: InstallationConfig) -> None:
        """Initialize conflict manager."""
        self.config = config

    def analyze_conflicts(self, items: List[InstallationItem]) -> Dict[str, List[InstallationItem]]:
        """Analyze and categorize conflicts."""
        conflicts = {
            "new_files": [],
            "existing_files": [],
            "existing_symlinks": [],
        }
        
        for item in items:
            if not item.conflicts:
                conflicts["new_files"].append(item)
            elif item.existing_is_symlink:
                conflicts["existing_symlinks"].append(item)
            else:
                conflicts["existing_files"].append(item)
        
        return conflicts

    def display_conflict_summary(self, conflicts: Dict[str, List[InstallationItem]]) -> None:
        """Display a summary of conflicts to the user."""
        table = Table(title="Installation Analysis")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Files", style="dim")
        
        table.add_row(
            "✅ New Files",
            str(len(conflicts["new_files"])),
            f"{len(conflicts['new_files'])} files will be installed"
        )
        
        if conflicts["existing_files"]:
            table.add_row(
                "⚠️ Conflicts",
                str(len(conflicts["existing_files"])),
                "Files that already exist (not symlinks)"
            )
        
        if conflicts["existing_symlinks"]:
            table.add_row(
                "🔄 Updates",
                str(len(conflicts["existing_symlinks"])),
                "Existing symlinks that will be updated"
            )
        
        console.print(table)

    def resolve_conflicts_interactive(self, conflicted_items: List[InstallationItem]) -> Dict[InstallationItem, ConflictResolution]:
        """Resolve conflicts through interactive user prompts."""
        resolutions = {}
        
        if not conflicted_items:
            return resolutions
        
        console.print("\n🔍 [bold]Conflict Resolution Required[/bold]")
        
        # Group conflicts by category for easier review
        by_category = {}
        for item in conflicted_items:
            if item.category not in by_category:
                by_category[item.category] = []
            by_category[item.category].append(item)
        
        for category, items in by_category.items():
            console.print(f"\n📁 [bold cyan]{category.title()}[/bold cyan]")
            
            for item in items:
                console.print(f"  🔸 {item.name}")
                
                if item.existing_is_symlink:
                    console.print("    (existing symlink will be updated)")
                    resolutions[item] = ConflictResolution.OVERWRITE
                else:
                    choice = Prompt.ask(
                        "    Action",
                        choices=["skip", "backup", "overwrite"],
                        default="backup"
                    )
                    resolutions[item] = ConflictResolution(choice)
        
        return resolutions


class BackupManager:
    """Manages backup operations for existing files."""

    def __init__(self, config: InstallationConfig) -> None:
        """Initialize backup manager."""
        self.config = config

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a timestamped backup of an existing file."""
        if not file_path.exists():
            return None

        timestamp = int(time.time())
        backup_path = file_path.parent / f"{file_path.name}.backup-{timestamp}"
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backed up: {file_path.name} → {backup_path.name}")
            return backup_path
        except Exception as e:
            msg = f"Failed to create backup of {file_path}: {e}"
            raise RuntimeError(msg) from e


class SymlinkManager:
    """Manages individual file symlink operations."""

    def __init__(self, config: InstallationConfig) -> None:
        """Initialize symlink manager."""
        self.config = config
        self._created_links: List[Path] = []
        self._backups_created: List[Tuple[Path, Path]] = []

    def install_files(
        self, 
        items: List[InstallationItem],
        resolutions: Dict[InstallationItem, ConflictResolution]
    ) -> None:
        """Install files according to conflict resolutions."""
        backup_manager = BackupManager(self.config)
        
        # Filter items to actually install
        to_install = []
        for item in items:
            if item.conflicts:
                resolution = resolutions.get(item, ConflictResolution.SKIP)
                if resolution == ConflictResolution.SKIP:
                    continue
            to_install.append(item)
        
        if not to_install:
            console.print("ℹ️ No files to install")
            return

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing files...", total=len(to_install))

                for item in to_install:
                    self._install_single_file(item, resolutions, backup_manager)
                    progress.update(task, advance=1)

        except Exception:
            logger.error("Installation failed, rolling back changes")
            self._rollback_installation()
            raise

    def _install_single_file(
        self,
        item: InstallationItem,
        resolutions: Dict[InstallationItem, ConflictResolution],
        backup_manager: BackupManager
    ) -> None:
        """Install a single file with appropriate conflict handling."""
        # Ensure target directory exists
        item.target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle existing file
        if item.target_path.exists():
            resolution = resolutions.get(item, ConflictResolution.SKIP)
            
            if resolution == ConflictResolution.BACKUP:
                backup_path = backup_manager.create_backup(item.target_path)
                if backup_path:
                    self._backups_created.append((item.target_path, backup_path))
            elif resolution == ConflictResolution.SKIP:
                return
            
            # Remove existing file/symlink
            item.target_path.unlink()

        # Create symlink
        try:
            item.target_path.symlink_to(item.source_path)
            self._created_links.append(item.target_path)
            logger.debug(f"Linked: {item.name}")
        except OSError as e:
            msg = f"Failed to create symlink {item.target_path} → {item.source_path}: {e}"
            raise RuntimeError(msg) from e

    def _rollback_installation(self) -> None:
        """Rollback installation by removing created symlinks and restoring backups."""
        # Remove created symlinks
        for link_path in reversed(self._created_links):
            try:
                if link_path.is_symlink():
                    link_path.unlink()
                    logger.info(f"Removed symlink during rollback: {link_path}")
            except Exception as e:
                logger.warning(f"Failed to remove symlink {link_path}: {e}")
        
        # Restore backups
        for original_path, backup_path in reversed(self._backups_created):
            try:
                if backup_path.exists():
                    shutil.copy2(backup_path, original_path)
                    logger.info(f"Restored backup: {original_path}")
            except Exception as e:
                logger.warning(f"Failed to restore backup {backup_path}: {e}")


def get_repo_root() -> Path:
    """Discover repository root from script location."""
    return Path(__file__).parent.parent.parent.resolve()


@click.command()
@click.option(
    "--backup/--no-backup",
    default=True,
    help="Create backup of existing files before installation",
)
@click.option(
    "--conflict-resolution",
    type=click.Choice(["skip", "backup", "overwrite", "interactive"]),
    default="interactive",
    help="Strategy for handling file conflicts",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force installation without confirmation prompts",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging output",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be installed without making changes",
)
def main(
    backup: bool, 
    conflict_resolution: str, 
    force: bool, 
    verbose: bool, 
    dry_run: bool
) -> None:
    """Install Claude template configuration via individual file symlinks.

    This command safely installs agents, commands, and hooks by creating
    individual symlinks for each file. It detects conflicts, offers resolution
    options, and maintains backups to ensure no data is lost.

    Args:
        backup: Whether to backup existing files
        conflict_resolution: How to handle conflicts (skip/backup/overwrite/interactive)
        force: Skip confirmation prompts
        verbose: Enable detailed logging
        dry_run: Preview installation without making changes
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console.print("🚀 [bold blue]Claude Template Installation System[/bold blue]")
    if dry_run:
        console.print("🔍 [yellow]Dry run mode - no changes will be made[/yellow]")

    try:
        # Initialize configuration
        config = InstallationConfig(
            repo_root=get_repo_root(),
            backup_enabled=backup,
            force_install=force,
            conflict_resolution=ConflictResolution(conflict_resolution),
        )

        # Discover installable files
        discovery = FileDiscovery(config)
        all_items = discovery.discover_installable_files()
        
        if not all_items:
            console.print("ℹ️ No installable files found in repository")
            return

        # Analyze conflicts
        conflict_manager = ConflictManager(config)
        conflicts = conflict_manager.analyze_conflicts(all_items)
        conflict_manager.display_conflict_summary(conflicts)

        # Get user confirmation for installation
        if not force and not dry_run:
            console.print(f"\n📍 Installation Details:")
            console.print(f"  • Target directory: {config.claude_dir}")
            console.print(f"  • Repository root: {config.repo_root}")
            console.print(f"  • Backup enabled: {backup}")
            console.print(f"  • Conflict resolution: {conflict_resolution}")

            if not Confirm.ask("\nProceed with installation?"):
                console.print("❌ Installation cancelled by user")
                sys.exit(0)

        # Resolve conflicts
        resolutions = {}
        if conflicts["existing_files"] and not dry_run:
            if config.conflict_resolution == ConflictResolution.INTERACTIVE:
                resolutions = conflict_manager.resolve_conflicts_interactive(
                    conflicts["existing_files"]
                )
            else:
                # Apply consistent resolution strategy
                for item in conflicts["existing_files"]:
                    resolutions[item] = config.conflict_resolution

        if dry_run:
            console.print("\n📋 [bold]Dry Run Summary[/bold]")
            console.print(f"  • {len(conflicts['new_files'])} new files would be installed")
            console.print(f"  • {len(conflicts['existing_symlinks'])} symlinks would be updated")
            console.print(f"  • {len(conflicts['existing_files'])} conflicts require resolution")
            return

        # Install files
        symlink_manager = SymlinkManager(config)
        symlink_manager.install_files(all_items, resolutions)

        # Success message
        installed_count = len([
            item for item in all_items 
            if not item.conflicts or resolutions.get(item) != ConflictResolution.SKIP
        ])
        
        console.print(f"\n✅ [bold green]Installation completed successfully![/bold green]")
        console.print(f"  • {installed_count} files installed")
        if resolutions:
            backup_count = len([r for r in resolutions.values() if r == ConflictResolution.BACKUP])
            if backup_count:
                console.print(f"  • {backup_count} files backed up")

        console.print("\n📋 Next Steps:")
        console.print("  1. Run `make configure` to customize your setup")
        console.print("  2. Restart Claude Code to load the new configuration")
        console.print("  3. Use agents, commands, and hooks from the claude-dump repository")
        
        # Ask about statusline installation
        console.print("\n🎨 [bold yellow]Enhanced Statusline Available[/bold yellow]")
        console.print("Would you like to install the enhanced statusline with:")
        console.print("  • Model info and git status")
        console.print("  • Daily usage tracking")
        console.print("  • 5-hour window countdown")
        console.print("  • Configurable components")
        
        if not force and Confirm.ask("\nInstall enhanced statusline?", default=True):
            try:
                import subprocess
                console.print("🚀 [blue]Installing and configuring statusline...[/blue]")
                result = subprocess.run(
                    ["make", "force-install-statusline"], 
                    cwd=get_repo_root(), 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    console.print("✅ [bold green]Statusline fully configured![/bold green]")
                    console.print("\n🎉 [blue]Ready to use:[/blue]")
                    console.print("  • Statusline is automatically active in Claude Code")
                    console.print("  • No manual configuration needed")
                    console.print("  • Just restart Claude Code to see it!")
                    console.print("\n💡 [dim]Files created:[/dim]")
                    console.print("  • Settings: ~/.claude/settings.json")
                    console.print("  • Config: ~/.claude/claude_dump/statusline_config.json")
                    console.print("  • Usage data: ~/.claude/claude_dump/usage_tracking.json")
                else:
                    console.print(f"⚠️  [yellow]Statusline installation had issues:[/yellow] {result.stderr}")
                    console.print("You can try again with: make install-statusline")
            except Exception as e:
                console.print(f"⚠️  [yellow]Could not install statusline automatically:[/yellow] {e}")
                console.print("You can install it manually with: make install-statusline")
        else:
            console.print("⏭️  [yellow]Statusline installation skipped[/yellow]")
            console.print("You can install it later with: make install-statusline")

        logger.info("Claude template installation completed successfully")

    except Exception as e:
        console.print(f"❌ [bold red]Installation failed:[/bold red] {e}")
        logger.error(f"Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
