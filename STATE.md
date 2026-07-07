# STATE.md

## Current Sprint: T-032 — LaTeX Papers + AI Creation Tools ✅

**Goal**: Enable LaTeX format for papers with a dedicated editor and compile-to-PDF preview. Give the AI assistant tools to create experiments, notebooks, and edit papers directly.

### Plan — 6 steps ✅ ALL DONE

1. ✅ **Migration + API update**: Add `latex_content TEXT` column to papers table. Update papers CRUD routes to accept/return `latex_content`.

2. ✅ **AI — EditPaperTool**: Add tool that lets AI update paper fields (title, abstract, status, latex_content). Register in ask.py.

3. ✅ **AI — CreateExperimentTool + CreateNotebookTool**: Add tools that let AI create experiments and notebooks with specified names/projects. Register in ask.py.

4. ✅ **Frontend — Papers detail page**: Create `app/dashboard/papers/[id]/page.tsx` with metadata editing, LaTeX source editing (CodeMirror), citation list.

5. ✅ **Frontend — LaTeX compile endpoint**: Create `POST /v1/papers/{id}/compile` that runs `pdflatex` (or returns setup instructions).

6. ✅ **Update tests**: Add tests for new AI tools and compile endpoint. 74/74 passing.

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
