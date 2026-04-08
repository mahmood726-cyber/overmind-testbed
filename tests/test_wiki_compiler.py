"""Test wiki compiler: article generation, history, index, changelog."""
from __future__ import annotations

from pathlib import Path

from overmind.storage.models import ProjectRecord
from overmind.verification.scope_lock import ScopeLock, WitnessResult
from overmind.verification.cert_bundle import CertBundle
from overmind.wiki.compiler import WikiCompiler


def _bundle(project_id="proj_a", verdict="CERTIFIED", reason="2/2 agree"):
    lock = ScopeLock(
        project_id=project_id, project_path="C:\\test",
        risk_profile="high", witness_count=2,
        test_command="pytest", smoke_modules=("engine",),
        baseline_path=None, expected_outcome="pass",
        source_hash="abc", created_at="2026-04-07T00:00:00Z",
    )
    w1 = WitnessResult("test_suite", "PASS", 0, "30 passed", "", 3.2)
    w2 = WitnessResult("smoke", "PASS", 0, "5 modules OK", "", 0.8)
    return CertBundle(
        project_id=project_id, scope_lock=lock,
        witness_results=[w1, w2], verdict=verdict,
        arbitration_reason=reason, timestamp="2026-04-07T03:00:00Z",
    )


def _project(project_id="proj_a", name="TestProject"):
    return ProjectRecord(
        project_id=project_id, name=name,
        root_path="C:\\test", risk_profile="high",
        advanced_math_score=20, project_type="python_tool",
        stack=["python"], test_commands=["pytest tests/ -q"],
    )


def test_article_generated(tmp_path):
    compiler = WikiCompiler(tmp_path / "wiki")
    compiler.compile([_bundle()], [_project()])
    article = (tmp_path / "wiki" / "proj_a.md").read_text(encoding="utf-8")
    assert "# TestProject" in article
    assert "CERTIFIED" in article
    assert "test_suite" in article


def test_history_appended(tmp_path):
    wiki_dir = tmp_path / "wiki"
    compiler = WikiCompiler(wiki_dir)
    # First run
    compiler.compile([_bundle()], [_project()])
    # Second run
    compiler.compile([_bundle(verdict="REJECT", reason="disagree")], [_project()])
    article = (wiki_dir / "proj_a.md").read_text(encoding="utf-8")
    # Should have 2 history rows
    assert article.count("| 20") >= 2  # date starts with "20xx"


def test_index_generated(tmp_path):
    compiler = WikiCompiler(tmp_path / "wiki")
    compiler.compile([_bundle()], [_project()])
    index = (tmp_path / "wiki" / "INDEX.md").read_text(encoding="utf-8")
    assert "Overmind Wiki Index" in index
    assert "TestProject" in index
    assert "CERTIFIED" in index


def test_changelog_appended(tmp_path):
    compiler = WikiCompiler(tmp_path / "wiki")
    compiler.compile([_bundle()], [_project()])
    changelog = (tmp_path / "wiki" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Overmind Wiki Changelog" in changelog
    assert "Certified: 1" in changelog or "certified" in changelog.lower()


def test_reject_has_notes(tmp_path):
    lock = ScopeLock(
        project_id="proj_b", project_path="C:\\test",
        risk_profile="high", witness_count=2,
        test_command="pytest", smoke_modules=("engine",),
        baseline_path=None, expected_outcome="pass",
        source_hash="abc", created_at="2026-04-07T00:00:00Z",
    )
    w1 = WitnessResult("test_suite", "PASS", 0, "ok", "", 1.0)
    w2 = WitnessResult("smoke", "FAIL", 1, "", "ImportError: scipy", 0.5)
    bundle = CertBundle(
        project_id="proj_b", scope_lock=lock,
        witness_results=[w1, w2], verdict="REJECT",
        arbitration_reason="Witnesses disagree: test_suite PASS vs smoke FAIL",
        timestamp="2026-04-07T03:00:00Z",
    )
    proj = ProjectRecord(
        project_id="proj_b", name="BrokenProject",
        root_path="C:\\test", risk_profile="high",
        advanced_math_score=15, test_commands=["pytest"],
    )
    compiler = WikiCompiler(tmp_path / "wiki")
    compiler.compile([bundle], [proj])
    article = (tmp_path / "wiki" / "proj_b.md").read_text(encoding="utf-8")
    assert "## Notes" in article
    assert "ImportError" in article


def test_compile_returns_stats(tmp_path):
    compiler = WikiCompiler(tmp_path / "wiki")
    stats = compiler.compile([_bundle()], [_project()])
    assert stats["articles_written"] == 1
    assert stats["certified"] == 1
    assert stats["rejected"] == 0
