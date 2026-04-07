"""Test git worktree isolation for CardioOracle."""
from __future__ import annotations

from pathlib import Path

from overmind.isolation.worktree_manager import WorktreeManager


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_non_git_returns_none(tmp_path):
    """Non-git directory returns None (no worktree created)."""
    wt = WorktreeManager(tmp_path / "worktrees")
    result = wt.create(tmp_path, "test_task")
    assert result is None


def test_needs_isolation_detects_concurrent(tmp_path):
    """If project root is in active_project_roots, isolation is needed."""
    wt = WorktreeManager(tmp_path / "worktrees")
    assert wt.needs_isolation(
        CARDIOORACLE_ROOT,
        {str(CARDIOORACLE_ROOT)},
    ) is True


def test_no_isolation_when_not_concurrent(tmp_path):
    """If project root is NOT in active set, isolation is not needed."""
    wt = WorktreeManager(tmp_path / "worktrees")
    assert wt.needs_isolation(
        CARDIOORACLE_ROOT,
        {"C:\\Models\\OtherProject"},
    ) is False
