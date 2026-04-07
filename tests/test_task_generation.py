"""Test that Overmind generates correct tasks for CardioOracle."""
from __future__ import annotations

from overmind.tasks.task_generator import TaskGenerator


def test_generates_test_first_tasks(seeded_db, cardiooracle_project):
    """CardioOracle has advanced_math + test_commands -> tests-first pair."""
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    assert len(tasks) == 2
    types = {t.task_type for t in tasks}
    assert "test_writing" in types
    assert "implementation" in types


def test_impl_task_has_verify_command(seeded_db, cardiooracle_project):
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    impl_task = [t for t in tasks if t.task_type == "implementation"][0]
    assert impl_task.verify_command is not None
    assert "pytest" in impl_task.verify_command or "test" in impl_task.verify_command


def test_no_duplicates_on_rerun(seeded_db, cardiooracle_project):
    generator = TaskGenerator()
    first_run = generator.generate([cardiooracle_project], [])
    second_run = generator.generate([cardiooracle_project], first_run)
    assert len(second_run) == 0


def test_impl_blocked_by_test_task(seeded_db, cardiooracle_project):
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    test_task = [t for t in tasks if t.task_type == "test_writing"][0]
    impl_task = [t for t in tasks if t.task_type == "implementation"][0]
    assert test_task.task_id in impl_task.blocked_by
