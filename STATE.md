# STATE.md

## Current Sprint: T-035 — Inline Block Editing in Frontend

**Goal**: Allow users to edit block content inline (without delete+recreate) and view execution history directly in the notebook detail page.

### Plan — 3 steps

1. **Add `updateBlock` to frontend API client** — Add the `updateBlock()` function and an `UpdateBlockData` type to `frontend/lib/api/notebooks.ts`
2. **Add inline edit mode to BlockRow** — Toggle between read-only display and edit mode with a textarea for non-executable blocks; add save/cancel buttons
3. **Add edit mode + execution history to CodeBlock** — Add inline editing and an execution history toggle for executable blocks (python, rust, sql)

### Done (previous sprints)
- T-034 — AI Chat Session Persistence (74/74 tests)
- T-033 — Import Path Normalization (74/74 tests)
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (for future sprints)
- Search: add autocomplete and graph search
- Persist `.pth` path fix in Dockerfile to survive rebuilds (blocked by protected path)
- Install texlive in container for full LaTeX PDF compilation (blocked by protected path)
