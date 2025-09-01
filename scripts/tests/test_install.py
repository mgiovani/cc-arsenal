"""Unit tests for the installation script."""

import tempfile
import unittest
from pathlib import Path

import pytest
from setup.install import (
    BackupManager,
    ConflictManager,
    ConflictResolution,
    FileDiscovery,
    InstallationConfig,
    InstallationItem,
    SymlinkManager,
)


class TestInstallationConfig(unittest.TestCase):
    """Test InstallationConfig validation and setup."""

    def test_config_creation(self) -> None:
        """Test basic configuration creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            config = InstallationConfig(repo_root=repo_root)

            assert config.repo_root == repo_root
            assert config.conflict_resolution == ConflictResolution.INTERACTIVE
            assert config.backup_enabled
            assert not config.force_install

    def test_nonexistent_repo_root_validation(self) -> None:
        """Test that nonexistent repo root raises validation error."""
        with pytest.raises(ValueError, match='Repository root does not exist'):
            InstallationConfig(repo_root=Path('/nonexistent/path'))

    def test_claude_dir_expansion(self) -> None:
        """Test that claude_dir is properly expanded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            config = InstallationConfig(repo_root=repo_root, claude_dir=Path('~/.claude'))

            assert config.claude_dir.is_absolute()
            assert '.claude' in str(config.claude_dir)


class TestInstallationItem(unittest.TestCase):
    """Test InstallationItem model."""

    def test_item_creation(self) -> None:
        """Test basic item creation."""
        item = InstallationItem(
            source_path=Path('/repo/agents/dev.md'),
            target_path=Path('/home/.claude/agents/dev.md'),
            category='agents',
            name='dev.md',
        )

        assert item.category == 'agents'
        assert item.name == 'dev.md'
        assert not item.conflicts
        assert not item.existing_is_symlink


class TestFileDiscovery(unittest.TestCase):
    """Test file discovery functionality."""

    def setUp(self) -> None:
        """Set up test directory structure."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

        # Create test structure
        (self.repo_root / 'agents' / 'development').mkdir(parents=True)
        (self.repo_root / 'commands' / 'security').mkdir(parents=True)
        (self.repo_root / 'hooks' / 'security').mkdir(parents=True)

        # Create test files
        (self.repo_root / 'agents' / 'development' / 'test-agent.md').write_text(
            '# Test Agent'
        )
        (self.repo_root / 'commands' / 'security' / 'test-command.md').write_text(
            '# Test Command'
        )
        (self.repo_root / 'hooks' / 'security' / 'test-hook.py').write_text('# Test Hook')

        # Create non-matching files (should be ignored)
        (self.repo_root / 'agents' / 'development' / 'readme.txt').write_text(
            'Not included'
        )

        # Use temporary claude directory for testing
        self.claude_dir = Path(self.temp_dir.name) / 'claude'
        self.config = InstallationConfig(
            repo_root=self.repo_root, claude_dir=self.claude_dir
        )

    def tearDown(self) -> None:
        """Clean up test directory."""
        self.temp_dir.cleanup()

    def test_discover_all_files(self) -> None:
        """Test discovering all installable files."""
        discovery = FileDiscovery(self.config)
        items = discovery.discover_installable_files()

        # Should find 3 files (.md and .py files only)
        expected_file_count = 3
        assert len(items) == expected_file_count

        # Check categories
        categories = {item.category for item in items}
        assert categories == {'agents', 'commands', 'hooks'}

        # Check file extensions
        extensions = {item.source_path.suffix for item in items}
        assert extensions == {'.md', '.py'}

    def test_conflict_detection(self) -> None:
        """Test conflict detection when target files exist."""
        # Create existing files
        claude_dir = self.config.claude_dir
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / 'agents' / 'development').mkdir(parents=True, exist_ok=True)

        existing_file = claude_dir / 'agents' / 'development' / 'test-agent.md'
        existing_file.write_text('Existing content')

        discovery = FileDiscovery(self.config)
        items = discovery.discover_installable_files()

        # Find the conflicting item
        conflicted_items = [item for item in items if item.conflicts]
        assert len(conflicted_items) == 1
        assert conflicted_items[0].name == 'development/test-agent.md'
        assert not conflicted_items[0].existing_is_symlink

    def test_symlink_detection(self) -> None:
        """Test detection of existing symlinks."""
        # Create symlink
        claude_dir = self.config.claude_dir
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / 'agents' / 'development').mkdir(parents=True, exist_ok=True)

        existing_symlink = claude_dir / 'agents' / 'development' / 'test-agent.md'
        existing_symlink.symlink_to(
            self.repo_root / 'agents' / 'development' / 'test-agent.md'
        )

        discovery = FileDiscovery(self.config)
        items = discovery.discover_installable_files()

        # Find the symlink item
        symlink_items = [item for item in items if item.existing_is_symlink]
        assert len(symlink_items) == 1
        assert symlink_items[0].conflicts


class TestConflictManager(unittest.TestCase):
    """Test conflict analysis and resolution."""

    def setUp(self) -> None:
        """Set up test configuration."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = InstallationConfig(repo_root=Path(self.temp_dir.name))

    def tearDown(self) -> None:
        """Clean up test directory."""
        self.temp_dir.cleanup()

    def test_analyze_conflicts(self) -> None:
        """Test conflict categorization."""
        # Create test items
        items = [
            InstallationItem(
                source_path=Path('/repo/new.md'),
                target_path=Path('/claude/new.md'),
                category='agents',
                name='new.md',
                conflicts=False,
            ),
            InstallationItem(
                source_path=Path('/repo/existing.md'),
                target_path=Path('/claude/existing.md'),
                category='agents',
                name='existing.md',
                conflicts=True,
                existing_is_symlink=False,
            ),
            InstallationItem(
                source_path=Path('/repo/symlink.md'),
                target_path=Path('/claude/symlink.md'),
                category='agents',
                name='symlink.md',
                conflicts=True,
                existing_is_symlink=True,
            ),
        ]

        conflict_manager = ConflictManager(self.config)
        conflicts = conflict_manager.analyze_conflicts(items)

        assert len(conflicts['new_files']) == 1
        assert len(conflicts['existing_files']) == 1
        assert len(conflicts['existing_symlinks']) == 1


class TestBackupManager(unittest.TestCase):
    """Test backup functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = InstallationConfig(repo_root=Path(self.temp_dir.name))
        self.backup_manager = BackupManager(self.config)

    def tearDown(self) -> None:
        """Clean up test directory."""
        self.temp_dir.cleanup()

    def test_create_backup_success(self) -> None:
        """Test successful backup creation."""
        # Create test file
        test_file = Path(self.temp_dir.name) / 'test.md'
        test_file.write_text('Original content')

        backup_path = self.backup_manager.create_backup(test_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert 'backup-' in backup_path.name
        assert backup_path.read_text() == 'Original content'

    def test_create_backup_nonexistent(self) -> None:
        """Test backup of nonexistent file returns None."""
        nonexistent = Path(self.temp_dir.name) / 'nonexistent.md'
        backup_path = self.backup_manager.create_backup(nonexistent)

        assert backup_path is None


class TestSymlinkManager(unittest.TestCase):
    """Test symlink management functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name) / 'repo'
        self.claude_dir = Path(self.temp_dir.name) / 'claude'

        self.repo_root.mkdir()
        self.claude_dir.mkdir()

        # Create source file
        self.source_file = self.repo_root / 'test.md'
        self.source_file.write_text('Source content')

        self.config = InstallationConfig(
            repo_root=self.repo_root, claude_dir=self.claude_dir
        )
        self.symlink_manager = SymlinkManager(self.config)

    def tearDown(self) -> None:
        """Clean up test directory."""
        self.temp_dir.cleanup()

    def test_install_new_file(self) -> None:
        """Test installing a new file without conflicts."""
        target_path = self.claude_dir / 'test.md'
        item = InstallationItem(
            source_path=self.source_file,
            target_path=target_path,
            category='test',
            name='test.md',
        )

        self.symlink_manager.install_files([item], {})

        assert target_path.is_symlink()
        assert target_path.resolve() == self.source_file.resolve()

    def test_install_with_backup_resolution(self) -> None:
        """Test installing with backup conflict resolution."""
        target_path = self.claude_dir / 'test.md'
        target_path.write_text('Existing content')

        item = InstallationItem(
            source_path=self.source_file,
            target_path=target_path,
            category='test',
            name='test.md',
            conflicts=True,
        )

        resolutions = {item: ConflictResolution.BACKUP}
        self.symlink_manager.install_files([item], resolutions)

        # Should be symlink now
        assert target_path.is_symlink()

        # Backup should exist
        backup_files = list(target_path.parent.glob('test.md.backup-*'))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == 'Existing content'

    def test_install_with_skip_resolution(self) -> None:
        """Test installing with skip conflict resolution."""
        target_path = self.claude_dir / 'test.md'
        target_path.write_text('Existing content')

        item = InstallationItem(
            source_path=self.source_file,
            target_path=target_path,
            category='test',
            name='test.md',
            conflicts=True,
        )

        resolutions = {item: ConflictResolution.SKIP}
        self.symlink_manager.install_files([item], resolutions)

        # Should still be original file
        assert not target_path.is_symlink()
        assert target_path.read_text() == 'Existing content'


if __name__ == '__main__':
    unittest.main()
