# STATE.md

## Current Sprint: T-036 — Enhanced Search: Rich Suggestions + Result Highlighting

**Goal**: Improve search UX with structured suggestion data (showing node type) and highlighted result snippets.

### Plan

1. **Add `highlights` to SearchResult backend model** — Add `highlights` field to `SearchResult` dataclass; modify `_hydrate` to use `ts_headline()` for highlighted title/description snippets
2. **Improve suggestions endpoint to return structured data** — Change `/v1/search/suggestions` from `list[str]` to `list[dict]` with `title`, `node_type`, `id`, `similarity`
3. **Update frontend types + API client** — Add `SuggestionResult` interface, update `fetchSuggestions()`, add `highlights` to `SearchResult`
4. **Update frontend suggestions dropdown** — Show node type badge + icon per suggestion; clicking searches for that title
5. **Update tests** — Update `test_suggestions` for new shape; add `test_search_highlights`

**Status**: Planning

### Done (previous sprints)
- T-035 — Inline Block Editing in Frontend (74/74 tests)
- T-034 — AI Chat Session Persistence (74/74 tests)
- T-033 — Import Path Normalization (74/74 tests)
- T-032 — LaTeX Papers + AI Creation Tools (all 6 steps)
- T-031 — Wire AI Tools to Database (SearchTool, Experiment, Notebook, Paper tools)
- T-030 — Research Papers Feature (domain, migration, API, frontend)
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next priorities (blocked/larger scope)
- Search autocomplete: depends on T-036 (enhanced from basic)
- Graph search: requires edges table (migration + seeding)
- Dockerfile changes: protected path (cannot edit)
