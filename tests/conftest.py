from __future__ import annotations

import json as _json
import sys
from datetime import datetime as _datetime
from pathlib import Path

import pytest

from overmind.storage.db import StateDatabase
from overmind.storage.models import (
    MemoryRecord,
    ProjectRecord,
    RunnerRecord,
    TaskRecord,
    utc_now,
)
from overmind.discovery.project_scanner import ProjectScanner
from overmind.config import AppConfig, PoliciesConfig

CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")
STUBS_DIR = Path(__file__).resolve().parents[1] / "stubs"
PYTHON_EXE = sys.executable


@pytest.fixture
def fresh_db(tmp_path):
    """Fresh SQLite DB with all Overmind tables. Cleaned up after test."""
    db_path = tmp_path / "test_overmind.db"
    db = StateDatabase(db_path)
    yield db
    db.close()


@pytest.fixture(scope="session")
def cardiooracle_project():
    """Scan real CardioOracle once per session. Read-only."""
    config = AppConfig.from_directory()
    scanner = ProjectScanner(config)
    record = scanner.scan_project(CARDIOORACLE_ROOT)
    return record


@pytest.fixture
def seeded_db(fresh_db, cardiooracle_project):
    """fresh_db + CardioOracle record + sample memories + Q-router history."""
    db = fresh_db
    db.upsert_project(cardiooracle_project)

    for i, (mtype, title, content) in enumerate([
        ("heuristic", "Most common error: ValueError",
         "Across 30 sessions, ValueError appeared 178 times."),
        ("decision", "Review: CONCERNS (2P0/3P1/1P2)",
         "Multi-persona review on tick 50: verdict=CONCERNS."),
        ("project_learning", "CardioOracle calibration fixed",
         "Platt scaling improved calibration slope from 0.194 to 0.874."),
    ]):
        db.upsert_memory(MemoryRecord(
            memory_id=f"seed_mem_{i}",
            memory_type=mtype,
            scope=cardiooracle_project.project_id,
            title=title,
            content=content,
            source_tick=50,
            relevance=0.9,
            confidence=0.8,
            tags=["seed", mtype],
        ))

    db.update_routing_score("claude", "verification", True)
    db.update_routing_score("claude", "verification", True)
    db.update_routing_score("claude", "verification", False)

    yield db


@pytest.fixture(scope="session")
def stub_runners():
    """RunnerRecord objects pointing to stub scripts."""
    return {
        "claude_stub": RunnerRecord(
            runner_id="claude_stub",
            runner_type="claude",
            environment="windows",
            command=f'"{PYTHON_EXE}" "{STUBS_DIR / "echo_runner.py"}"',
            success_rate_7d=0.7,
        ),
        "codex_stub": RunnerRecord(
            runner_id="codex_stub",
            runner_type="codex",
            environment="windows",
            command=f'"{PYTHON_EXE}" "{STUBS_DIR / "echo_runner.py"}"',
            success_rate_7d=0.6,
        ),
        "loop_stub": RunnerRecord(
            runner_id="loop_stub",
            runner_type="claude",
            environment="windows",
            command=f'"{PYTHON_EXE}" "{STUBS_DIR / "loop_runner.py"}"',
        ),
        "slow_stub": RunnerRecord(
            runner_id="slow_stub",
            runner_type="gemini",
            environment="windows",
            command=f'"{PYTHON_EXE}" "{STUBS_DIR / "slow_runner.py"}" 2',
            optional=True,
        ),
    }


@pytest.fixture
def policies():
    """PoliciesConfig loaded from Overmind's real config."""
    config = AppConfig.from_directory()
    return config.policies


def pytest_sessionfinish(session, exitstatus):
    """Write test results to JSON for dashboard consumption."""
    results = []
    for item in session.items:
        passed = None
        if hasattr(item, "stash"):
            try:
                passed = item.stash.get("passed", None)
            except Exception:
                pass
        results.append({
            "name": item.name,
            "file": item.nodeid.split("::")[0].split("/")[-1],
            "nodeid": item.nodeid,
            "passed": passed,
        })
    output_path = Path(__file__).resolve().parents[1] / "dashboard" / "test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_json.dumps({
        "timestamp": _datetime.now().isoformat(),
        "total": len(results),
        "exit_status": exitstatus,
        "tests": results,
    }, indent=2), encoding="utf-8")


def pytest_runtest_makereport(item, call):
    """Store pass/fail status on each test item."""
    if call.when == "call":
        if hasattr(item, "stash"):
            item.stash["passed"] = call.excinfo is None
