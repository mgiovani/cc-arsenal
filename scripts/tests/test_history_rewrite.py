"""Tests for the oss-launch history rewrite script (needs git and git-filter-repo)."""

# ruff: noqa: S105, S607

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / 'skills'
    / 'oss-launch'
    / 'scripts'
    / 'history_rewrite.sh'
)
SECRET = 'sk_live_TESTSECRET123'

pytestmark = pytest.mark.skipif(
    shutil.which('git-filter-repo') is None, reason='git-filter-repo not installed'
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ['git', *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / 'proj'
    path.mkdir()
    _git(path, 'init', '-q')
    _git(path, 'config', 'user.email', 't@example.com')
    _git(path, 'config', 'user.name', 'T')
    (path / 'keep.txt').write_text('keep\n')
    (path / 'creds.json').write_text('{}\n')
    (path / 'conf.env').write_text(f'KEY={SECRET}\n')
    _git(path, 'add', '.')
    _git(path, 'commit', '-q', '-m', 'init')
    return path


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, 'HISTORY_REWRITE_SKIP_VISIBILITY': '1'}
    return subprocess.run(
        ['sh', str(SCRIPT), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_rewrite_removes_paths_and_strings(repo: Path, tmp_path: Path) -> None:
    paths = tmp_path / 'paths.txt'
    paths.write_text('creds.json\n')
    repl = tmp_path / 'repl.txt'
    repl.write_text(f'{SECRET}==>REDACTED\n')

    result = _run(repo, '--paths', str(paths), '--replace', str(repl))

    assert result.returncode == 0, result.stderr
    assert 'Removed paths still present in history: 0' in result.stdout
    assert 'Lines still matching the replace patterns in history: 0' in result.stdout
    assert 'git push --force-with-lease origin --all' in result.stdout
    assert SECRET not in result.stdout + result.stderr
    assert 'creds.json' not in _git(repo, 'log', '--all', '--name-only')
    assert SECRET not in _git(repo, 'log', '--all', '-p')
    assert list(tmp_path.glob('proj-pre-rewrite-backup-*.git'))


def test_refuses_dirty_tree(repo: Path, tmp_path: Path) -> None:
    paths = tmp_path / 'paths.txt'
    paths.write_text('creds.json\n')
    (repo / 'keep.txt').write_text('dirty\n')

    result = _run(repo, '--paths', str(paths))

    assert result.returncode != 0
    assert 'not clean' in result.stderr
    assert not list(tmp_path.glob('proj-pre-rewrite-backup-*.git'))


def test_refuses_without_visibility_bypass(repo: Path, tmp_path: Path) -> None:
    paths = tmp_path / 'paths.txt'
    paths.write_text('creds.json\n')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    gh = bin_dir / 'gh'
    gh.write_text('#!/bin/sh\necho PUBLIC\n')
    gh.chmod(0o755)
    env = {**os.environ, 'PATH': f'{bin_dir}{os.pathsep}{os.environ["PATH"]}'}
    env.pop('HISTORY_REWRITE_SKIP_VISIBILITY', None)

    result = subprocess.run(
        ['sh', str(SCRIPT), '--paths', str(paths)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert 'only a private repo' in result.stderr
