"""Test Q-learning routing and scheduler assignment."""
from __future__ import annotations

from overmind.runners.q_router import QRouter
from overmind.core.scheduler import Scheduler
from overmind.storage.models import ProjectRecord, RunnerRecord, TaskRecord


def _minimal_project(project_id: str) -> ProjectRecord:
    """Return a minimal ProjectRecord so the scheduler does not skip the task."""
    return ProjectRecord(
        project_id=project_id,
        name="test-project",
        root_path="C:/test",
    )


def test_q_score_updates_on_win(fresh_db):
    router = QRouter(fresh_db)
    assert router.score("claude", "verification") == 0.5
    router.record("claude", "verification", True)
    assert router.score("claude", "verification") > 0.5


def test_q_score_updates_on_loss(fresh_db):
    router = QRouter(fresh_db)
    router.record("codex", "implementation", False)
    assert router.score("codex", "implementation") < 0.5


def test_laplace_smoothing_cold_start(fresh_db):
    router = QRouter(fresh_db)
    router.record("gemini", "critique", True)
    q = router.score("gemini", "critique")
    assert abs(q - 2 / 3) < 0.01


def test_scheduler_prefers_claude_for_high_risk(fresh_db, policies):
    router = QRouter(fresh_db)
    scheduler = Scheduler(policies, q_router=router)
    claude = RunnerRecord(
        runner_id="claude_r", runner_type="claude", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    codex = RunnerRecord(
        runner_id="codex_r", runner_type="codex", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    task = TaskRecord(
        task_id="t1", project_id="test", title="Fix bug",
        task_type="focused_fix", source="test", priority=0.9,
        risk="high", expected_runtime_min=5, expected_context_cost="medium",
        required_verification=["relevant_tests"],
    )
    assignments = scheduler.assign(
        [task], [claude, codex], {"test": _minimal_project("test")},
        capacity=1, prompt_builder=lambda p, t: "test prompt",
    )
    assert len(assignments) == 1
    assert assignments[0].runner_id == "claude_r"


def test_scheduler_prefers_codex_for_tests(fresh_db, policies):
    router = QRouter(fresh_db)
    scheduler = Scheduler(policies, q_router=router)
    claude = RunnerRecord(
        runner_id="claude_r", runner_type="claude", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    codex = RunnerRecord(
        runner_id="codex_r", runner_type="codex", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    task = TaskRecord(
        task_id="t2", project_id="test", title="Run tests",
        task_type="verification", source="test", priority=0.9,
        risk="medium", expected_runtime_min=5, expected_context_cost="low",
        required_verification=["relevant_tests"],
    )
    assignments = scheduler.assign(
        [task], [claude, codex], {"test": _minimal_project("test")},
        capacity=1, prompt_builder=lambda p, t: "test prompt",
    )
    assert len(assignments) == 1
    assert assignments[0].runner_id == "codex_r"
