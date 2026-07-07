# STATE.md

## Current Sprint: T-031 — Wire AI Tools to Database ✅

**Goal**: All 6 AI assistant tools currently return placeholder strings. Wire them to actually query the database so the AI chat can answer questions about papers, experiments, notebooks, and research objects. Also add paper-specific tools for the new Papers feature.

### Done
- ✅ T-031 Step 1 — Wire SearchTool to real database
- ✅ T-031 Step 2 — Wire Experiment Tools (GetExperiment, ListExperiments)
- ✅ T-031 Step 3 — Wire Notebook Tools (GetNotebook, ListNotebooks, GetBlockContent)
- ✅ T-031 Step 4 — Add Paper Tools (GetPaper, ListPapers)
- ✅ T-031 Step 5 — Update Tests & Verify (18/18 passing)
- ✅ T-030 — Research Papers Feature (domain, migration, API, frontend)
- ✅ T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (for future sprints)
- AI chat: persist sessions to database (currently in-memory)
- AI chat: pass db connection from API route to orchestrator
- Notebook block execution frontend improvements
- Search: add autocomplete and graph search
