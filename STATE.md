# STATE.md

## Current Sprint: T-024 — Notebook Block Content History/Diff

**Goal**: Add history and diff endpoints for notebook blocks. Users can see all versions of a block's content and compare any two versions.

### Plan
1. Add `GET /v1/notebooks/{id}/blocks/{bid}/history` — list all `block_content` entries for a block, ordered by version DESC with `created_at` timestamps and `created_by`
2. Add `GET /v1/notebooks/{id}/blocks/{bid}/diff?v1=X&v2=Y` — compare two versions using `difflib.unified_diff`, return the diff as a list of strings
3. Write tests for history (lists versions, includes metadata) and diff (returns meaningful diff, handles invalid version combos)
4. Run feedback loop: ruff + mypy + pytest

### In Progress
- Step 1-2: Implement history and diff endpoints

### Done
- T-019: Notebook Block CRUD (committed 51ebc89)
- T-020: Notebook Block Execution Backend (committed eec8a48)
- T-021: Notebook Block Execution Frontend (committed d0b5d44)
- T-022: Artifact Storage Backend (committed 43319e2)
- T-023: Notebook Block Editing (Update/Delete) (committed fa954de)

### Next Steps (after this sprint)
- Rust/SQL execution support
- Artifact frontend (upload UI, artifact list, download)
