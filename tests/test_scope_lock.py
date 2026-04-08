"""Test ScopeLock immutability, source_hash, and tier logic."""
from __future__ import annotations

from overmind.verification.scope_lock import ScopeLock, WitnessResult, compute_tier


def test_scope_lock_is_frozen():
    lock = ScopeLock(
        project_id="test_proj", project_path="C:\\test",
        risk_profile="high", witness_count=3,
        test_command="python -m pytest tests/ -q",
        smoke_modules=("engine", "utils"),
        baseline_path=None, expected_outcome="pass",
        source_hash="abc123", created_at="2026-04-07T00:00:00Z",
    )
    try:
        lock.project_id = "changed"
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_compute_tier_high_math_gets_3():
    assert compute_tier("high", 20) == 3
    assert compute_tier("high", 10) == 3
    assert compute_tier("high", 9) == 2
    assert compute_tier("medium_high", 20) == 2
    assert compute_tier("medium", 5) == 1


def test_witness_result_fields():
    result = WitnessResult(
        witness_type="test_suite", verdict="PASS",
        exit_code=0, stdout="5 passed", stderr="", elapsed=3.2,
    )
    assert result.verdict == "PASS"
    assert result.elapsed == 3.2
