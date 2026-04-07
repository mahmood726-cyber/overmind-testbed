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
