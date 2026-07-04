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
