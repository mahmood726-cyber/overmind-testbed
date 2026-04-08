"""Test Evolution Manager: recipe tracking, resolution, confidence, procedures."""
from __future__ import annotations

from pathlib import Path

from overmind.diagnosis.judge import Diagnosis
from overmind.evolution.manager import EvolutionManager
from overmind.evolution.recipe import Recipe


def _diag(project_id="proj_a", failure_type="DEPENDENCY_ROT", evidence=None):
    return Diagnosis(
        project_id=project_id,
        failure_type=failure_type,
        confidence=0.9,
        summary="test diagnosis",
        evidence=evidence or ["ModuleNotFoundError: No module named 'scipy'"],
        recommended_action="pip install scipy",
        witness_type="smoke",
        created_at="2026-04-07T03:00:00Z",
    )


def test_new_diagnosis_creates_candidate(tmp_path):
    mgr = EvolutionManager(tmp_path / "wiki")
    stats = mgr.evolve([_diag()])
    assert stats["new_recipes"] == 1
    assert stats["total_recipes"] == 1
    assert (tmp_path / "wiki" / "PROCEDURES.md").exists()


def test_repeated_pattern_increments(tmp_path):
    mgr = EvolutionManager(tmp_path / "wiki")
    mgr.evolve([_diag(project_id="proj_a")])
    stats = mgr.evolve([_diag(project_id="proj_b")])
    assert stats["updated_recipes"] >= 1
    # Recipe should have times_seen >= 2
    content = (tmp_path / "wiki" / "PROCEDURES.md").read_text(encoding="utf-8")
    assert "| 2 |" in content


def test_resolution_tracked(tmp_path):
    mgr = EvolutionManager(tmp_path / "wiki")
    # Night 1: failure
    diag = _diag(project_id="proj_a")
    mgr.evolve([diag])
    # Night 2: resolved (proj_a now passing)
    stats = mgr.evolve(
        diagnoses=[],
        last_night_diagnoses=[diag],
        resolved_project_ids={"proj_a"},
    )
    assert stats["resolutions"] == 1


def test_confidence_calculated(tmp_path):
    recipe = Recipe(
        recipe_id="test", failure_type="TIMEOUT",
        pattern="timed out", fix_description="increase timeout",
        times_seen=4, times_resolved=2,
    )
    assert recipe.confidence == 0.5
    recipe.record_resolved()
    assert recipe.confidence == 0.75  # 3/4 (record_resolved only increments times_resolved)


def test_procedures_md_written(tmp_path):
    mgr = EvolutionManager(tmp_path / "wiki")
    mgr.evolve([_diag()])
    content = (tmp_path / "wiki" / "PROCEDURES.md").read_text(encoding="utf-8")
    assert "# Overmind Procedures" in content
    assert "DEPENDENCY_ROT" in content
    assert "scipy" in content


def test_recipe_recommended_on_match(tmp_path):
    mgr = EvolutionManager(tmp_path / "wiki")
    diag1 = _diag(project_id="proj_a")
    mgr.evolve([diag1])
    # Manually make it proven
    mgr.evolve(
        diagnoses=[_diag(project_id="proj_b")],
        last_night_diagnoses=[diag1],
        resolved_project_ids={"proj_a"},
    )
    # Now look up recommendation
    diag3 = _diag(project_id="proj_c")
    rec = mgr.get_recommendation(diag3)
    assert rec is not None
    assert rec.is_proven()
    assert "scipy" in rec.pattern or "scipy" in rec.fix_description
