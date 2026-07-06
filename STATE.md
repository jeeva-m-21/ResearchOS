# STATE.md

## Current Sprint: T-022 — Artifact Storage Backend

**Goal**: Add artifact storage — upload, list, and retrieve files/artifacts linked to experiments and notebooks. MVP uses local filesystem storage.

### Plan
1. Create domain entities (`Artifact`, `ArtifactVersion`) + events (`ArtifactUploaded`)
2. Create Alembic migration for `artifacts` + `artifact_versions` tables
3. Create storage adapter (local filesystem in a configurable directory)
4. Create API endpoints (`POST /v1/artifacts/upload`, `GET /v1/artifacts/`, `GET /v1/artifacts/{id}`)
5. Write tests for artifact CRUD
6. Run feedback loop: ruff + mypy + pytest

### In Progress
- (none yet)

### Done
- T-019: Notebook Block CRUD (committed 51ebc89)
- T-020: Notebook Block Execution Backend (committed eec8a48)
- T-021: Notebook Block Execution Frontend (committed d0b5d44)

### Next Steps (after this sprint)
- Artifact frontend (upload UI, artifact list, download)
- Notebook block editing (update/delete)
- Rust/SQL execution support
