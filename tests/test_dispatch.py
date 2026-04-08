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

    # Poll until process exits (up to 10s) instead of fixed sleep
    for _ in range(20):
        time.sleep(0.5)
        observations = manager.collect_output()
        if observations and observations[0].exit_code is not None:
            break
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
