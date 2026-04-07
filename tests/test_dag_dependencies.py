"""Test DAG task dependencies and unblocking."""
from __future__ import annotations

from overmind.tasks.task_queue import TaskQueue
from overmind.storage.models import TaskRecord


def _task(tid, status="QUEUED", blocked_by=None):
    return TaskRecord(
        task_id=tid, project_id="test", title=f"Task {tid}",
        task_type="verification", source="test", priority=0.8,
        risk="medium", expected_runtime_min=1, expected_context_cost="low",
        required_verification=["build"], status=status,
        blocked_by=blocked_by or [],
    )


def test_build_task_is_queued(fresh_db):
    tq = TaskQueue(fresh_db)
    tq.upsert([_task("build_1")])
    queued_ids = {t.task_id for t in tq.queued()}
    assert "build_1" in queued_ids


def test_blocked_task_not_in_queued(fresh_db):
    tq = TaskQueue(fresh_db)
    tq.upsert([_task("build_2"), _task("test_2", blocked_by=["build_2"])])
    queued_ids = {t.task_id for t in tq.queued()}
    assert "build_2" in queued_ids
    assert "test_2" not in queued_ids


def test_completing_blocker_unblocks_dependent(fresh_db):
    tq = TaskQueue(fresh_db)
    tq.upsert([
        _task("build_3"),
        _task("test_3", blocked_by=["build_3"]),
    ])
    tq.transition("build_3", "ASSIGNED")
    tq.transition("build_3", "RUNNING")
    tq.transition("build_3", "VERIFYING")
    tq.transition("build_3", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "test_3" in queued_ids


def test_multi_dependency_all_must_complete(fresh_db):
    tq = TaskQueue(fresh_db)
    tq.upsert([
        _task("dep_a"),
        _task("dep_b"),
        _task("final", blocked_by=["dep_a", "dep_b"]),
    ])

    tq.transition("dep_a", "ASSIGNED")
    tq.transition("dep_a", "RUNNING")
    tq.transition("dep_a", "VERIFYING")
    tq.transition("dep_a", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "final" not in queued_ids

    tq.transition("dep_b", "ASSIGNED")
    tq.transition("dep_b", "RUNNING")
    tq.transition("dep_b", "VERIFYING")
    tq.transition("dep_b", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "final" in queued_ids
