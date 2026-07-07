# STATE.md

## Current Sprint: T-032 — LaTeX Papers + AI Creation Tools

**Goal**: Enable LaTeX format for papers with a dedicated editor and compile-to-PDF preview. Give the AI assistant tools to create experiments, notebooks, and edit papers directly.

### Priority
Papers exist as metadata (title, abstract, authors) but lack LaTeX body content. The AI reads but cannot create or edit research objects. This sprint adds:
- LaTeX content field on papers
- EditPaper tool for AI
- CreateExperiment and CreateNotebook tools for AI
- Frontend paper detail page with LaTeX editor
- LaTeX compilation endpoint (preview to PDF)

### Plan — 6 steps

1. **Migration + API update**: Add `latex_content TEXT` column to papers table. Update papers CRUD routes to accept/return `latex_content`.

2. **AI — EditPaperTool**: Add tool that lets AI update paper fields (title, abstract, status, latex_content). Register in ask.py.

3. **AI — CreateExperimentTool + CreateNotebookTool**: Add tools that let AI create experiments and notebooks with specified names/projects. Register in ask.py.

4. **Frontend — Papers detail page**: Create `app/dashboard/papers/[id]/page.tsx` with metadata editing, LaTeX source editing (CodeMirror/Monaco-style textarea), citation list.

5. **Frontend — LaTeX compile endpoint**: Create `POST /v1/papers/{id}/compile` that runs `pdflatex` (or external service) and returns PDF URL or compilation errors.

6. **Update tests**: Add tests for new AI tools and compile endpoint.

### Done
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)
