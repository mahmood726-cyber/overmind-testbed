"""Test that Overmind correctly discovers and indexes CardioOracle."""
from __future__ import annotations

from pathlib import Path

from overmind.config import AppConfig
from overmind.discovery.indexer import ProjectIndexer


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_project_type_is_browser_app(cardiooracle_project):
    # CardioOracle has index.html at root → browser_app (no pyproject.toml/requirements.txt)
    assert cardiooracle_project.project_type == "browser_app"


def test_risk_profile_is_high(cardiooracle_project):
    assert cardiooracle_project.risk_profile == "high"


def test_advanced_math_detected(cardiooracle_project):
    assert cardiooracle_project.has_advanced_math is True
    assert cardiooracle_project.advanced_math_score > 0
    assert len(cardiooracle_project.advanced_math_signals) > 0


def test_test_commands_found(cardiooracle_project):
    assert len(cardiooracle_project.test_commands) > 0
    assert any("pytest" in cmd or "test" in cmd for cmd in cardiooracle_project.test_commands)
