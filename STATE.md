# STATE.md

## Current Sprint: T-039 — Event System Consumer Health Dashboard

**Goal**: Build a frontend dashboard for monitoring the event system health, consumer group status, stream statistics, and dead letter queue management. Backend endpoints already exist; the missing piece is the UI.

### Plan
1. Create frontend API client (`frontend/lib/api/events.ts`) for events endpoints (health, stats, consumer health, DLQ retry, event types)
2. Build events dashboard page at `frontend/app/dashboard/events/page.tsx` with:
   - Overall system health card (status, uptime indicators)
   - Consumer group health cards per group (projectors, notifiers, embedders, auditors)
   - Stream statistics (event count, rate, lag)
   - Event type listing
   - DLQ retry buttons
3. Add "Events" nav item to sidebar in `layout.tsx`
4. Verify with `npx tsc --noEmit` and `npm run build`
5. Commit and push

**Status**: In Progress

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
- **Dockerfile changes**: protected path (cannot edit)
