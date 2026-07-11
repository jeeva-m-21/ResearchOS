# STATE.md

## Current Sprint: T-040 — Wire SDK Client to WAL for Offline-First Persistence

**Goal**: Make the Python SDK actually persist events via the Write-Ahead Log and sync them to the backend. Currently `client.py` and `experiment.py` are stubs with TODOs. This sprint wires them to the existing WAL + Syncer and adds the missing utility modules.

### Plan
1. Add `utils/backoff.py` — exponential backoff with jitter for sync retry
2. Add `utils/hash.py` — SHA-256 file hashing for artifact support
3. Rewrite `experiment.py` as a proper context manager that initializes WAL + sync
4. Rewrite `client.py` to wire `init_experiment`, `log_metric`, `log_parameter`, `finish` into WAL persistence + background sync
5. Write tests for the wired client (append to WAL, offset tracking, background sync)
6. Run tests inside Docker and commit

**Status**: Done

### Done (previous sprints)
- T-040 — Wire SDK Client to WAL for Offline-First Persistence (16/16 tests)
- T-039 — Event System Consumer Health Dashboard (Frontend)
- T-038 — Graph Search: Edge-based Result Enrichment (81/81 tests)
- T-037 — Comprehensive README (Mermaid diagrams, ASCII art, full API reference)
- T-036 — Enhanced Search: Rich Suggestions + Result Highlighting (75/75)
- T-035 — Inline Block Editing in Frontend (74/74 tests)
- T-034 — AI Chat Session Persistence (74/74 tests)
- T-033 — Import Path Normalization (74/74 tests)
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (available)
- **SDK autolog modules**: system/GPU metrics auto-logging (next logical slice)
- **SDK artifact support**: file hashing + artifact upload events
- **Dockerfile changes**: protected path (cannot edit)
