# STATE.md

## Current Sprint: T-038 — Graph Search: Edge-based Result Enrichment

**Goal**: Add graph search capability by creating the `edges` table, implementing graph domain entities, and integrating edge-based traversal into the search service so users can query relationships between research nodes.

### Plan
1. ✅ Step 1: Create Alembic migration for `edge_type` enum and `edges` table
2. ✅ Step 2: Implement domain entities for graph in `domain/graph/`
3. ✅ Step 3: Add graph search to SearchService + API route
4. ✅ Step 4: Seed edge data between existing test nodes
5. ✅ Step 5: Write tests for graph search
6. ✅ Step 6: Run feedback loop (ruff, mypy, pytest) and commit

**Status**: Done

### Done (previous sprints)
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
- **Python SDK offline-first WAL sync**: large feature, ~4-5 sprints
- **Event System consumer health dashboard**: medium, ~1 sprint
- **Dockerfile changes**: protected path (cannot edit)
