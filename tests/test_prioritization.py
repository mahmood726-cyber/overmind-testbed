"""Test that Overmind prioritizes CardioOracle tasks correctly."""
from __future__ import annotations

from overmind.tasks.prioritizer import Prioritizer
from overmind.tasks.task_generator import TaskGenerator


def test_browser_tests_boost(seeded_db, cardiooracle_project):
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    for task in prioritized:
        assert task.priority > 0.5


def test_numeric_logic_boost(seeded_db, cardiooracle_project):
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    if cardiooracle_project.has_numeric_logic:
        for task in prioritized:
            assert task.priority >= 0.7


def test_priority_capped_at_099(seeded_db, cardiooracle_project):
    prioritizer = Prioritizer()
    generator = TaskGenerator()
    tasks = generator.generate([cardiooracle_project], [])
    project_map = {cardiooracle_project.project_id: cardiooracle_project}
    prioritized = prioritizer.reprioritize(tasks, project_map)
    for task in prioritized:
        assert task.priority <= 0.99
