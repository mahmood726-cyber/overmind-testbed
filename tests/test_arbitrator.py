"""Test arbitrator fail-closed logic."""
from __future__ import annotations

from overmind.verification.scope_lock import WitnessResult
from overmind.verification.cert_bundle import Arbitrator


def _witness(wtype, verdict):
    return WitnessResult(
        witness_type=wtype, verdict=verdict,
        exit_code=0 if verdict == "PASS" else 1,
        stdout="", stderr="", elapsed=1.0,
    )


def test_all_pass_is_certified():
    arb = Arbitrator()
    results = [_witness("test_suite", "PASS"), _witness("smoke", "PASS"), _witness("numerical", "PASS")]
    verdict, reason = arb.arbitrate(results)
    assert verdict == "CERTIFIED"


def test_all_fail_is_fail():
    arb = Arbitrator()
    results = [_witness("test_suite", "FAIL"), _witness("smoke", "FAIL")]
    verdict, reason = arb.arbitrate(results)
    assert verdict == "FAIL"


def test_disagreement_is_reject():
    arb = Arbitrator()
    results = [_witness("test_suite", "PASS"), _witness("smoke", "FAIL")]
    verdict, reason = arb.arbitrate(results)
    assert verdict == "REJECT"


def test_numerical_drift_is_reject():
    arb = Arbitrator()
    results = [_witness("test_suite", "PASS"), _witness("smoke", "PASS"), _witness("numerical", "FAIL")]
    verdict, reason = arb.arbitrate(results)
    assert verdict == "REJECT"
    assert "disagree" in reason.lower()


def test_skip_witnesses_not_counted():
    arb = Arbitrator()
    results = [_witness("test_suite", "PASS"), _witness("smoke", "SKIP")]
    verdict, reason = arb.arbitrate(results)
    assert verdict == "PASS"
