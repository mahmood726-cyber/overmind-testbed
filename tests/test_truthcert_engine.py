"""Test TruthCertEngine orchestration: tier selection, full pipeline, fail-closed."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from overmind.storage.models import ProjectRecord
from overmind.verification.truthcert_engine import TruthCertEngine
from overmind.verification.scope_lock import WitnessResult


def _project(risk="high", math_score=20, test_cmds=None):
    return ProjectRecord(
        project_id="test_proj", name="TestProject",
        root_path="C:\\test", risk_profile=risk,
        has_advanced_math=math_score > 0,
        advanced_math_score=math_score,
        test_commands=test_cmds or ["python -m pytest tests/ -q"],
    )


def test_tier_3_runs_three_witnesses(tmp_path):
    engine = TruthCertEngine(baselines_dir=tmp_path)
    project = _project(risk="high", math_score=20)
    lock = engine.build_scope_lock(project)
    assert lock.witness_count == 3


def test_tier_1_runs_one_witness(tmp_path):
    engine = TruthCertEngine(baselines_dir=tmp_path)
    project = _project(risk="medium", math_score=2)
    lock = engine.build_scope_lock(project)
    assert lock.witness_count == 1


def test_full_pipeline_with_mocked_witnesses(tmp_path):
    engine = TruthCertEngine(baselines_dir=tmp_path)
    project = _project(risk="medium", math_score=2)

    def mock_test_suite_run(command, cwd):
        return WitnessResult("test_suite", "PASS", 0, "ok", "", 1.0)

    with patch.object(engine.test_suite_witness, "run", side_effect=mock_test_suite_run):
        bundle = engine.verify(project)

    assert bundle.verdict == "PASS"
    assert len(bundle.witness_results) == 1
    assert bundle.bundle_hash


def test_disagreement_produces_reject(tmp_path):
    engine = TruthCertEngine(baselines_dir=tmp_path)
    project = _project(risk="high", math_score=5)  # tier 2

    def mock_test_run(command, cwd):
        return WitnessResult("test_suite", "PASS", 0, "ok", "", 1.0)

    def mock_smoke_run(modules, cwd):
        return WitnessResult("smoke", "FAIL", 1, "", "ImportError", 0.5)

    with patch.object(engine.test_suite_witness, "run", side_effect=mock_test_run), \
         patch.object(engine.smoke_witness, "run", side_effect=mock_smoke_run):
        bundle = engine.verify(project)

    assert bundle.verdict == "REJECT"
    assert "disagree" in bundle.arbitration_reason.lower()
