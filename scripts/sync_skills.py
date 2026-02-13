#!/usr/bin/env python3
"""Sync script for merging base SKILL.md files with Claude Code enhancements.

This script synchronizes skills from the mgiovani/skills upstream repository
with Claude Code-specific enhancements from the enhancements/ directory,
producing merged SKILL.md files in the skills/ directory.

Architecture:
    1. Base SKILL.md files live in skills-upstream/skills/<name>/
    2. Enhancement files live in enhancements/<name>/ENHANCEMENT.md
    3. Merged output goes to skills/<name>/SKILL.md
    4. Bundled resources (scripts/, references/, assets/) are copied from upstream
    5. SYNC.md metadata file tracks sync state with commit hash and timestamp

Usage:
    python scripts/sync_skills.py              # Sync all skills
    python scripts/sync_skills.py --status     # Show sync status
    python scripts/sync_skills.py --skill git-commit  # Sync single skill
"""

import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
import yaml
from pydantic import BaseModel, Field
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Configure rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='[%X]',
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


class SyncMetadata(BaseModel):
    """Metadata tracking sync state for a skill."""

    upstream_commit: str = Field(..., description='Git commit hash from upstream')
    sync_timestamp: str = Field(..., description='ISO 8601 timestamp of sync')
    base_skill_path: str = Field(..., description='Path to base SKILL.md')
    enhancement_path: str | None = Field(
        None, description='Path to ENHANCEMENT.md if exists'
    )
    has_enhancement: bool = Field(..., description='Whether enhancement exists')


class SkillSync:
    """Synchronize a single skill from upstream with enhancements."""

    def __init__(
        self,
        skill_name: str,
        repo_root: Path,
        upstream_dir: Path,
        enhancements_dir: Path,
        skills_dir: Path,
    ) -> None:
        """Initialize skill synchronization.

        Args:
            skill_name: Name of the skill (e.g., 'git-commit')
            repo_root: Root directory of cc-arsenal repository
            upstream_dir: Path to skills-upstream submodule
            enhancements_dir: Path to enhancements/ directory
            skills_dir: Path to skills/ output directory
        """
        self.skill_name = skill_name
        self.repo_root = repo_root
        self.upstream_dir = upstream_dir
        self.enhancements_dir = enhancements_dir
        self.skills_dir = skills_dir

        # Define paths
        self.base_skill_dir = upstream_dir / 'skills' / skill_name
        self.base_skill_file = self.base_skill_dir / 'SKILL.md'
        self.enhancement_dir = enhancements_dir / skill_name
        self.enhancement_file = self.enhancement_dir / 'ENHANCEMENT.md'
        self.output_dir = skills_dir / skill_name
        self.output_file = self.output_dir / 'SKILL.md'
        self.sync_metadata_file = self.output_dir / 'SYNC.md'

    def get_upstream_commit(self) -> str:
        """Get current commit hash of upstream submodule."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.upstream_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to get upstream commit: {e}')
            return 'unknown'

    def read_frontmatter_and_body(self, file_path: Path) -> tuple[dict[str, Any], str]:
        """Read YAML frontmatter and markdown body from a file.

        Args:
            file_path: Path to markdown file with YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)

        Raises:
            ValueError: If file doesn't have valid frontmatter
        """
        content = file_path.read_text(encoding='utf-8')

        # Check for frontmatter delimiters
        if not content.startswith('---\n'):
            msg = f'No frontmatter found in {file_path}'
            raise ValueError(msg)

        # Find end of frontmatter
        parts = content.split('\n---\n', 2)
        if len(parts) < 2:  # noqa: PLR2004
            msg = f'Malformed frontmatter in {file_path}'
            raise ValueError(msg)

        # Parse frontmatter and body
        frontmatter_str = parts[0].replace('---\n', '', 1)
        frontmatter = yaml.safe_load(frontmatter_str) or {}
        body = parts[1] if len(parts) > 1 else ''

        return frontmatter, body.strip()

    def merge_frontmatter(
        self, base: dict[str, Any], enhancement: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge frontmatter with enhancement overriding base.

        Args:
            base: Base frontmatter from upstream SKILL.md
            enhancement: Enhancement frontmatter from ENHANCEMENT.md

        Returns:
            Merged frontmatter dictionary
        """
        merged = base.copy()
        merged.update(enhancement)
        return merged

    def sync(self) -> bool:
        """Synchronize the skill: merge base + enhancement, copy resources.

        Returns:
            True if sync succeeded, False otherwise
        """
        logger.info(f'Syncing skill: {self.skill_name}')

        # Check if base skill exists
        if not self.base_skill_file.exists():
            logger.warning(f'Base skill not found: {self.base_skill_file}. Skipping.')
            return False

        # Read base SKILL.md
        try:
            base_frontmatter, base_body = self.read_frontmatter_and_body(
                self.base_skill_file
            )
        except ValueError as e:
            logger.error(f'Failed to read base skill: {e}')
            return False

        # Check for enhancement
        has_enhancement = self.enhancement_file.exists()
        if has_enhancement:
            try:
                (
                    enhancement_frontmatter,
                    enhancement_body,
                ) = self.read_frontmatter_and_body(self.enhancement_file)
            except ValueError as e:
                logger.error(f'Failed to read enhancement: {e}')
                return False
        else:
            enhancement_frontmatter = {}
            enhancement_body = ''
            logger.info(f'No enhancement found for {self.skill_name}, using base only')

        # Merge frontmatter (enhancement overrides base)
        merged_frontmatter = self.merge_frontmatter(
            base_frontmatter, enhancement_frontmatter
        )

        # Concatenate body (base + enhancement)
        if enhancement_body:
            merged_body = f'{base_body}\n\n{enhancement_body}'
        else:
            merged_body = base_body

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write merged SKILL.md
        merged_content = (
            '---\n'
            + yaml.dump(merged_frontmatter, default_flow_style=False, sort_keys=False)
            + '---\n\n'
            + merged_body
        )
        self.output_file.write_text(merged_content, encoding='utf-8')
        logger.info(f'✓ Merged SKILL.md written to {self.output_file}')

        # Copy bundled resources (scripts/, references/, assets/)
        for resource_dir in ['scripts', 'references', 'assets']:
            source_resource = self.base_skill_dir / resource_dir
            if source_resource.exists():
                target_resource = self.output_dir / resource_dir
                if target_resource.exists():
                    import shutil

                    shutil.rmtree(target_resource)
                import shutil

                shutil.copytree(source_resource, target_resource)
                logger.info(f'✓ Copied {resource_dir}/ from upstream')

        # Write SYNC.md metadata
        metadata = SyncMetadata(
            upstream_commit=self.get_upstream_commit(),
            sync_timestamp=datetime.now(UTC).isoformat(),
            base_skill_path=str(self.base_skill_file.relative_to(self.repo_root)),
            enhancement_path=(
                str(self.enhancement_file.relative_to(self.repo_root))
                if has_enhancement
                else None
            ),
            has_enhancement=has_enhancement,
        )

        sync_content = f"""# Sync Metadata

This file tracks the sync state of this skill with the upstream repository.

**Upstream Commit**: `{metadata.upstream_commit}`
**Sync Timestamp**: `{metadata.sync_timestamp}`
**Base Skill**: `{metadata.base_skill_path}`
**Enhancement**: `{metadata.enhancement_path or 'None'}`
**Has Enhancement**: `{metadata.has_enhancement}`

---

**Do not edit this file manually.** It is auto-generated by `scripts/sync_skills.py`.
"""
        self.sync_metadata_file.write_text(sync_content, encoding='utf-8')
        logger.info(f'✓ Sync metadata written to {self.sync_metadata_file}')

        return True

    def get_status(self) -> dict[str, Any]:
        """Get sync status for this skill.

        Returns:
            Dictionary with status information
        """
        status: dict[str, Any] = {
            'skill': self.skill_name,
            'base_exists': self.base_skill_file.exists(),
            'enhancement_exists': self.enhancement_file.exists(),
            'output_exists': self.output_file.exists(),
            'synced': False,
            'upstream_commit': None,
            'sync_timestamp': None,
        }

        if self.sync_metadata_file.exists():
            content = self.sync_metadata_file.read_text(encoding='utf-8')
            # Parse metadata from SYNC.md (simple regex for now)
            import re

            commit_match = re.search(r'\*\*Upstream Commit\*\*: `([^`]+)`', content)
            time_match = re.search(r'\*\*Sync Timestamp\*\*: `([^`]+)`', content)

            if commit_match and time_match:
                status['upstream_commit'] = commit_match.group(1)
                status['sync_timestamp'] = time_match.group(1)
                status['synced'] = True

        return status


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    '--status',
    is_flag=True,
    help='Show sync status for all skills',
)
@click.option(
    '--skill',
    type=str,
    help='Sync a specific skill by name (e.g., git-commit)',
)
def main(ctx: click.Context, status: bool, skill: str | None) -> None:
    """Sync skills from mgiovani/skills upstream with Claude Code enhancements."""
    # Determine repository root
    repo_root = Path(__file__).parent.parent.resolve()
    upstream_dir = repo_root / 'skills-upstream'
    enhancements_dir = repo_root / 'enhancements'
    skills_dir = repo_root / 'skills'

    # Validate directories exist
    if not upstream_dir.exists():
        console.print('[red]❌ skills-upstream/ not found. Initialize submodule:[/red]')
        console.print('   git submodule update --init --recursive')
        sys.exit(1)

    if not enhancements_dir.exists():
        console.print(
            '[yellow]⚠ enhancements/ not found. No enhancements available.[/yellow]'
        )

    # Show status
    if status:
        show_status(repo_root, upstream_dir, enhancements_dir, skills_dir)
        return

    # Sync specific skill
    if skill:
        syncer = SkillSync(skill, repo_root, upstream_dir, enhancements_dir, skills_dir)
        success = syncer.sync()
        sys.exit(0 if success else 1)

    # Default: sync all skills
    sync_all_skills(repo_root, upstream_dir, enhancements_dir, skills_dir)


def sync_all_skills(
    repo_root: Path,
    upstream_dir: Path,
    enhancements_dir: Path,
    skills_dir: Path,
) -> None:
    """Sync all skills from upstream."""
    upstream_skills_dir = upstream_dir / 'skills'

    if not upstream_skills_dir.exists():
        console.print(
            f'[red]❌ No skills found in {upstream_skills_dir}. '
            'Repository may not be initialized.[/red]'
        )
        sys.exit(1)

    # Discover all skills in upstream
    skill_names = [
        d.name
        for d in upstream_skills_dir.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]

    if not skill_names:
        console.print('[yellow]⚠ No skills found in upstream repository.[/yellow]')
        sys.exit(0)

    console.print(f'[blue]Found {len(skill_names)} skills in upstream[/blue]')

    # Sync each skill with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        console=console,
    ) as progress:
        task = progress.add_task('Syncing skills...', total=len(skill_names))

        successes = 0
        failures = 0

        for skill_name in sorted(skill_names):
            progress.update(task, description=f'Syncing {skill_name}...')
            syncer = SkillSync(
                skill_name, repo_root, upstream_dir, enhancements_dir, skills_dir
            )
            if syncer.sync():
                successes += 1
            else:
                failures += 1
            progress.advance(task)

    console.print(f'\n[green]✓ Successfully synced {successes} skills[/green]')
    if failures:
        console.print(f'[red]✗ Failed to sync {failures} skills[/red]')


def show_status(
    repo_root: Path,
    upstream_dir: Path,
    enhancements_dir: Path,
    skills_dir: Path,
) -> None:
    """Show sync status for all skills."""
    upstream_skills_dir = upstream_dir / 'skills'

    if not upstream_skills_dir.exists():
        console.print(f'[red]❌ No skills found in {upstream_skills_dir}[/red]')
        sys.exit(1)

    # Discover all skills
    skill_names = [
        d.name
        for d in upstream_skills_dir.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]

    if not skill_names:
        console.print('[yellow]⚠ No skills found in upstream repository.[/yellow]')
        sys.exit(0)

    # Create status table
    table = Table(title='Skill Sync Status')
    table.add_column('Skill', style='cyan')
    table.add_column('Base', justify='center')
    table.add_column('Enhancement', justify='center')
    table.add_column('Synced', justify='center')
    table.add_column('Last Sync', style='dim')

    for skill_name in sorted(skill_names):
        syncer = SkillSync(
            skill_name, repo_root, upstream_dir, enhancements_dir, skills_dir
        )
        status = syncer.get_status()

        base_icon = '✓' if status['base_exists'] else '✗'
        enh_icon = '✓' if status['enhancement_exists'] else '-'
        synced_icon = '✓' if status['synced'] else '✗'

        last_sync = status.get('sync_timestamp', 'Never')
        if last_sync and last_sync != 'Never':
            # Format ISO timestamp to human-readable
            try:
                dt = datetime.fromisoformat(last_sync)
                last_sync = dt.strftime('%Y-%m-%d %H:%M')
            except (ValueError, AttributeError):
                pass

        table.add_row(
            skill_name,
            base_icon,
            enh_icon,
            synced_icon,
            last_sync,
        )

    console.print(table)


if __name__ == '__main__':
    main()
