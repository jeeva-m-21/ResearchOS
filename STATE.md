# STATE.md

## Current Sprint: T-034 — AI Chat Session Persistence

**Goal**: Persist AI chat sessions and messages to the database instead of keeping them in-memory. Currently sessions are lost on server restart.

### Plan — 3 steps remaining

1. **Fix orchestrator persistence** — Remove dead in-memory `_sessions` code; call `_save_assistant_message()` to persist assistant responses to DB
2. **Wire DB into API route** — Import `db` from `infrastructure.database` and pass it to `AIOrchestrator` in `ask.py`
3. **Update tests** — Fix `test_orchestrator_persists_session` to not rely on removed `_sessions` attribute; verify DB-backed session creation

### Done (this sprint)
- Step 1: Alembic migration `3c2b1d550efb_add_ai_session_tables.py` — creates `agent_sessions`, `ai_messages`, `tool_calls` tables ✅

### Previous sprints
- T-033 — Import Path Normalization (34 files, 74/74 tests passing)
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (for future sprints)
- Notebook block execution frontend improvements
- Search: add autocomplete and graph search
- Persist `.pth` path fix in Dockerfile to survive rebuilds
- Install texlive in container for full LaTeX PDF compilation
