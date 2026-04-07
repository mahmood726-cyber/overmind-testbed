# OvermindTestBed

Integration test harness for Overmind v3.0.0 — exercises 14 orchestrator subsystems against CardioOracle.

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
