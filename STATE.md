# STATE.md

## Current Sprint: T-033 — Import Path Normalization

**Goal**: Fix the Python import path duplication bug causing notebook execution records not to be persisted. Normalize all imports to use consistent paths, making all tests pass green.

### Plan — 4 steps

1. **Remove `from src.` prefix** from all imports across `src/` (28 files) — use `sed` inside container
2. **Fix test imports** — update `test_ask.py` and `seed_search_data.py` to remove `src.` prefix
3. **Run full test suite** — verify all 74 tests pass with the fix
4. **Clean up `.pth` fix** — remove the workaround since it's no longer needed

### Done
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (for future sprints)
- AI chat: persist sessions to database (currently in-memory)
- AI chat: pass db connection from API route to orchestrator
- Notebook block execution frontend improvements
- Search: add autocomplete and graph search
- Persist `.pth` path fix in Dockerfile to survive rebuilds
- Install texlive in container for full LaTeX PDF compilation
