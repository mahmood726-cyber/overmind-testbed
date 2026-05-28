from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def _candidate_drives() -> list[str]:
    drives: list[str] = []
    for drive in (REPO_ROOT.drive, Path.home().drive, "F:", "C:", "D:"):
        if drive and drive not in drives:
            drives.append(drive)
    return drives


def _roots_for(*parts: str) -> list[Path]:
    return [Path(f"{drive}\\").joinpath(*parts) for drive in _candidate_drives()]


def resolve_overmind_root() -> Path:
    candidates = []
    env_root = os.environ.get("OVERMIND_ROOT", "")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend([REPO_ROOT.parent / "overmind", *_roots_for("overmind")])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Overmind root not found. Set OVERMIND_ROOT or restore one of: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def resolve_cardiooracle_root() -> Path:
    candidates = []
    env_root = os.environ.get("CARDIOORACLE_ROOT", "")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend([
        REPO_ROOT.parent / "Models" / "CardioOracle",
        REPO_ROOT.parent / "Projects" / "CardioOracle",
        *_roots_for("Models", "CardioOracle"),
        *_roots_for("Projects", "CardioOracle"),
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "CardioOracle root not found. Set CARDIOORACLE_ROOT or restore one of: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def fixture_root(name: str = "test-root") -> str:
    return str((REPO_ROOT / name).resolve())
