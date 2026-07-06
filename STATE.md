# STATE.md

## Current Sprint: T-023 — Notebook Block Editing (Update/Delete)

**Goal**: Add PUT and DELETE endpoints for notebook blocks. Blocks are versioned — updating creates a new `block_content` entry with incremented version number. Deleting sets `deleted_at` (soft delete).

### Result
✅ All 34 tests pass (10 notebook tests, 2 new)
✅ ruff + mypy clean
✅ Committed

### Done
- T-019: Notebook Block CRUD (committed 51ebc89)
- T-020: Notebook Block Execution Backend (committed eec8a48)
- T-021: Notebook Block Execution Frontend (committed d0b5d44)
- T-022: Artifact Storage Backend (committed 43319e2)
- **T-023: Notebook Block Editing (Update/Delete)** ✅

### Next Steps
- Notebook block content history/diff endpoint
- Rust/SQL execution support
- Artifact frontend (upload UI, artifact list, download)
