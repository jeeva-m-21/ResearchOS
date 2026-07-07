# STATE.md

## Current Sprint: T-031 — Wire AI Tools to Database

**Goal**: All 6 AI assistant tools currently return placeholder strings. Wire them to actually query the database so the AI chat can answer questions about papers, experiments, notebooks, and research objects. Also add paper-specific tools for the new Papers feature.

### Motivation
The Research AI Chat Assistant (T-026) was built with stub tool implementations. Tools like `get_experiment` and `list_notebooks` return placeholder messages saying "Details would be fetched here when DB is available." Users can type research questions but the assistant has no ability to look up real data. This sprint fixes that.

### Plan — 5 steps

1. **Wire SearchTool**: Update `SearchTool` to use the global `db` connection and `SearchService` with real database access. Add proper error handling.

2. **Wire Experiment Tools**: Implement real queries in `GetExperimentTool` (fetch experiment + runs + metrics) and `ListExperimentsTool` (list with project filter).

3. **Wire Notebook Tools**: Implement real queries in `GetNotebookTool` (fetch notebook + blocks + content), `ListNotebooksTool` (list with project filter), and `GetBlockContentTool` (fetch specific block content).

4. **Add Paper Tools**: Create `GetPaperTool` and `ListPapersTool` for querying the new papers feature from the AI assistant.

5. **Update Tests & Verify**: Update tool tests to verify real data is returned. Run full test suite.

### Done
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)
