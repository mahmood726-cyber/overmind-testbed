from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PATH_FILES = [
    REPO_ROOT / "conftest.py",
    REPO_ROOT / "test_paths.py",
    REPO_ROOT / "tests" / "conftest.py",
    REPO_ROOT / "tests" / "test_discovery.py",
    REPO_ROOT / "tests" / "test_routing.py",
    REPO_ROOT / "tests" / "test_verification.py",
    REPO_ROOT / "tests" / "test_wiki_compiler.py",
    REPO_ROOT / "tests" / "test_worktree.py",
]


def test_harness_has_no_hardcoded_machine_paths() -> None:
    for path in PATH_FILES:
        text = path.read_text(encoding="utf-8")
        assert "C:/overmind" not in text, path
        assert r"C:\overmind" not in text, path
        assert "C:/Models/CardioOracle" not in text, path
        assert r"C:\Models\CardioOracle" not in text, path
        assert "C:/test" not in text, path
        assert r"C:\test" not in text, path
