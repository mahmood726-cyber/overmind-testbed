# OvermindTestBed

Integration test harness for Overmind — exercises orchestrator subsystems against CardioOracle.

## Install

```bash
pip install -r requirements.txt    # or just: pip install pytest
```

Overmind itself must be importable on the Python path (it lives in a sibling clone — see *Dependencies* below).

## Run tests

```bash
python -m pytest -q
```

Current count: 94 tests across 17 files, covering project discovery, task generation, prioritization, Q-learning routing, subprocess dispatch, verification, context injection, loop detection, multi-persona review, memory lifecycle, DAG dependencies, resource scaling, git worktree isolation, and full orchestration cycles. `pytest.ini` registers the `tests/` directory as a package.

## Dashboard

Open `dashboard/index.html` after running tests to see the feature coverage matrix.

## Dependencies

- Python 3.13+
- Overmind installed at a sibling location (default `../overmind/`; override via env var if your layout differs)
- CardioOracle test fixture (read-only)
- `pytest` (testing), `pytest-timeout` (optional but recommended)
