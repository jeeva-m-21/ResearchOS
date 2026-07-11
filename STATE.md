# STATE.md

## Current Sprint: T-036 — Enhanced Search (DONE)

**Goal**: Improve search UX with structured suggestion data (showing node type) and highlighted result snippets.

### Results
- **SearchResult** now includes `highlights` field with `ts_headline()`-generated title/description snippets
- **Suggestions** endpoint returns structured objects (`id`, `title`, `node_type`, `similarity`)
- **Frontend** suggestions dropdown shows node type badges + icons; clicking sets query by title
- **Tests**: 75/75 pass (new `test_search_highlights`, updated `test_suggestions`)

### Plan executed
1. ✅ Added `highlights` to SearchResult + `ts_headline()` in `_hydrate`
2. ✅ Changed suggestions endpoint to return structured dicts
3. ✅ Updated frontend types + API client (SuggestionResult, SearchResult.highlights)
4. ✅ Updated suggestions dropdown to show node type badges
5. ✅ Updated tests — all 75 passing

**Status**: Done

### Done (previous sprints)
- T-036 — Enhanced Search: Rich Suggestions + Result Highlighting (75/75)
- T-035 — Inline Block Editing in Frontend (74/74 tests)
- T-034 — AI Chat Session Persistence (74/74 tests)
- T-033 — Import Path Normalization (74/74 tests)
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (available)
- **Graph search**: requires `edges` table (migration + seeding) — ~2-3 sprints
- **Python SDK offline-first WAL sync**: large feature, ~4-5 sprints
- **Event System consumer health dashboard**: medium, ~1 sprint
- **Dockerfile changes**: protected path (cannot edit)
