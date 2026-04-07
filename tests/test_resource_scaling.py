"""Test concurrency scaling under simulated resource pressure."""
from __future__ import annotations

from overmind.core.policy_engine import PolicyEngine
from overmind.storage.models import MachineHealthSnapshot


def test_normal_resources_two_sessions(policies):
    # cpu=75 > scale_up_cpu_below(70) -> scale-up branch NOT triggered.
    # ram=50 < scale_down_ram_above(85), swap=200 < scale_down_swap_above_mb(1024) -> no scale-down.
    # Falls through to default_active_sessions=2.
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=75.0, ram_percent=50.0, swap_used_mb=200.0,
        active_sessions=0, load_state="normal",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 2


def test_high_ram_scales_down(policies):
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=40.0, ram_percent=90.0, swap_used_mb=200.0,
        active_sessions=2, load_state="stressed",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 1


def test_high_swap_scales_down(policies):
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=40.0, ram_percent=70.0, swap_used_mb=4500.0,
        active_sessions=2, load_state="stressed",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 1


def test_low_cpu_scales_up(policies):
    engine = PolicyEngine(policies)
    health = MachineHealthSnapshot(
        cpu_percent=30.0, ram_percent=40.0, swap_used_mb=100.0,
        active_sessions=1, load_state="healthy",
    )
    result = engine.compute_concurrency(health, available_runners=3)
    assert result == 3
