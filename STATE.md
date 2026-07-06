# STATE.md

## Current Sprint: T-021 — Notebook Block Execution (Frontend)

**Goal**: Add a "Run" button to executable code blocks (python/rust/sql) in the notebook UI, showing execution output in a terminal-like panel.

### Plan
1. Add `Execution` interface + `executeBlock()` + `fetchExecutions()` to `frontend/lib/api/notebooks.ts`
2. Create `frontend/components/notebooks/CodeBlock.tsx` — renders a code block with a Run button + output panel
3. Refactor `BlockRow` in notebook detail page to use `CodeBlock` for executable block types
4. Run feedback loop: tsc --noEmit + npm run build

### In Progress
- (none yet)

### Done
- T-019: Notebook Block CRUD (committed 51ebc89)
- T-020: Notebook Block Execution Backend — domain entities, migration, executor, API endpoints, tests (committed eec8a48)

### Next Steps (after this sprint)
- Artifact storage backend/frontend
- Rust/SQL execution support
