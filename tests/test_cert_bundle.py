"""Test CertBundle hashing and serialization."""
from __future__ import annotations

import json

from overmind.verification.scope_lock import ScopeLock, WitnessResult
from overmind.verification.cert_bundle import CertBundle


def _lock():
    return ScopeLock(
        project_id="test", project_path="C:\\test",
        risk_profile="high", witness_count=2,
        test_command="pytest", smoke_modules=("engine",),
        baseline_path=None, expected_outcome="pass",
        source_hash="abc123", created_at="2026-04-07T00:00:00Z",
    )


def _witness(verdict="PASS"):
    return WitnessResult(
        witness_type="test_suite", verdict=verdict,
        exit_code=0, stdout="ok", stderr="", elapsed=1.0,
    )


def test_bundle_hash_is_deterministic():
    b1 = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[_witness()], verdict="CERTIFIED",
        arbitration_reason="1/1 PASS", timestamp="2026-04-07T03:00:00Z",
    )
    b2 = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[_witness()], verdict="CERTIFIED",
        arbitration_reason="1/1 PASS", timestamp="2026-04-07T03:00:00Z",
    )
    assert b1.bundle_hash == b2.bundle_hash
    assert len(b1.bundle_hash) == 16


def test_bundle_hash_changes_on_different_verdict():
    b1 = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[_witness()], verdict="CERTIFIED",
        arbitration_reason="ok", timestamp="2026-04-07T03:00:00Z",
    )
    b2 = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[_witness("FAIL")], verdict="FAIL",
        arbitration_reason="broken", timestamp="2026-04-07T03:00:00Z",
    )
    assert b1.bundle_hash != b2.bundle_hash


def test_bundle_serializes_to_json():
    bundle = CertBundle(
        project_id="test", scope_lock=_lock(),
        witness_results=[_witness()], verdict="CERTIFIED",
        arbitration_reason="all pass", timestamp="2026-04-07T03:00:00Z",
    )
    d = bundle.to_dict()
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["verdict"] == "CERTIFIED"
    assert parsed["bundle_hash"] == bundle.bundle_hash
    assert parsed["scope_lock"]["project_id"] == "test"
