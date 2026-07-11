# STATE.md

## Current Sprint: T-041 — SDK Autolog: System/GPU Metrics Auto-Logging

**Goal**: Create an `autolog` module that automatically captures system metrics (CPU, memory, disk) and GPU metrics (when available) and logs them as experiment metrics via the WAL-backed client. Users get zero-effort system monitoring in their experiments.

**Status**: DONE (13 autolog tests + 16 existing = 29/29 SDK tests green)

### What was implemented
- `researchos/autolog/__init__.py` — package exports (AutoLogger, collect_system_metrics, GPUCollector)
- `researchos/autolog/system.py` — CPU/memory/disk collectors via psutil with `sys/` prefix
- `researchos/autolog/gpu.py` — GPU collector via nvidia-smi with graceful fallback (empty dict if no GPU)
- `researchos/autolog/monitor.py` — `AutoLogger` background thread that polls and logs via callback
- `sdk/python/researchos/__init__.py` — `enable_autolog()`/`disable_autolog()` top-level functions
- `sdk/python/researchos/experiment.py` — `Experiment(autolog=True, autolog_interval=5.0)` support
- `sdk/python/pyproject.toml` — added `psutil>=5.9.0` dependency
- `sdk/python/tests/test_autolog.py` — 13 tests: unit (system/gpu/monitor) + integration (WAL, top-level API, Experiment context manager)

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
- **SDK artifact support**: file hashing + artifact upload events
- **Dockerfile changes**: protected path (cannot edit)
