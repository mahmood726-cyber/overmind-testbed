# OvermindTestBed Design Spec

**Date:** 2026-04-07
**Status:** APPROVED
**Target:** Overmind v3.0.0 (`C:\overmind\`) against CardioOracle (`C:\Models\CardioOracle\`)

## 1. Purpose

Standalone integration test project that drives Overmind through every major feature against a real research project (CardioOracle). Proves that the orchestrator can discover, task-generate, prioritize, route, dispatch, observe, intervene, verify, learn, and dream — end-to-end — without spawning real AI agents.

Ships as E156 micro-paper + GitHub repo + Pages dashboard.

## 2. Architecture

```
C:\OvermindTestBed\
├── tests/
│   ├── conftest.py              # Shared fixtures: fresh DB, CardioOracle record, runner stubs
│   ├── test_discovery.py        # Overmind scans + indexes CardioOracle correctly
│   ├── test_task_generation.py  # Tasks match CardioOracle profile
│   ├── test_prioritization.py   # Priority scores reflect attributes
│   ├── test_routing.py          # Q-learning + scheduler assignment
│   ├── test_dispatch.py         # Subprocess dispatch with stubbed runners
│   ├── test_verification.py     # verify_command runs real CardioOracle pytest
│   ├── test_context_injection.py # Context includes memories + heuristics
│   ├── test_loop_detection.py   # Synthetic loops trigger intervention
│   ├── test_review.py           # Multi-persona review + cross-model dispatch
│   ├── test_memory_lifecycle.py # Extract → store → dream → consolidate → recall
│   ├── test_dag_dependencies.py # Chained build→test→review unblocking
│   ├── test_resource_scaling.py # Concurrency under simulated pressure
│   ├── test_worktree.py         # Git worktree creation + cleanup
│   └── test_full_cycle.py       # End-to-end run_once smoke test
├── stubs/
│   ├── echo_runner.py           # Prints RESULT: SUCCESS, exits 0
│   ├── loop_runner.py           # Repeats same line 5x, exits 1
│   └── slow_runner.py           # Sleeps configurable seconds, exits 0
├── dashboard/
│   └── index.html               # Feature coverage matrix + results
├── conftest.py                  # Root: adds C:\overmind to sys.path
├── pytest.ini                   # Test config
├── README.md
├── CLAUDE.md
└── E156-PROTOCOL.md
```

## 3. Design Decisions

### 3.1 Fresh DB per test
Each test gets a temporary SQLite database via `tmp_path` fixture. No cross-test contamination. The `seeded_db` fixture pre-populates with a CardioOracle project record and sample memories.

### 3.2 Real CardioOracle path, read-only
Tests scan the actual `C:\Models\CardioOracle\` directory for project discovery — this proves Overmind's scanner works against real file structures. Tests never modify CardioOracle files.

### 3.3 Stubbed runners for dispatch
Instead of spawning Claude/Codex/Gemini (expensive, nondeterministic, requires API keys), three Python stub scripts simulate runner behavior:

- **echo_runner.py** — Reads prompt from stdin, prints `RESULT: SUCCESS` + `EVIDENCE: all tests passed`, exits 0. Simulates well-behaved agent.
- **loop_runner.py** — Prints identical error line 5 times with 0.1s delay, exits 1. Triggers loop detection.
- **slow_runner.py** — Sleeps for N seconds (default 15, configurable via argv), exits 0. Triggers idle timeout.

All invoked via `python stubs/X.py` — same subprocess path as real runners.

### 3.4 One real verification test
`test_verification.py` runs CardioOracle's actual `pytest tests/test_curation.py` (~6 seconds) to prove verify_command works end-to-end. This is the only test that touches a real test suite.

### 3.5 Resource scaling via mocked psutil
`test_resource_scaling.py` patches `psutil.virtual_memory()` and `psutil.swap_memory()` to return simulated pressure values. Tests that Overmind scales concurrency down without actually stressing the machine.

## 4. Test Coverage Matrix

| File | Overmind Module | Tests | Description |
|------|----------------|-------|-------------|
| test_discovery.py | ProjectScanner, Indexer | 4 | Detects CardioOracle as python_tool, high-risk, advanced_math; finds test commands; correct tech stack |
| test_task_generation.py | TaskGenerator | 4 | Generates tests-first tasks for math project; verify_command populated; no duplicates on re-run; correct task_type |
| test_prioritization.py | Prioritizer | 3 | browser_tests boost, numeric_logic boost, advanced_math boost with cap |
| test_routing.py | QRouter, Scheduler | 5 | Q-scores update on win/loss; Claude preferred for high-risk; Codex for tests; Laplace smoothing; scheduler respects Q |
| test_dispatch.py | SessionManager, TerminalSession | 4 | echo_runner spawns/exits clean; output captured; exit code propagated; INTERACTIVE protocol stdin open |
| test_verification.py | Verifier, verify_command | 3 | Real pytest run; parses pass count; returns success=True |
| test_context_injection.py | ContextInjector | 4 | Builds context with header; includes heuristics; includes Q-scores; no crash on empty DB |
| test_loop_detection.py | LoopDetector, interventions | 3 | loop_runner triggers detection; intervention message sent; fingerprint catches near-duplicates |
| test_review.py | MultiPersonaReviewer | 4 | 5 personas for high-risk math; cross-model dispatch; consensus from mock outputs; parse_review_output |
| test_memory_lifecycle.py | MemoryStore, DreamEngine | 5 | Save → recall by project → dream merges duplicates → prune stale → FTS5 search |
| test_dag_dependencies.py | TaskQueue | 4 | Build queued; test blocked; build completes → test unblocks; circular dependency handled |
| test_resource_scaling.py | PolicyEngine | 4 | Normal → 2 sessions; high RAM → 1; high swap → 1; recovery when freed |
| test_worktree.py | WorktreeManager | 3 | Creates worktree; detects concurrent need; cleanup removes worktree |
| test_full_cycle.py | Orchestrator.run_once | 3 | Dry-run returns would_dispatch; live cycle completes; memories extracted after |
| **Total** | **14 modules** | **53** | |

## 5. Fixtures

### Root conftest.py
Adds `C:\overmind` to `sys.path` so Overmind imports resolve.

### tests/conftest.py

**fresh_db** (function scope)
- Creates tmp SQLite DB with all Overmind tables
- Yields `StateDatabase`
- Deletes file after test

**cardiooracle_project** (session scope)
- Runs Overmind's `ProjectScanner` against `C:\Models\CardioOracle\` once
- Returns `ProjectRecord` with all detected attributes
- Read-only — never modifies CardioOracle

**seeded_db** (function scope)
- `fresh_db` + CardioOracle project record inserted
- 3 sample memories: heuristic, decision, audit_snapshot
- Q-router history: 2 wins, 1 loss for claude/verification

**stub_runners** (session scope)
- Returns `dict[str, RunnerRecord]` pointing to stub scripts:
  - `claude_stub` → `echo_runner.py`
  - `codex_stub` → `echo_runner.py`
  - `loop_stub` → `loop_runner.py`
  - `slow_stub` → `slow_runner.py`

**orchestrator** (function scope)
- Wired `Orchestrator` with real Overmind modules but stubbed runners
- Uses `seeded_db`, policies from `C:\overmind\config\`

## 6. Dashboard

Single-file `dashboard/index.html`:
- **Feature coverage matrix** — 14 Overmind features as rows, PASS/FAIL/SKIP columns, color-coded
- **Test results table** — 53 tests with name, duration, pass/fail, module exercised
- **Timeline** — Pass rate trend over runs
- **Resource monitor** — Simulated scaling scenarios and Overmind's decisions

Reads `test_results.json` generated by pytest conftest after each run. Fully offline, no CDN.

## 7. E156 Entry

- **S1:** Can an always-on agent orchestrator reliably manage multi-model dispatch, verification, and memory consolidation against a real cardiovascular research project?
- **S2:** 53 integration tests exercising 14 Overmind v3.0.0 subsystems against CardioOracle, a 784-trial CV trial outcome predictor with Bayesian ensemble and L2 meta-regression.
- **S3:** Pytest harness with stubbed runners (echo, loop, slow), fresh SQLite per test, one real verification via CardioOracle's 30-test curation suite.
- **S4:** [Results after implementation]
- **S5:** [Robustness after implementation]
- **S6:** [Interpretation after implementation]
- **S7:** [Limitations after implementation]

## 8. Runtime Estimate

- 52 tests with stubs: ~20 seconds (subprocess spawn + DB ops)
- 1 test with real pytest: ~6 seconds
- Dashboard generation: ~1 second
- **Total: ~30 seconds**

## 9. Constraints

- Never modify CardioOracle files
- Never spawn real AI agents (Claude/Codex/Gemini)
- Never require API keys or network access
- All tests deterministic (fixed seeds where randomness involved)
- Single-threaded test execution (avoid Chrome port conflicts per testing.md)
