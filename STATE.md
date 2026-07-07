# STATE.md

## Current Sprint: T-030 — Research Papers Feature

**Goal**: Build a complete Papers feature — domain entities, database schema, API routes, and frontend UI for writing and managing research papers with citation support.

### Priority
Papers are the most impactful missing feature in ResearchOS. The platform already has experiments, notebooks, and artifacts — but papers are the primary output of research. This sprint adds:
- Paper CRUD (title, abstract, status, DOI, arXiv ID)
- Citation management (internal + external)
- Reference tracking (where citations are used)
- Frontend list + detail pages

### Plan — 6 steps

1. **Domain Layer**: Create `domain/papers/entities.py` (Paper, Citation, Reference with status transitions), update `events.py` (PaperCreated, PaperDeleted, CitationAdded), create `repositories.py` interfaces.

2. **Alembic Migration**: Create new migration for `papers`, `citations`, and `references` tables.

3. **API Routes**: Create `api/routes/papers.py` with full CRUD — create paper, list papers, get paper, update paper, delete paper, add citation, remove citation, list citations. Register router.

4. **Frontend API Client**: Create `lib/api/papers.ts` with all API functions + TypeScript interfaces.

5. **Frontend List Page**: Replace placeholder `app/dashboard/papers/page.tsx` with full list view (status badges, create dialog, search/filter, empty states, loading skeletons).

6. **Frontend Detail Page**: Create `app/dashboard/papers/[id]/page.tsx` with paper metadata, edit capabilities, citation list, and AI summary block support.

### Wire AI Tools (follow-up)
After Papers is committed, wire the AI tools to actually query the database so the chat can answer questions about papers, experiments, and notebooks.

### Commit uncommitted Settings (quick win)
The Settings module (connection configs + API key management) is complete but uncommitted. Will commit it first.

### Done
- T-026 — Research AI Chat Assistant (backend + frontend + tests)
- T-030 Step 1 — Papers domain layer (entities, events, repositories)
- T-030 Step 2 — Papers migration
- T-030 Step 3 — Papers API routes
- T-030 Step 4 — Frontend API client
- T-030 Step 5 — Frontend list page
- T-030 Step 6 — Frontend detail page
