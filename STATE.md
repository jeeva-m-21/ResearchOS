# STATE.md

## Current Sprint: Notebook Block CRUD (Backend + Frontend)

**Goal**: Build CRUD endpoints for notebook blocks, wire them into the frontend to replace mock blocks.

### State: ALL DONE — committed

### Done

#### Backend
- `GET /v1/notebooks/{notebook_id}/blocks` — list blocks with current content
- `POST /v1/notebooks/{notebook_id}/blocks` — create block (type, content, language, position)
- `GET /v1/notebooks/{notebook_id}/blocks/{block_id}` — get single block
- Alembic migration `2a8f9c1e3d5b` adds `block_contents` table
- 3 new tests: `test_create_block`, `test_list_blocks`, `test_get_block`

#### Frontend
- `lib/api/notebooks.ts`: `Block` type, `fetchBlocks()`, `createBlock()`, `fetchBlock()`
- `app/dashboard/notebooks/[id]/page.tsx`: Replaced `MOCK_BLOCKS` with real `fetchBlocks()` query; enabled "Add Block" button with `CreateBlockDialog` (block-type picker + content editor)
- Installed shadcn components: `label`, `select`, `textarea`

#### Quality gates
- ✅ ruff + mypy clean (my files)
- ✅ 27/27 tests pass
- ✅ tsc --noEmit clean
- ✅ npm run build succeeds

### Next Steps
- Notebook block execution (run Python/Rust/SQL blocks)
- Project detail page
- "All projects" view in dashboard
