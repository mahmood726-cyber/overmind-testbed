"""Test loop detection and intervention triggers."""
from __future__ import annotations

from overmind.parsing.loop_detector import LoopDetector


def test_exact_repeat_detected():
    detector = LoopDetector()
    lines = ["Error: connection refused"] * 5
    assert detector.detect(lines) is True


def test_fingerprint_catches_near_duplicates():
    detector = LoopDetector()
    lines = [
        "Error at 10:30:01 connection refused code 42",
        "Error at 10:30:05 connection refused code 43",
        "Error at 10:30:09 connection refused code 44",
    ]
    assert detector.detect(lines) is True


def test_different_lines_not_flagged():
    detector = LoopDetector()
    lines = [
        "Building project...",
        "Running tests...",
        "Deploying to staging...",
        "Verifying deployment...",
    ]
    assert detector.detect(lines) is False
