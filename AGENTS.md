# ResearchOS AGENTS.md
> Instructions for AI agents working on the ResearchOS codebase.

## Environment (READ FIRST — do not skip)
This project is already set up. Your job is to work within it, not rebuild it.

- Use the Makefile for everything. It encapsulates the correct environment. Never run pip install, bare pytest, or ad-hoc setup commands.
  - make install — install/sync all dependencies (managed via backend/pyproject.toml). Run this FIRST if anything is missing.
  - make docker-up — start Postgres 16 + Redis 7 (required before running the app or DB-touching tests).
  - make dev — start the dev server.
  - make test — run the test suite.
- If a tool/package seems missing, STOP and run make install. Do NOT install it yourself, do NOT create a venv, do NOT pip install. If make install doesn't fix it, STOP and ask a human.
- NEVER touch the Protected Paths below. Docker, compose, Helm, Terraform, CI, and existing Alembic migrations are production-ready and DONE. If something looks missing or broken there, STOP and ask — do not recreate or fix it.
- After every edit, run the feedback loop before continuing:
  - ruff check backend/ (lint) and mypy backend/src/ (types). Fix all errors before moving on.
- Work in small, reversible steps. One failing test at a time. If a change makes things worse, revert (/undo) instead of stacking more fixes.

### Protected paths — NEVER create, edit, or delete

    Dockerfile, **/Dockerfile, .dockerignore
    docker-compose*.yml, compose*.yml
    helm/**             # Kubernetes charts
    infra/terraform/**  # Infrastructure as code
    .github/**          # CI/CD workflows
    backend/alembic/versions/**   # EXISTING migrations immutable; create NEW ones via alembic revision

## Golden Rules (how every agent must operate)
1. Plan before you build. For anything non-trivial, produce a short written plan and get it approved before editing. Phase 1 is COMPLETE and production-ready — do not refactor working code unless explicitly asked.
2. Smallest change that works. Prefer a 10-line diff that passes one test over a 300-line rewrite. Large diffs defeat type-checking and undo.
3. Green one test at a time. Never write all the code then run all tests. Make one failing test pass, verify, commit, repeat.
4. Always close the feedback loop. ruff + mypy after every edit; run the relevant tests, not the whole suite mid-iteration.
5. Never invent infrastructure. No new Docker/compose/CI files. No new dependency managers. Use what exists.
6. When blocked, STOP and ask. Do not improvise around a failed command — that's how the codebase gets damaged.
7. Respect the layers (see Architecture). Domain never imports from infrastructure or api.

## Quick Start (for agents)
1. Read this file fully, then docs/01-high-level-architecture.md.
2. Check the current task in .opencode/tasks/.
3. Read your role instructions in .opencode/agents/{agent-name}.md.
4. Plan the change and get it approved (Golden Rule #1).
5. Ensure env is ready: make install -> make docker-up.
6. Implement one atomic step; run ruff + mypy + the relevant test.
7. Request review from @reviewer, then commit.

## Current Status (July 3, 2026) — PROTECTED
Phase 1 is COMPLETE and PRODUCTION READY. Treat all Phase 1 code, schema, and infra as protected. Do not modify it to make a Phase 2 feature easier without explicit human approval. Extend, don't rewrite.

### What works (do not break)
1. Authentication & multi-tenancy (JWT, org isolation, sessions)
2. Experiment lifecycle: Create -> Run -> Metric -> Complete
3. Database with foreign keys + constraints (organization_id on every table)
4. API endpoints with validation
5. Health monitoring — 13/15 endpoints healthy, core workflow 100%

### Known minor issues (safe to fix in Phase 2)
- GET /auth/api-keys doesn't exist — use POST /auth/api-keys.
- logout requires a body with refresh_token.

### Phase 2 priorities
Event System (Redis Streams) | Search (pgvector, HNSW, hybrid) | Notebooks (block execution + versioning) | AI Assistant (RAG + multi-agent) | Python SDK (offline-first, WAL sync) | Artifact storage | Graph features | Paper writing | Monitoring.

## Agent Registry & model tiering
Fix from the original setup: don't run every agent on a mid-tier model. Planning/judgment roles (orchestrator, architect, reviewer) should run a stronger model; mechanical implementation can stay on DeepSeek/MiniMax. Mid-tier models need more scaffolding, so give the thinking roles the better brain.

| Agent | Role | Recommended model tier |
|-------|------|------------------------|
| @orchestrator | Eng manager, planning & coordination | Strong (e.g. Claude Sonnet via Bedrock) |
| @architect | Architecture & ADRs | Strong |
| @reviewer | Code review (read-only) | Strong |
| @backend / @db / @sdk / @test | Implementation | DeepSeek V3.2 (low temp, tight guardrails) |
| @frontend / @infra | UI / infra changes | MiniMax M2.5 (infra: read-only + ask on bash) |

Role prompts live in .opencode/agents/{name}.md. @reviewer and @infra should have edit: deny and bash: ask in their permission blocks. On Bedrock, the DeepSeek model ID needs the region inference-profile form (apac.deepseek.v3.2 in ap-south-1).

## Architecture (what agents must respect)
ResearchOS is a Hexagonal (Ports & Adapters) + DDD system. The dependency rule is absolute:
api -> application -> domain, and infrastructure implements domain interfaces. The domain layer imports nothing from application, infrastructure, or api.

    backend/src/
    |-- domain/          # Entities, value objects, events, repository INTERFACES, domain services
    |   |-- experiments/ notebooks/ papers/ artifacts/ graph/ shared/
    |-- application/     # Use-case services, event handlers, DTOs (orchestrates domain)
    |   |-- experiments/ notebooks/ search/ ai/
    |-- infrastructure/  # Repository IMPLEMENTATIONS, adapters, event bus
    |   |-- persistence/ (postgres, redis)  adapters/ (llm, embeddings, storage)  events/ (producer, consumer, dlq)
    |-- api/             # FastAPI routes, dependencies, middleware

### Bounded contexts
| Context | Aggregates |
|---------|------------|
| Research Graph | Node, Edge, Branch, Fork |
| Experiments | Experiment, Run, Metric |
| Notebooks | Notebook, Block, BlockContent |
| Papers | Paper, Citation, Reference |
| Artifacts | Artifact, ArtifactVersion |
| Search | Read model only (no aggregates) |
| AI | AgentSession, ToolCall |

### Key design decisions (don't relitigate these)
- Property-graph model — every research object is a node with typed edges (traversal, versioning, forking, impact analysis).
- Event-driven / CQRS on critical paths (experiments, notebooks): audit trail, replay, temporal queries.
- Hybrid search = PostgreSQL pgvector + trigram. No Elasticsearch — do not add a search engine.
- Notebooks are code, not Jupyter — block-level versioning, reusable blocks, git-compatible storage.
- Multi-tenant — organization_id on every table; enforce org isolation on every query.

### Non-functional targets
Search p99 < 100ms | API p95 < 200ms | 10k concurrent users/tenant | idempotent ops | graceful degradation (offline SDK) | row-level security.

## Development Workflow
### Feature flow
@architect (design/ADR) -> @backend (implement) -> @test (tests) -> @reviewer (approve) -> commit

### Quality gates (all must pass before merge)
- [ ] Tests pass: make test (or cd backend && pytest tests/)
- [ ] Types: mypy backend/src/
- [ ] Lint: ruff check backend/
- [ ] Coverage: pytest --cov (backend)
- [ ] No changes to Protected Paths
- [ ] Layer rule respected (domain imports nothing outward)

## Environment & Commands (make-first)

    # Setup / run (ALWAYS prefer these)
    make install        # Install/sync dependencies (backend/pyproject.toml)
    make docker-up      # Start Postgres 16 + Redis 7
    make dev            # Start dev server (API on http://localhost:8000)
    make test           # Run tests

    # Backend (only if a make target doesn't exist)
    cd backend
    pytest tests/       # Run tests
    pytest --cov        # Coverage
    ruff check src/     # Lint
    mypy src/           # Type check
    alembic revision -m "message"   # Create a NEW migration (never edit existing ones)
    alembic upgrade head            # Apply migrations

    # Frontend
    cd frontend
    npm run dev         # Dev server
    npm test            # Tests
    npm run build       # Build
    tsc --noEmit        # Type check

### Quick verification

    curl http://localhost:8000/health/    # {"status":"healthy"}

## Tech Stack
- Backend: Python 3.11+ | FastAPI | Pydantic v2 | asyncpg (PostgreSQL) | redis-py | Alembic
- Frontend: Next.js 15 (App Router) | React 18 | TypeScript | Tailwind | shadcn/ui | TipTap | xterm.js
- Data: PostgreSQL 16 + pgvector | Redis 7 (Streams/PubSub) | S3-compatible storage (MinIO self-hosted)
- AI/ML: LLM adapters (OpenAI, Anthropic, Ollama) | embeddings (text-embedding-3-small, Cohere, local) | HNSW in pgvector

## Code Conventions
- Python: type hints everywhere | PEP 8 | Pydantic v2 models | async/await for I/O | respect hexagonal boundaries.
- TypeScript: strict mode | Zod for runtime validation | App Router conventions | server components by default.

## Key Documents
| Document | Path |
|----------|------|
| High-level Architecture | docs/01-high-level-architecture.md |
| Domain Model | docs/02-domain-model.md |
| Database Schema | docs/03-database-schema.md |
| Python SDK | docs/04-python-sdk.md |
| AI Architecture | docs/05-ai-architecture.md |
| Search Architecture | docs/06-search-architecture.md |
| Research Graph | docs/07-research-graph.md |
| Notebook Architecture | docs/08-notebook-architecture.md |
| Event Architecture | docs/09-event-architecture.md |
| Deployment | docs/10-deployment-architecture.md |
| Monitoring & DR | docs/15-monitoring-backup-dr.md |
| Architecture Audit | docs/16-architecture-audit.md |
| References | docs/references.bib |

## Testing credentials & secrets
Only non-production TEST credentials belong in this file. Never commit real secrets, API keys, or production connection strings to AGENTS.md or the repo — use env vars / a secrets manager.

    Email: researcher@test.com
    Password: password123
    Organization: Test Research Lab (02b5991b-d971-41fc-b257-4ded07d94aac)
    Project: Test Project (90c7cb47-cc1f-472f-99c5-2b17a9e088a8)