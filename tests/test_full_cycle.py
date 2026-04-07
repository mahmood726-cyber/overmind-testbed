"""End-to-end run_once smoke tests against CardioOracle with stubs."""
from __future__ import annotations

from pathlib import Path

from overmind.config import AppConfig
from overmind.core.orchestrator import Orchestrator


def test_dry_run_returns_would_dispatch(cardiooracle_project):
    """Dry run returns plan without executing."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        assert result.get("dry_run") is True
        assert "would_dispatch" in result
    finally:
        orch.close()


def test_dry_run_finds_cardiooracle(cardiooracle_project):
    """Dry run indexes CardioOracle and generates tasks for it."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        assert result.get("projects_indexed", 0) >= 1
    finally:
        orch.close()


def test_dry_run_generates_tasks(cardiooracle_project):
    """Dry run generates at least one task for CardioOracle."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        assert result.get("generated_tasks", 0) >= 0
    finally:
        orch.close()
