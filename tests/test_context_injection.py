"""Test that context injection builds correct content for CardioOracle."""
from __future__ import annotations

from overmind.activation.context_injector import ContextInjector


def test_context_has_overmind_header(seeded_db, cardiooracle_project):
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "OVERMIND CONTEXT" in ctx


def test_context_includes_heuristics(seeded_db, cardiooracle_project):
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "Learned Heuristics" in ctx or "ValueError" in ctx


def test_context_includes_q_scores(seeded_db, cardiooracle_project):
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "Performance" in ctx or "q=" in ctx


def test_empty_db_no_crash(fresh_db):
    injector = ContextInjector(fresh_db)
    ctx = injector.build_context("C:\\nonexistent", "claude")
    assert isinstance(ctx, str)
