"""Test the three witness types: TestSuite, Smoke, Numerical."""
from __future__ import annotations

import json
from pathlib import Path

from overmind.verification.witnesses import (
    TestSuiteWitness,
    SmokeWitness,
    NumericalWitness,
)


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_test_suite_witness_passes_real_pytest(tmp_path):
    witness = TestSuiteWitness(timeout=120)
    result = witness.run(
        command="python -m pytest tests/test_curation.py -q",
        cwd=str(CARDIOORACLE_ROOT),
    )
    assert result.witness_type == "test_suite"
    assert result.verdict == "PASS"
    assert result.exit_code == 0


def test_test_suite_witness_detects_failure(tmp_path):
    witness = TestSuiteWitness(timeout=30)
    result = witness.run(
        command='python -c "raise SystemExit(1)"',
        cwd=str(tmp_path),
    )
    assert result.verdict == "FAIL"
    assert result.exit_code == 1


def test_smoke_witness_passes_clean_modules(tmp_path):
    (tmp_path / "good_module.py").write_text("X = 42\n", encoding="utf-8")
    witness = SmokeWitness(timeout=10)
    result = witness.run(modules=["good_module"], cwd=str(tmp_path))
    assert result.verdict == "PASS"


def test_smoke_witness_catches_import_error(tmp_path):
    (tmp_path / "bad_module.py").write_text("import nonexistent_package_xyz\n", encoding="utf-8")
    witness = SmokeWitness(timeout=10)
    result = witness.run(modules=["bad_module"], cwd=str(tmp_path))
    assert result.verdict == "FAIL"


def test_numerical_witness_passes_matching_snapshot(tmp_path):
    baseline = {
        "command": 'python -c "import json; print(json.dumps(dict(tau2=0.04, effect=-0.23)))"',
        "values": {"tau2": 0.04, "effect": -0.23},
        "tolerance": 1e-4,
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    witness = NumericalWitness(timeout=30)
    result = witness.run(baseline_path=str(baseline_path), cwd=str(tmp_path))
    assert result.verdict == "PASS"


def test_numerical_witness_detects_drift(tmp_path):
    baseline = {
        "command": 'python -c "import json; print(json.dumps(dict(tau2=0.99, effect=-0.23)))"',
        "values": {"tau2": 0.04, "effect": -0.23},
        "tolerance": 1e-6,
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    witness = NumericalWitness(timeout=30)
    result = witness.run(baseline_path=str(baseline_path), cwd=str(tmp_path))
    assert result.verdict == "FAIL"
