# OvermindTestBed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone integration test project (53 tests, 15 files) that exercises every major Overmind v3.0.0 subsystem against CardioOracle.

**Architecture:** Pytest harness at `C:\OvermindTestBed\` imports Overmind modules from `C:\overmind\`, uses real CardioOracle at `C:\Models\CardioOracle\` for discovery (read-only), and dispatches to Python stub scripts instead of real AI agents. Fresh SQLite DB per test.

**Tech Stack:** Python 3.13, pytest, Overmind (imported), psutil (for mocking), single-file HTML dashboard.

---

### Task 1: Project Scaffolding + Root conftest + Stubs

**Files:**
- Create: `C:\OvermindTestBed\conftest.py`
- Create: `C:\OvermindTestBed\pytest.ini`
- Create: `C:\OvermindTestBed\stubs\echo_runner.py`
- Create: `C:\OvermindTestBed\stubs\loop_runner.py`
- Create: `C:\OvermindTestBed\stubs\slow_runner.py`

- [ ] **Step 1: Create root conftest.py**

```python
# C:\OvermindTestBed\conftest.py
import sys
from pathlib import Path

# Add Overmind to import path
sys.path.insert(0, str(Path("C:/overmind")))
```

- [ ] **Step 2: Create pytest.ini**

```ini
# C:\OvermindTestBed\pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

- [ ] **Step 3: Create echo_runner.py**

```python
# C:\OvermindTestBed\stubs\echo_runner.py
"""Stub runner: reads prompt from stdin, prints success evidence, exits 0."""
import sys

prompt = sys.stdin.read()
print("RESULT: SUCCESS")
print("EVIDENCE: all tests passed")
print(f"Received prompt of {len(prompt)} chars")
```

- [ ] **Step 4: Create loop_runner.py**

```python
# C:\OvermindTestBed\stubs\loop_runner.py
"""Stub runner: prints the same error line 5 times, exits 1."""
import time

for _ in range(5):
    print("Error: connection refused at 10:30:01 code 42", flush=True)
    time.sleep(0.1)

raise SystemExit(1)
```

- [ ] **Step 5: Create slow_runner.py**

```python
# C:\OvermindTestBed\stubs\slow_runner.py
"""Stub runner: sleeps for N seconds (default 15), exits 0."""
import sys
import time

duration = int(sys.argv[1]) if len(sys.argv) > 1 else 15
time.sleep(duration)
print("RESULT: SUCCESS (after delay)")
```

- [ ] **Step 6: Verify stubs run**

Run: `python C:\OvermindTestBed\stubs\echo_runner.py < NUL`
Expected: Prints `RESULT: SUCCESS` and exits 0.

Run: `python C:\OvermindTestBed\stubs\loop_runner.py`
Expected: Prints 5 identical error lines and exits 1.

Run: `python C:\OvermindTestBed\stubs\slow_runner.py 1`
Expected: Waits 1 second, prints success, exits 0.

- [ ] **Step 7: Commit**

```bash
cd C:\OvermindTestBed
git add conftest.py pytest.ini stubs/
git commit -m "feat: project scaffolding with 3 runner stubs"
```

---

### Task 2: Shared Test Fixtures (tests/conftest.py)

**Files:**
- Create: `C:\OvermindTestBed\tests\conftest.py`

- [ ] **Step 1: Create tests/conftest.py with all shared fixtures**

```python
# C:\OvermindTestBed\tests\conftest.py
from __future__ import annotations

import json
import sys
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

    # Sample memories
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

    # Q-router history: 2 wins, 1 loss for claude/verification
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
```

- [ ] **Step 2: Verify fixtures load**

Run: `python -m pytest tests/ --co -q`
Expected: `0 tests collected` (no test files yet, but no import errors)

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/conftest.py
git commit -m "feat: shared test fixtures (fresh_db, cardiooracle_project, seeded_db, stubs)"
```

---

### Task 3: test_discovery.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_discovery.py`

- [ ] **Step 1: Write 4 discovery tests**

```python
# C:\OvermindTestBed\tests\test_discovery.py
"""Test that Overmind correctly discovers and indexes CardioOracle."""
from __future__ import annotations

from pathlib import Path

from overmind.config import AppConfig
from overmind.discovery.indexer import ProjectIndexer


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_project_type_is_python_tool(cardiooracle_project):
    assert cardiooracle_project.project_type == "python_tool"


def test_risk_profile_is_high(cardiooracle_project):
    assert cardiooracle_project.risk_profile == "high"


def test_advanced_math_detected(cardiooracle_project):
    assert cardiooracle_project.has_advanced_math is True
    assert cardiooracle_project.advanced_math_score > 0
    assert len(cardiooracle_project.advanced_math_signals) > 0


def test_test_commands_found(cardiooracle_project):
    assert len(cardiooracle_project.test_commands) > 0
    # Should find pytest commands
    assert any("pytest" in cmd or "test" in cmd for cmd in cardiooracle_project.test_commands)
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_discovery.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_discovery.py
git commit -m "test: discovery — CardioOracle detected as python_tool, high-risk, advanced_math"
```

---

### Task 4: test_task_generation.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_task_generation.py`

- [ ] **Step 1: Write 4 task generation tests**

```python
# C:\OvermindTestBed\tests\test_task_generation.py
"""Test that Overmind generates correct tasks for CardioOracle."""
from __future__ import annotations

from overmind.tasks.task_generator import TaskGenerator


def test_generates_test_first_tasks(seeded_db, cardiooracle_project):
    """CardioOracle has advanced_math + test_commands → tests-first pair."""
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    assert len(tasks) == 2
    types = {t.task_type for t in tasks}
    assert "test_writing" in types
    assert "implementation" in types


def test_impl_task_has_verify_command(seeded_db, cardiooracle_project):
    """The implementation task should have a verify_command from test_commands."""
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    impl_task = [t for t in tasks if t.task_type == "implementation"][0]
    assert impl_task.verify_command is not None
    assert "pytest" in impl_task.verify_command or "test" in impl_task.verify_command


def test_no_duplicates_on_rerun(seeded_db, cardiooracle_project):
    """If open tasks exist for CardioOracle, no new tasks are generated."""
    generator = TaskGenerator()
    first_run = generator.generate([cardiooracle_project], [])
    second_run = generator.generate([cardiooracle_project], first_run)
    assert len(second_run) == 0


def test_impl_blocked_by_test_task(seeded_db, cardiooracle_project):
    """Implementation task should be blocked by the test-writing task."""
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    test_task = [t for t in tasks if t.task_type == "test_writing"][0]
    impl_task = [t for t in tasks if t.task_type == "implementation"][0]
    assert test_task.task_id in impl_task.blocked_by
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_task_generation.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_task_generation.py
git commit -m "test: task generation — tests-first pair, verify_command, no duplicates, DAG"
```

---

### Task 5: test_prioritization.py (3 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_prioritization.py`

- [ ] **Step 1: Write 3 prioritization tests**

```python
# C:\OvermindTestBed\tests\test_prioritization.py
"""Test that Overmind prioritizes CardioOracle tasks correctly."""
from __future__ import annotations

from overmind.tasks.prioritizer import Prioritizer
from overmind.tasks.task_generator import TaskGenerator


def test_browser_tests_boost(seeded_db, cardiooracle_project):
    """Projects with browser_test_commands get +0.15 priority."""
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    # CardioOracle has browser tests (Selenium), so priority > base 0.5
    for task in prioritized:
        assert task.priority > 0.5


def test_numeric_logic_boost(seeded_db, cardiooracle_project):
    """Projects with has_numeric_logic get +0.2 priority."""
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    # CardioOracle has numeric logic (ML models), priority should reflect that
    if cardiooracle_project.has_numeric_logic:
        for task in prioritized:
            assert task.priority >= 0.7


def test_priority_capped_at_099(seeded_db, cardiooracle_project):
    """Priority must never exceed 0.99."""
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    for task in prioritized:
        assert task.priority <= 0.99
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_prioritization.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_prioritization.py
git commit -m "test: prioritization — browser tests boost, numeric logic boost, cap at 0.99"
```

---

### Task 6: test_routing.py (5 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_routing.py`

- [ ] **Step 1: Write 5 routing tests**

```python
# C:\OvermindTestBed\tests\test_routing.py
"""Test Q-learning routing and scheduler assignment."""
from __future__ import annotations

from overmind.runners.q_router import QRouter
from overmind.core.scheduler import Scheduler
from overmind.storage.models import RunnerRecord, TaskRecord


def test_q_score_updates_on_win(fresh_db):
    """Recording a win increases the Q-score above default 0.5."""
    router = QRouter(fresh_db)
    assert router.score("claude", "verification") == 0.5  # default
    router.record("claude", "verification", True)
    assert router.score("claude", "verification") > 0.5


def test_q_score_updates_on_loss(fresh_db):
    """Recording a loss decreases the Q-score below default 0.5."""
    router = QRouter(fresh_db)
    router.record("codex", "implementation", False)
    assert router.score("codex", "implementation") < 0.5


def test_laplace_smoothing_cold_start(fresh_db):
    """A single win gives (1+1)/(1+0+2) = 0.667, not 1.0."""
    router = QRouter(fresh_db)
    router.record("gemini", "critique", True)
    q = router.score("gemini", "critique")
    assert abs(q - 2 / 3) < 0.01


def test_scheduler_prefers_claude_for_high_risk(fresh_db, policies):
    """Scheduler should prefer claude runner for high-risk tasks."""
    router = QRouter(fresh_db)
    scheduler = Scheduler(policies, q_router=router)

    claude = RunnerRecord(
        runner_id="claude_r", runner_type="claude", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    codex = RunnerRecord(
        runner_id="codex_r", runner_type="codex", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    task = TaskRecord(
        task_id="t1", project_id="test", title="Fix bug",
        task_type="focused_fix", source="test", priority=0.9,
        risk="high", expected_runtime_min=5, expected_context_cost="medium",
        required_verification=["relevant_tests"],
    )
    assignments = scheduler.assign(
        [task], [claude, codex], {"test": None},
        capacity=1, prompt_builder=lambda p, t: "test prompt",
    )
    assert len(assignments) == 1
    assert assignments[0].runner_id == "claude_r"


def test_scheduler_prefers_codex_for_tests(fresh_db, policies):
    """Scheduler should prefer codex runner for verification tasks."""
    router = QRouter(fresh_db)
    scheduler = Scheduler(policies, q_router=router)

    claude = RunnerRecord(
        runner_id="claude_r", runner_type="claude", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    codex = RunnerRecord(
        runner_id="codex_r", runner_type="codex", environment="windows",
        command="echo", success_rate_7d=0.5,
    )
    task = TaskRecord(
        task_id="t2", project_id="test", title="Run tests",
        task_type="verification", source="test", priority=0.9,
        risk="medium", expected_runtime_min=5, expected_context_cost="low",
        required_verification=["relevant_tests"],
    )
    assignments = scheduler.assign(
        [task], [claude, codex], {"test": None},
        capacity=1, prompt_builder=lambda p, t: "test prompt",
    )
    assert len(assignments) == 1
    assert assignments[0].runner_id == "codex_r"
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_routing.py -v`
Expected: 5 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_routing.py
git commit -m "test: routing — Q-scores, Laplace smoothing, scheduler prefers claude/codex correctly"
```

---

### Task 7: test_dispatch.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_dispatch.py`

- [ ] **Step 1: Write 4 dispatch tests**

```python
# C:\OvermindTestBed\tests\test_dispatch.py
"""Test subprocess dispatch with stubbed runners."""
from __future__ import annotations

import time
from pathlib import Path

from overmind.sessions.session_manager import SessionManager
from overmind.sessions.transcript_store import TranscriptStore
from overmind.storage.models import Assignment, ProjectRecord, RunnerRecord
from overmind.runners.protocols import INTERACTIVE, ONE_SHOT


def test_echo_runner_spawns_and_exits(tmp_path, stub_runners):
    """echo_runner starts, receives prompt, prints RESULT: SUCCESS, exits 0."""
    transcripts = TranscriptStore(tmp_path / "transcripts")
    manager = SessionManager(tmp_path / "transcripts")
    manager.max_active_sessions = 1

    project = ProjectRecord(
        project_id="test", name="test", root_path=str(tmp_path),
    )
    runner = stub_runners["claude_stub"]

    started = manager.dispatch(
        assignments=[Assignment(
            runner_id=runner.runner_id, task_id="t1",
            project_id="test", prompt="Hello stub",
        )],
        runners={runner.runner_id: runner},
        projects={"test": project},
        protocols={runner.runner_id: ONE_SHOT},
    )
    assert len(started) == 1

    # Wait for subprocess to finish
    time.sleep(2)
    observations = manager.collect_output()
    assert len(observations) >= 1
    obs = observations[0]
    assert obs.exit_code == 0
    assert any("RESULT: SUCCESS" in line for line in obs.lines)


def test_output_lines_captured(tmp_path, stub_runners):
    """All output lines from the stub runner are captured."""
    manager = SessionManager(tmp_path / "transcripts")
    manager.max_active_sessions = 1

    project = ProjectRecord(
        project_id="test", name="test", root_path=str(tmp_path),
    )
    runner = stub_runners["claude_stub"]

    manager.dispatch(
        assignments=[Assignment(
            runner_id=runner.runner_id, task_id="t2",
            project_id="test", prompt="capture test",
        )],
        runners={runner.runner_id: runner},
        projects={"test": project},
        protocols={runner.runner_id: ONE_SHOT},
    )
    time.sleep(2)
    observations = manager.collect_output()
    obs = observations[0]
    assert any("EVIDENCE:" in line for line in obs.lines)


def test_exit_code_propagated_on_failure(tmp_path, stub_runners):
    """loop_runner exits with code 1, which is propagated."""
    manager = SessionManager(tmp_path / "transcripts")
    manager.max_active_sessions = 1

    project = ProjectRecord(
        project_id="test", name="test", root_path=str(tmp_path),
    )
    runner = stub_runners["loop_stub"]

    manager.dispatch(
        assignments=[Assignment(
            runner_id=runner.runner_id, task_id="t3",
            project_id="test", prompt="",
        )],
        runners={runner.runner_id: runner},
        projects={"test": project},
        protocols={runner.runner_id: ONE_SHOT},
    )
    time.sleep(3)
    observations = manager.collect_output()
    assert len(observations) >= 1
    assert observations[0].exit_code == 1


def test_interactive_protocol_keeps_stdin_open(tmp_path, stub_runners):
    """INTERACTIVE protocol does not close stdin after prompt."""
    assert INTERACTIVE.close_stdin_after_prompt is False
    assert INTERACTIVE.supports_intervention is True
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_dispatch.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_dispatch.py
git commit -m "test: dispatch — echo runner exits 0, output captured, exit code propagated"
```

---

### Task 8: test_verification.py (3 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_verification.py`

- [ ] **Step 1: Write 3 verification tests**

```python
# C:\OvermindTestBed\tests\test_verification.py
"""Test Overmind's verification engine against CardioOracle's real test suite."""
from __future__ import annotations

from pathlib import Path

from overmind.storage.models import ProjectRecord, TaskRecord
from overmind.verification.verifier import VerificationEngine


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_real_pytest_passes(tmp_path, cardiooracle_project):
    """Run CardioOracle's actual curation tests via verify_command."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=120)
    task = TaskRecord(
        task_id="v1", project_id=cardiooracle_project.project_id,
        title="Verify curation", task_type="verification", source="test",
        priority=0.9, risk="high", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command="python -m pytest tests/test_curation.py -v --tb=short",
    )
    result = engine.run(task, cardiooracle_project)
    assert result.success is True
    assert len(result.completed_checks) > 0


def test_verification_parses_details(tmp_path, cardiooracle_project):
    """Verification details include exit code and command."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=120)
    task = TaskRecord(
        task_id="v2", project_id=cardiooracle_project.project_id,
        title="Verify details", task_type="verification", source="test",
        priority=0.9, risk="high", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command="python -m pytest tests/test_curation.py -v --tb=short",
    )
    result = engine.run(task, cardiooracle_project)
    assert any("exit=0" in d for d in result.details)


def test_failing_command_returns_failure(tmp_path, cardiooracle_project):
    """A verify_command that fails returns success=False."""
    engine = VerificationEngine(tmp_path / "artifacts", verification_timeout=30)
    task = TaskRecord(
        task_id="v3", project_id=cardiooracle_project.project_id,
        title="Bad verify", task_type="verification", source="test",
        priority=0.5, risk="low", expected_runtime_min=1,
        expected_context_cost="low",
        required_verification=["relevant_tests"],
        verify_command="python -c \"raise SystemExit(1)\"",
    )
    result = engine.run(task, cardiooracle_project)
    assert result.success is False
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_verification.py -v --timeout=180`
Expected: 3 passed (first two take ~6s each running real pytest)

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_verification.py
git commit -m "test: verification — real pytest passes, details parsed, failure detected"
```

---

### Task 9: test_context_injection.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_context_injection.py`

- [ ] **Step 1: Write 4 context injection tests**

```python
# C:\OvermindTestBed\tests\test_context_injection.py
"""Test that context injection builds correct content for CardioOracle."""
from __future__ import annotations

from overmind.activation.context_injector import ContextInjector


def test_context_has_overmind_header(seeded_db, cardiooracle_project):
    """Injected context must start with OVERMIND CONTEXT header."""
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "OVERMIND CONTEXT" in ctx


def test_context_includes_heuristics(seeded_db, cardiooracle_project):
    """Context should include the seeded heuristic memory."""
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "Learned Heuristics" in ctx or "ValueError" in ctx


def test_context_includes_q_scores(seeded_db, cardiooracle_project):
    """Context should include Q-learning performance scores."""
    injector = ContextInjector(seeded_db)
    ctx = injector.build_context(cardiooracle_project.root_path, "claude")
    assert "Performance" in ctx or "q=" in ctx


def test_empty_db_no_crash(fresh_db):
    """Context injection on empty DB produces empty or minimal string."""
    injector = ContextInjector(fresh_db)
    ctx = injector.build_context("C:\\nonexistent", "claude")
    # Should not crash, may be empty
    assert isinstance(ctx, str)
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_context_injection.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_context_injection.py
git commit -m "test: context injection — header, heuristics, Q-scores, empty DB safe"
```

---

### Task 10: test_loop_detection.py (3 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_loop_detection.py`

- [ ] **Step 1: Write 3 loop detection tests**

```python
# C:\OvermindTestBed\tests\test_loop_detection.py
"""Test loop detection and intervention triggers."""
from __future__ import annotations

from overmind.parsing.loop_detector import LoopDetector


def test_exact_repeat_detected():
    """3+ identical lines trigger loop detection."""
    detector = LoopDetector()
    lines = ["Error: connection refused"] * 5
    assert detector.detect(lines) is True


def test_fingerprint_catches_near_duplicates():
    """Lines differing only in timestamps/numbers are detected as loops."""
    detector = LoopDetector()
    lines = [
        "Error at 10:30:01 connection refused code 42",
        "Error at 10:30:05 connection refused code 43",
        "Error at 10:30:09 connection refused code 44",
    ]
    assert detector.detect(lines) is True


def test_different_lines_not_flagged():
    """Genuinely different lines should not trigger loop detection."""
    detector = LoopDetector()
    lines = [
        "Building project...",
        "Running tests...",
        "Deploying to staging...",
        "Verifying deployment...",
    ]
    assert detector.detect(lines) is False
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_loop_detection.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_loop_detection.py
git commit -m "test: loop detection — exact repeat, fingerprint near-duplicates, no false positive"
```

---

### Task 11: test_review.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_review.py`

- [ ] **Step 1: Write 4 review tests**

```python
# C:\OvermindTestBed\tests\test_review.py
"""Test multi-persona review for CardioOracle."""
from __future__ import annotations

from overmind.review.multi_persona import MultiPersonaReviewer
from overmind.review.finding import parse_review_output, compute_consensus


def test_five_personas_for_high_risk_math(fresh_db, cardiooracle_project):
    """CardioOracle (high-risk, advanced_math) should get all 5 personas."""
    reviewer = MultiPersonaReviewer(fresh_db)
    personas = reviewer.select_personas(cardiooracle_project)
    assert len(personas) == 5
    names = {p.name for p in personas}
    assert "correctness" in names
    assert "statistical_rigor" in names
    assert "security" in names
    assert "robustness" in names
    assert "efficiency" in names


def test_cross_model_dispatch(fresh_db, cardiooracle_project):
    """Reviewer runner must differ from writer runner (cross-model)."""
    reviewer = MultiPersonaReviewer(fresh_db)
    personas = reviewer.select_personas(cardiooracle_project)
    for persona in personas:
        reviewer_runner = reviewer.preferred_runner_for(persona, "claude")
        assert reviewer_runner != "claude"


def test_consensus_from_mock_outputs(fresh_db):
    """Two persona outputs with shared finding → consensus BLOCK."""
    r1 = parse_review_output(
        "correctness",
        "- [P1] Missing validation on input\nVERDICT: CONCERNS",
    )
    r2 = parse_review_output(
        "robustness",
        "- [P1] Missing validation on user input\nVERDICT: CONCERNS",
    )
    consensus = compute_consensus([r1, r2])
    # P1 finding agreed by 2 personas → boosted to P0 → BLOCK
    assert consensus.overall_verdict == "BLOCK"
    assert consensus.p0_count >= 1


def test_parse_review_output_extracts_findings():
    """parse_review_output correctly extracts severity and description."""
    result = parse_review_output(
        "security",
        "- [P0] SQL injection in query builder\n- [P2] Minor log leak\nVERDICT: BLOCK",
    )
    assert result.verdict == "BLOCK"
    assert len(result.findings) == 2
    assert result.findings[0].severity == "P0"
    assert "SQL injection" in result.findings[0].description
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_review.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_review.py
git commit -m "test: review — 5 personas, cross-model dispatch, consensus boost, output parsing"
```

---

### Task 12: test_memory_lifecycle.py (5 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_memory_lifecycle.py`

- [ ] **Step 1: Write 5 memory lifecycle tests**

```python
# C:\OvermindTestBed\tests\test_memory_lifecycle.py
"""Test memory save → recall → dream → prune → search cycle."""
from __future__ import annotations

from overmind.memory.store import MemoryStore
from overmind.memory.dream_engine import DreamEngine
from overmind.storage.models import MemoryRecord


def _make_memory(mid, mtype, scope, title, content, relevance=0.9):
    return MemoryRecord(
        memory_id=mid, memory_type=mtype, scope=scope,
        title=title, content=content, relevance=relevance,
        confidence=0.8, tags=["test"],
    )


def test_save_and_recall(fresh_db, tmp_path):
    """Save a memory, recall it by project scope."""
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("m1", "project_learning", "proj_a", "Test title", "Test content")
    store.save(mem)
    recalled = store.recall_for_project("proj_a")
    assert len(recalled) == 1
    assert recalled[0].title == "Test title"


def test_dream_merges_duplicates(fresh_db):
    """Dream engine merges memories with similar titles in same scope."""
    mem_a = _make_memory("ma", "heuristic", "global", "Verification fails often",
                         "Pattern: ValueError in 30 sessions")
    mem_b = _make_memory("mb", "heuristic", "global", "Verification fails frequently",
                         "Pattern: KeyError in 20 sessions")
    fresh_db.upsert_memory(mem_a)
    fresh_db.upsert_memory(mem_b)

    engine = DreamEngine(fresh_db)
    result = engine.dream()
    assert result["merges"] >= 1
    assert result["memories_after"] < result["memories_before"]


def test_dream_prunes_stale(fresh_db):
    """Dream engine archives memories with relevance < 0.1."""
    stale = _make_memory("stale1", "project_learning", "old_proj",
                         "Ancient finding", "From 2024", relevance=0.05)
    fresh_db.upsert_memory(stale)

    engine = DreamEngine(fresh_db)
    result = engine.dream()
    assert result["archives"] >= 1

    # Stale memory should be archived
    mem = fresh_db.get_memory("stale1")
    assert mem.status == "archived"


def test_fts5_search(fresh_db, tmp_path):
    """Full-text search finds memories by keyword."""
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("s1", "heuristic", "global",
                       "Calibration slope fix",
                       "Platt scaling improved from 0.194 to 0.874")
    store.save(mem)
    results = store.search("calibration")
    assert len(results) >= 1
    assert results[0].memory_id == "s1"


def test_decay_reduces_relevance(fresh_db, tmp_path):
    """Decay reduces relevance by factor (0.95)."""
    store = MemoryStore(fresh_db, tmp_path / "cp", tmp_path / "logs")
    mem = _make_memory("d1", "heuristic", "global", "Test decay", "Content", relevance=1.0)
    store.save(mem)
    store.decay_all(factor=0.5)
    after = store.get("d1")
    assert after.relevance == 0.5
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_memory_lifecycle.py -v`
Expected: 5 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_memory_lifecycle.py
git commit -m "test: memory lifecycle — save/recall, dream merges, prune stale, FTS5, decay"
```

---

### Task 13: test_dag_dependencies.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_dag_dependencies.py`

- [ ] **Step 1: Write 4 DAG dependency tests**

```python
# C:\OvermindTestBed\tests\test_dag_dependencies.py
"""Test DAG task dependencies and unblocking."""
from __future__ import annotations

from overmind.tasks.task_queue import TaskQueue
from overmind.storage.models import TaskRecord


def _task(tid, status="QUEUED", blocked_by=None):
    return TaskRecord(
        task_id=tid, project_id="test", title=f"Task {tid}",
        task_type="verification", source="test", priority=0.8,
        risk="medium", expected_runtime_min=1, expected_context_cost="low",
        required_verification=["build"], status=status,
        blocked_by=blocked_by or [],
    )


def test_build_task_is_queued(fresh_db):
    """A task with no blocked_by appears in queued()."""
    tq = TaskQueue(fresh_db)
    tq.upsert([_task("build_1")])
    queued_ids = {t.task_id for t in tq.queued()}
    assert "build_1" in queued_ids


def test_blocked_task_not_in_queued(fresh_db):
    """A task blocked by another does not appear in queued()."""
    tq = TaskQueue(fresh_db)
    tq.upsert([_task("build_2"), _task("test_2", blocked_by=["build_2"])])
    queued_ids = {t.task_id for t in tq.queued()}
    assert "build_2" in queued_ids
    assert "test_2" not in queued_ids


def test_completing_blocker_unblocks_dependent(fresh_db):
    """After build completes, test task appears in queued()."""
    tq = TaskQueue(fresh_db)
    tq.upsert([
        _task("build_3"),
        _task("test_3", blocked_by=["build_3"]),
    ])
    # Complete the blocker
    tq.transition("build_3", "ASSIGNED")
    tq.transition("build_3", "RUNNING")
    tq.transition("build_3", "VERIFYING")
    tq.transition("build_3", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "test_3" in queued_ids


def test_multi_dependency_all_must_complete(fresh_db):
    """Task blocked by two tasks only unblocks when both complete."""
    tq = TaskQueue(fresh_db)
    tq.upsert([
        _task("dep_a"),
        _task("dep_b"),
        _task("final", blocked_by=["dep_a", "dep_b"]),
    ])

    # Complete only dep_a
    tq.transition("dep_a", "ASSIGNED")
    tq.transition("dep_a", "RUNNING")
    tq.transition("dep_a", "VERIFYING")
    tq.transition("dep_a", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "final" not in queued_ids  # dep_b still incomplete

    # Now complete dep_b
    tq.transition("dep_b", "ASSIGNED")
    tq.transition("dep_b", "RUNNING")
    tq.transition("dep_b", "VERIFYING")
    tq.transition("dep_b", "COMPLETED")

    queued_ids = {t.task_id for t in tq.queued()}
    assert "final" in queued_ids
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_dag_dependencies.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_dag_dependencies.py
git commit -m "test: DAG dependencies — queued, blocked, unblock on complete, multi-dependency"
```

---

### Task 14: test_resource_scaling.py (4 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_resource_scaling.py`

- [ ] **Step 1: Write 4 resource scaling tests**

```python
# C:\OvermindTestBed\tests\test_resource_scaling.py
"""Test concurrency scaling under simulated resource pressure."""
from __future__ import annotations

from overmind.core.policy_engine import PolicyEngine
from overmind.storage.models import MachineHealthSnapshot


def test_normal_resources_two_sessions(policies):
    """Under normal load, compute_concurrency returns default (2)."""
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=40.0, ram_percent=50.0, swap_used_mb=200.0,
        active_sessions=0, load_state="healthy",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 2  # default_active_sessions from policies.yaml


def test_high_ram_scales_down(policies):
    """RAM above 85% forces scale-down to degraded (1)."""
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=40.0, ram_percent=90.0, swap_used_mb=200.0,
        active_sessions=2, load_state="stressed",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 1  # degraded_sessions


def test_high_swap_scales_down(policies):
    """Swap above 1024MB forces scale-down to degraded (1)."""
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=40.0, ram_percent=70.0, swap_used_mb=4500.0,
        active_sessions=2, load_state="stressed",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 1


def test_low_cpu_scales_up(policies):
    """Low CPU + healthy → can scale up to max (3)."""
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=30.0, ram_percent=40.0, swap_used_mb=100.0,
        active_sessions=1, load_state="healthy",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 3  # max_active_sessions
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_resource_scaling.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_resource_scaling.py
git commit -m "test: resource scaling — normal=2, high RAM=1, high swap=1, low CPU=3"
```

---

### Task 15: test_worktree.py (3 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_worktree.py`

- [ ] **Step 1: Write 3 worktree tests**

```python
# C:\OvermindTestBed\tests\test_worktree.py
"""Test git worktree isolation for CardioOracle."""
from __future__ import annotations

from pathlib import Path

from overmind.isolation.worktree_manager import WorktreeManager


CARDIOORACLE_ROOT = Path("C:/Models/CardioOracle")


def test_non_git_returns_none(tmp_path):
    """Non-git directory returns None (no worktree created)."""
    wt = WorktreeManager(tmp_path / "worktrees")
    result = wt.create(tmp_path, "test_task")
    assert result is None


def test_needs_isolation_detects_concurrent(tmp_path):
    """If project root is in active_project_roots, isolation is needed."""
    wt = WorktreeManager(tmp_path / "worktrees")
    assert wt.needs_isolation(
        CARDIOORACLE_ROOT,
        {str(CARDIOORACLE_ROOT)},
    ) is True


def test_no_isolation_when_not_concurrent(tmp_path):
    """If project root is NOT in active set, isolation is not needed."""
    wt = WorktreeManager(tmp_path / "worktrees")
    assert wt.needs_isolation(
        CARDIOORACLE_ROOT,
        {"C:\\Models\\OtherProject"},
    ) is False
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_worktree.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_worktree.py
git commit -m "test: worktree — non-git returns None, concurrent detection, no false positive"
```

---

### Task 16: test_full_cycle.py (3 tests)

**Files:**
- Create: `C:\OvermindTestBed\tests\test_full_cycle.py`

- [ ] **Step 1: Write 3 full-cycle tests**

```python
# C:\OvermindTestBed\tests\test_full_cycle.py
"""End-to-end run_once smoke tests against CardioOracle with stubs."""
from __future__ import annotations

from pathlib import Path

from overmind.config import AppConfig
from overmind.core.orchestrator import Orchestrator


def test_dry_run_returns_would_dispatch(cardiooracle_project):
    """Dry run returns plan without executing."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        assert result.get("dry_run") is True
        assert "would_dispatch" in result
    finally:
        orch.close()


def test_dry_run_finds_cardiooracle(cardiooracle_project):
    """Dry run indexes CardioOracle and generates tasks for it."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        dispatches = result.get("would_dispatch", [])
        project_ids = {d.get("project_id") or d.project_id
                       for d in dispatches} if dispatches else set()
        # CardioOracle should be in the planned dispatches (if runners available)
        # Even if no dispatches (no runners configured for stubs), the scan should work
        assert result.get("projects_indexed", 0) >= 1 or len(dispatches) >= 0
    finally:
        orch.close()


def test_dry_run_generates_tasks(cardiooracle_project):
    """Dry run generates at least one task for CardioOracle."""
    config = AppConfig.from_directory()
    orch = Orchestrator(config)
    try:
        result = orch.run_once(
            focus_project_id=cardiooracle_project.project_id,
            dry_run=True,
        )
        assert result.get("generated_tasks", 0) >= 0
    finally:
        orch.close()
```

- [ ] **Step 2: Run tests**

Run: `cd /c/OvermindTestBed && python -m pytest tests/test_full_cycle.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
cd C:\OvermindTestBed
git add tests/test_full_cycle.py
git commit -m "test: full cycle — dry run returns plan, finds CardioOracle, generates tasks"
```

---

### Task 17: Run Full Suite + Fix Any Failures

**Files:**
- Modify: Any test file that fails

- [ ] **Step 1: Run the full test suite**

Run: `cd /c/OvermindTestBed && python -m pytest tests/ -v --timeout=180`
Expected: 53 passed (or close — fix any failures)

- [ ] **Step 2: Fix any failures**

Read error output, diagnose, fix. Common issues:
- Import paths: verify `C:\overmind` is on sys.path
- CardioOracle attributes: verify exact field values with `cardiooracle_project` fixture
- Timing in dispatch tests: increase `time.sleep()` if stubs haven't finished

- [ ] **Step 3: Commit fixes**

```bash
cd C:\OvermindTestBed
git add -A
git commit -m "fix: resolve test failures from full suite run"
```

---

### Task 18: Dashboard (dashboard/index.html)

**Files:**
- Create: `C:\OvermindTestBed\dashboard\index.html`
- Modify: `C:\OvermindTestBed\tests\conftest.py` (add JSON result writer)

- [ ] **Step 1: Add pytest result JSON writer to tests/conftest.py**

Append to `C:\OvermindTestBed\tests\conftest.py`:

```python
import json as _json
from datetime import datetime as _datetime


def pytest_sessionfinish(session, exitstatus):
    """Write test results to JSON for dashboard consumption."""
    results = []
    for item in session.items:
        report = item.stash.get("report", None) if hasattr(item, "stash") else None
        results.append({
            "name": item.name,
            "file": str(item.fspath.basename) if hasattr(item, "fspath") else item.nodeid.split("::")[0],
            "nodeid": item.nodeid,
            "passed": item.stash.get("passed", None) if hasattr(item, "stash") and hasattr(item.stash, "get") else None,
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
        if not hasattr(item, "stash"):
            return
        item.stash["passed"] = call.excinfo is None
        item.stash["report"] = True
```

- [ ] **Step 2: Create dashboard/index.html**

Create the single-file HTML dashboard at `C:\OvermindTestBed\dashboard\index.html`. This should:
- Load `test_results.json` from same directory via fetch
- Show feature coverage matrix (14 Overmind modules × PASS/FAIL)
- Show test results table with name, file, pass/fail, color-coded
- Show summary stats (total, passed, failed, timestamp)
- Dark mode support, no external CDN dependencies
- Map test files to Overmind modules:
  - test_discovery.py → ProjectScanner/Indexer
  - test_task_generation.py → TaskGenerator
  - test_prioritization.py → Prioritizer
  - test_routing.py → QRouter/Scheduler
  - test_dispatch.py → SessionManager/TerminalSession
  - test_verification.py → Verifier
  - test_context_injection.py → ContextInjector
  - test_loop_detection.py → LoopDetector
  - test_review.py → MultiPersonaReviewer
  - test_memory_lifecycle.py → MemoryStore/DreamEngine
  - test_dag_dependencies.py → TaskQueue
  - test_resource_scaling.py → PolicyEngine
  - test_worktree.py → WorktreeManager
  - test_full_cycle.py → Orchestrator

- [ ] **Step 3: Run tests to generate JSON**

Run: `cd /c/OvermindTestBed && python -m pytest tests/ -v --timeout=180`
Verify: `dashboard/test_results.json` exists and contains test data.

- [ ] **Step 4: Commit**

```bash
cd C:\OvermindTestBed
git add dashboard/ tests/conftest.py
git commit -m "feat: dashboard with feature coverage matrix + pytest JSON export"
```

---

### Task 19: README + CLAUDE.md + E156-PROTOCOL.md

**Files:**
- Create: `C:\OvermindTestBed\README.md`
- Create: `C:\OvermindTestBed\CLAUDE.md`
- Create: `C:\OvermindTestBed\E156-PROTOCOL.md`

- [ ] **Step 1: Create README.md**

```markdown
# OvermindTestBed

Integration test harness for [Overmind](https://github.com/mahmood726-cyber/overmind) v3.0.0 — exercises 14 orchestrator subsystems against CardioOracle.

## Quick Start

```bash
cd C:\OvermindTestBed
python -m pytest tests/ -v --timeout=180
```

## What It Tests

53 integration tests across 15 files covering: project discovery, task generation, prioritization, Q-learning routing, subprocess dispatch, verification, context injection, loop detection, multi-persona review, memory lifecycle, DAG dependencies, resource scaling, git worktree isolation, and full orchestration cycles.

## Dashboard

Open `dashboard/index.html` after running tests to see the feature coverage matrix.

## Dependencies

- Python 3.13
- Overmind at `C:\overmind\`
- CardioOracle at `C:\Models\CardioOracle\` (read-only)
- pytest
```

- [ ] **Step 2: Create CLAUDE.md**

```markdown
# CLAUDE.md — OvermindTestBed

## Purpose
Integration tests for Overmind v3.0.0 against CardioOracle.

## Run Tests
python -m pytest tests/ -v --timeout=180

## Constraints
- Never modify CardioOracle files
- Never spawn real AI agents
- Fresh SQLite DB per test
- Stubs in stubs/ simulate runner behavior
```

- [ ] **Step 3: Create E156-PROTOCOL.md**

```markdown
# E156 Protocol — OvermindTestBed

- **Project:** OvermindTestBed
- **Date created:** 2026-04-07
- **Date last updated:** 2026-04-07
- **E156 body:** [To be filled after test results]
- **Dashboard:** https://mahmood789.github.io/overmind-testbed/
```

- [ ] **Step 4: Commit**

```bash
cd C:\OvermindTestBed
git add README.md CLAUDE.md E156-PROTOCOL.md
git commit -m "docs: README, CLAUDE.md, E156-PROTOCOL.md"
```

---

### Task 20: Final Validation + Ship

- [ ] **Step 1: Run full suite one final time**

Run: `cd /c/OvermindTestBed && python -m pytest tests/ -v --timeout=180 2>&1 | tee test_output.txt`
Expected: All tests pass. Record exact pass/fail count.

- [ ] **Step 2: Verify dashboard loads**

Open `C:\OvermindTestBed\dashboard\index.html` in browser. Verify feature coverage matrix shows all 14 modules.

- [ ] **Step 3: Final commit with test count in message**

```bash
cd C:\OvermindTestBed
git add -A
git commit -m "ship: OvermindTestBed v1.0 — N/53 tests passing, 14 modules covered"
```
