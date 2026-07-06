# Decision Log

Every significant decision is recorded with context, rationale, and outcome.

## Format

```markdown
### YYYY-MM-DD: Title
- **Context**: Situation that prompted the decision
- **Decision**: What was chosen
- **Rationale**: Why this option over others
- **Rejected**: What was explicitly not chosen and why
- **Consequences**: What happened as a result
- **Related**: Links to files, commits, tasks
```

---

### 2026-07-04: PYTHONPATH Fix via .pth File
- **Context**: `docker-compose.yml` sets `PYTHONPATH=/app/src`, but Python needs `/app` in sys.path to resolve `from src.xxx import yyy`. Cannot modify docker-compose.yml (protected path).
- **Decision**: Create `/usr/local/lib/python3.11/site-packages/researchos_pathfix.pth` containing `/app`.
- **Rationale**: `.pth` files are the standard Python mechanism for adding paths to sys.path. Zero code changes. Survives container restarts.
- **Rejected**: Modifying docker-compose.yml (protected), per-script sys.path hack (fragile), symlink in backend/ (breaks on rebuild).
- **Consequences**: All scripts can now `from src.xxx import yyy` without workarounds.
- **Confidence**: High.

### 2026-07-04: SDK Syncer Converts Events to DomainEvent Format
- **Context**: SDK `BaseEvent` has different fields than backend `DomainEvent`. The batch endpoint expects `DomainEvent`.
- **Decision**: `Syncer._convert_to_domain_event()` maps SDK event fields to DomainEvent-compatible dicts before POSTing.
- **Rationale**: Backend endpoint already exists and is tested. Adding a new endpoint is more work and more surface area to maintain.
- **Rejected**: New endpoint accepting SDK format (more code, more testing), embedding SDK in backend (coupling).
- **Consequences**: SDK sync works with existing infrastructure. 28 tests pass.
- **Confidence**: High.

### 2026-07-04: Agent Prompts Are Repository-Owned
- **Context**: `.opencode/agents/*.md` files control agent behavior. Earlier sessions used `:feedback <path>` which no longer works.
- **Decision**: All agent prompts are owned by the repository. They are reviewed, versioned, and improved like source code.
- **Rationale**: Prompt quality directly impacts development velocity. Version history allows rollback.
- **Rejected**: Prompts as external files (lost, out of sync).
- **Consequences**: Orchestrator/backend/reviewer prompts optimized with explicit commands.
- **Confidence**: High.

### 2026-07-06: Notebook Block CRUD via Nested Router Paths
- **Context**: Notebooks router already existed with create/list/get. Blocks needed their own sub-endpoints under `/v1/notebooks/{id}/blocks/`.
- **Decision**: Added block endpoints directly to the existing `notebooks.py` router using path parameters, rather than creating a separate blocks router.
- **Rationale**: Blocks are owned by notebooks (not an aggregate root). Keeping endpoints co-located reduces imports and keeps the domain boundary clear. Same pattern as `experiments/{id}/runs`.
- **Rejected**: Separate `blocks.py` router (extra file, extra imports for auth deps).
- **Consequences**: Clean, discoverable API. All 6 notebook tests pass. Frontend API mirrors the URL structure.
- **Confidence**: High.

### 2026-07-06: Frontend Block State Via React Query (Not Zustand)
- **Context**: Blocks are per-notebook, fetched on detail page mount. No global block state is needed.
- **Decision**: Use `useQuery(['blocks', notebookId], ...)` local to the detail page instead of adding block state to Zustand store.
- **Rationale**: Block data is scoped to one notebook view. Zustand is reserved for cross-page state (auth, project). React Query handles caching/invalidation naturally.
- **Rejected**: Zustand block store (global state unnecessary), plain fetch + useState (no cache invalidation).
- **Consequences**: "Add Block" mutation invalidates the blocks query key, triggering refetch. Clean separation of concerns.
- **Confidence**: High.

### 2026-07-06: shadcn Components Added Per-Need Rather Than Bulk
- **Context**: The CreateBlockDialog needed Select, Label, and Textarea components from shadcn.
- **Decision**: Install each shadcn component individually via `npx shadcn@latest add <component>` as needed.
- **Rationale**: shadcn installs component source code into the project. Bulk-installing unused components creates dead code and maintenance burden.
- **Rejected**: Bulk install of common components (dead code), hand-rolling components (unnecessary effort).
- **Consequences**: Three new component files in `frontend/components/ui/`. Zero unused imports. Build still passes.
- **Confidence**: High.
