"""Test Overmind's verification engine against CardioOracle's real test suite."""
from __future__ import annotations

from pathlib import Path

from overmind.storage.models import ProjectRecord, TaskRecord
from overmind.verification.verifier import VerificationEngine


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_real_pytest_passes(tmp_path, cardiooracle_project):
    """Run CardioOracle's actual curation tests via verify_command."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=120)
    task = TaskRecord(
        task_id="v1", project_id=cardiooracle_project.project_id,
        title="Verify curation", task_type="verification", source="test",
        priority=0.9, risk="high", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command="python -m pytest tests/test_curation.py -v --tb=short",
    )
    result = engine.run(task, cardiooracle_project)
    assert result.success is True
    assert len(result.completed_checks) > 0


def test_verification_parses_details(tmp_path, cardiooracle_project):
    """Verification details include exit code and command."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=120)
    task = TaskRecord(
        task_id="v2", project_id=cardiooracle_project.project_id,
        title="Verify details", task_type="verification", source="test",
        priority=0.9, risk="high", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command="python -m pytest tests/test_curation.py -v --tb=short",
    )
    result = engine.run(task, cardiooracle_project)
    assert any("exit=0" in d for d in result.details)


def test_failing_command_returns_failure(tmp_path, cardiooracle_project):
    """A verify_command that fails returns success=False."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=30)
    task = TaskRecord(
        task_id="v3", project_id=cardiooracle_project.project_id,
        title="Bad verify", task_type="verification", source="test",
        priority=0.5, risk="low", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command='python -c "raise SystemExit(1)"',
    )
    # Override test_commands on the project so the planner uses our failing command
    from dataclasses import replace
    failing_project = replace(
        cardiooracle_project,
        test_commands=['python -c "raise SystemExit(1)"'],
    )
    result = engine.run(task, failing_project)
    assert result.success is False
