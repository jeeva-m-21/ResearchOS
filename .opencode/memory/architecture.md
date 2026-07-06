# Architecture Evolution

This file tracks architectural decisions and their outcomes over time.

## Format

```markdown
### YYYY-MM-DD: Title
- **Decision**: What was decided
- **Rationale**: Why
- **Alternatives considered**: What was rejected
- **Outcome**: What happened after implementation
- **Evidence**: Links to commits, tests, metrics
- **Confidence**: High/Medium/Low (retrospective)
```

---

### 2026-07-04: Persistent Learning & Evolution Module
- **Decision**: Adopt a structured repository-owned memory system at `.opencode/memory/` with JSON/Markdown files, an evolution cycle runner at `scripts/learn.py`, and integration into the orchestrator prompt.
- **Rationale**: Previous development had no institutional memory across sessions. Each agent started fresh. The same issues were rediscovered multiple times (e.g., PYTHONPATH fix required re-documentation). A persistent memory system solves this.
- **Alternatives considered**: External database (too much infra), RAG vector store (too complex for current scale), agent-specific memory (lost on context clear).
- **Outcome**: Not yet evaluated.
- **Confidence**: High — the approach mirrors established practices in autonomous coding systems.

### 2026-07-04: Hexagonal Architecture (Ports & Adapters)
- **Decision**: Organize `backend/src/` into `domain/`, `application/`, `infrastructure/`, `api/` layers with strict inward-only dependency rule.
- **Rationale**: DDD-aligned separation of concerns; domain is framework-agnostic; infrastructure is swappable.
- **Alternatives considered**: Flat structure, MVC, microservices.
- **Outcome**: Successfully enforced across all tasks T-001 through T-010. No layer violations found in reviews.
- **Confidence**: High.

### 2026-07-04: Event-Driven Architecture with Redis Streams
- **Decision**: Use Redis Streams for event bus, PostgreSQL for event store (append-only).
- **Rationale**: Lightweight for current scale (<1000 events/sec); Kafka can be swapped in later.
- **Alternatives considered**: Kafka (overkill now), RabbitMQ (no stream replay), NATS.
- **Outcome**: Implemented for experiment lifecycle, DLQ, consumer groups. All 28 tests pass.
- **Confidence**: High.

### 2026-07-06: Block Content Versioning via Immutable BlockContents Table
- **Decision**: Content changes for blocks create new rows in `block_contents` (immutable), while `blocks.current_version` points to the active version.
- **Rationale**: Enables full audit trail per block, rollback to any prior version, and parallel editing without conflicts.
- **Alternatives considered**: JSONB column on blocks table (loses history), single content field with overwrite (no audit).
- **Outcome**: Successfully deployed with T-019. `GET /blocks` joins blocks + block_contents on current_version. All 27 tests pass.
- **Confidence**: High.
