"""Test Judge agent failure diagnosis."""
from __future__ import annotations

from overmind.verification.scope_lock import ScopeLock, WitnessResult
from overmind.verification.cert_bundle import CertBundle
from overmind.diagnosis.judge import Judge, Diagnosis


def _lock():
    return ScopeLock(
        project_id="test", project_path="C:\\test",
        risk_profile="high", witness_count=2,
        test_command="pytest", smoke_modules=(),
        baseline_path=None, expected_outcome="pass",
        source_hash="abc", created_at="2026-04-07T00:00:00Z",
    )


def _bundle(w1_verdict="PASS", w1_stderr="", w1_stdout="", w2_verdict="FAIL", w2_stderr="", w2_stdout="", verdict="REJECT"):
    w1 = WitnessResult("test_suite", w1_verdict, 0 if w1_verdict == "PASS" else 1, w1_stdout, w1_stderr, 1.0)
    w2 = WitnessResult("smoke", w2_verdict, 0 if w2_verdict == "PASS" else 1, w2_stdout, w2_stderr, 0.5)
    return CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[w1, w2], verdict=verdict,
        arbitration_reason="test", timestamp="2026-04-07T03:00:00Z",
    )


def test_dependency_rot_detected():
    judge = Judge()
    bundle = _bundle(w2_stderr="ModuleNotFoundError: No module named 'scipy.stats'")
    diag = judge.diagnose(bundle)
    assert diag is not None
    assert diag.failure_type == "DEPENDENCY_ROT"
    assert diag.confidence >= 0.8
    assert "scipy" in diag.recommended_action


def test_numerical_drift_detected():
    judge = Judge()
    w1 = WitnessResult("test_suite", "PASS", 0, "ok", "", 1.0)
    w3 = WitnessResult("numerical", "FAIL", 0, "", "Numerical drift: tau2: 0.04 -> 0.039 (delta=1.00e-03, tol=1e-06)", 0.5)
    bundle = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[w1, w3], verdict="REJECT",
        arbitration_reason="disagree", timestamp="2026-04-07T03:00:00Z",
    )
    diag = judge.diagnose(bundle)
    assert diag is not None
    assert diag.failure_type == "NUMERICAL_DRIFT"


def test_timeout_detected():
    judge = Judge()
    w1 = WitnessResult("test_suite", "FAIL", -1, "", "Timed out after 120s", 120.0)
    bundle = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[w1], verdict="FAIL",
        arbitration_reason="all fail", timestamp="2026-04-07T03:00:00Z",
    )
    diag = judge.diagnose(bundle)
    assert diag is not None
    assert diag.failure_type == "TIMEOUT"


def test_test_failure_detected():
    judge = Judge()
    w1 = WitnessResult("test_suite", "FAIL", 1, "3 failed, 27 passed", "", 5.0)
    bundle = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[w1], verdict="FAIL",
        arbitration_reason="all fail", timestamp="2026-04-07T03:00:00Z",
    )
    diag = judge.diagnose(bundle)
    assert diag is not None
    assert diag.failure_type == "TEST_FAILURE"


def test_flaky_detected():
    judge = Judge()
    bundle = _bundle(w2_stderr="some random error")
    history = ["CERTIFIED", "FAIL", "CERTIFIED"]
    diag = judge.diagnose_with_history(bundle, history)
    assert diag is not None
    assert diag.failure_type == "FLAKY"
    assert diag.confidence == 0.7


def test_unknown_fallback():
    judge = Judge()
    bundle = _bundle(w2_stderr="something completely unexpected happened")
    diag = judge.diagnose(bundle)
    assert diag is not None
    assert diag.failure_type == "UNKNOWN"
    assert diag.confidence == 0.3


def test_certified_returns_none():
    judge = Judge()
    w1 = WitnessResult("test_suite", "PASS", 0, "ok", "", 1.0)
    w2 = WitnessResult("smoke", "PASS", 0, "ok", "", 0.5)
    bundle = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[w1, w2], verdict="CERTIFIED",
        arbitration_reason="2/2 agree", timestamp="2026-04-07T03:00:00Z",
    )
    diag = judge.diagnose(bundle)
    assert diag is None
