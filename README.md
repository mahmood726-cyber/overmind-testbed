# OvermindTestBed

[![ci](https://github.com/mahmood726-cyber/overmind-testbed/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mahmood726-cyber/overmind-testbed/actions/workflows/ci.yml) [![codeql](https://github.com/mahmood726-cyber/overmind-testbed/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/mahmood726-cyber/overmind-testbed/actions/workflows/codeql.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

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
