# ResearchOS — Research Operating System

<p align="center">
  <em>An open-source platform for AI/ML research lifecycle management — experiments, notebooks, papers, AI assistance, and semantic search — built with hexagonal architecture and event-driven design.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-production%20ready-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/postgresql-16%2B-336791" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/next.js-15-000000" alt="Next.js">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Overview](#api-overview)
- [Project Structure](#project-structure)
- [Key Design Decisions](#key-design-decisions)
- [Testing](#testing)
- [Phase 2 Roadmap](#phase-2-roadmap)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

ResearchOS is a unified research operating system for AI/ML researchers and teams. It provides an integrated platform to manage the entire research workflow:

- **Track experiments** with metric logging, parameter management, and run history
- **Compose notebooks** using block-based editing with multi-language execution (Python, Rust, SQL, Mermaid, LaTeX)
- **Write papers** with LaTeX support, citation management, and versioning
- **Search semantically** across all research objects using hybrid vector + keyword search
- **Collaborate** with multi-tenant organization isolation and team projects
- **Automate** with an AI assistant that has tool access to your research data

Built with **Domain-Driven Design** and **Hexagonal Architecture**, ResearchOS is production-ready for self-hosted or SaaS deployment.

---

## Architecture

### Hexagonal (Ports & Adapters) + DDD

```
                    ┌─────────────────────────────────────┐
                    │         PRESENTATION LAYER           │
                    │  Next.js 15  │  FastAPI REST │ WebSocket │
                    └─────────────────────────────────────┘
                                       │
                    ┌─────────────────────────────────────┐
                    │         APPLICATION LAYER             │
                    │  Services, DTOs, Event Handlers       │
                    └─────────────────────────────────────┘
                                       │
                    ┌─────────────────────────────────────┐
                    │           DOMAIN LAYER                │
                    │  Entities, Value Objects, Events,     │
                    │  Repository Interfaces (pure Python)  │
                    └─────────────────────────────────────┘
                                       │
                    ┌─────────────────────────────────────┐
                    │       INFRASTRUCTURE LAYER            │
                    │  PostgreSQL │ Redis │ S3 │ LLM APIs  │
                    └─────────────────────────────────────┘
```

The dependency rule is **absolute**: `api → application → domain`, and infrastructure implements domain interfaces. The domain layer imports **nothing** from outer layers.

### Bounded Contexts

| Context | Purpose | Key Aggregates |
|---------|---------|----------------|
| **Research Graph** | Property-graph data model with typed edges | Node, Edge, Branch, Fork |
| **Experiments** | Experiment lifecycle, metrics, parameters | Experiment, Run, Metric |
| **Notebooks** | Block-based notebooks with independent versioning | Notebook, Block, BlockContent |
| **Papers** | Paper composition with LaTeX and citations | Paper, Citation, Reference |
| **Artifacts** | File storage with versioning and lineage | Artifact, ArtifactVersion |
| **Search** | Hybrid semantic + keyword search (read model) | — |
| **AI** | Multi-agent RAG assistant with tool access | AgentSession, ToolCall |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+ · FastAPI · Pydantic v2 · asyncpg · Alembic |
| **Frontend** | Next.js 15 (App Router) · React 18 · TypeScript · Tailwind CSS · shadcn/ui |
| **Database** | PostgreSQL 16 + pgvector · Redis 7 (Streams + Pub/Sub) |
| **Auth** | JWT (access + refresh tokens) · bcrypt · API keys |
| **AI/ML** | OpenAI · Anthropic · Ollama · text-embedding-3-small · Cohere |
| **Search** | pgvector HNSW · PostgreSQL trigram · BM25 full-text · RRF fusion |
| **Infrastructure** | Docker Compose (dev) · Kubernetes/Helm (production) |
| **Monitoring** | Prometheus · OpenTelemetry · Grafana |
| **SDK** | Python (offline-first with Write-Ahead Log + sync engine) |

---

## Features

### ✅ Authentication & Multi-Tenancy
- JWT-based authentication with refresh tokens
- Organization-scoped data isolation (`organization_id` on every table)
- API key support for SDK integration
- Role-based access (owner, admin, member, viewer)

### ✅ Experiment Tracking
- Full experiment lifecycle: Create → Run → Log Metrics → Complete
- Parameter management with run-level snapshots
- Time-series metric logging with step tracking
- Git commit/branch tracking per run

### ✅ Hybrid Search
- **Semantic** — pgvector HNSW indexes with cosine similarity
- **Keyword** — PostgreSQL `tsvector` full-text search with BM25 ranking
- **Fuzzy** — Trigram matching for typo-tolerant autocomplete
- **Fusion** — Reciprocal Rank Fusion (RRF) for combined ranking
- Result highlighting with `ts_headline()`

### ✅ Notebooks (Domain + API)
- Block-based editing (Markdown, Python, Rust, SQL, Mermaid, LaTeX)
- Independent block versioning (not full notebook snapshots)
- Git-like branching and merging
- Reusable blocks across notebooks
- Execution engine with kernel management

### ✅ Papers (Domain + API + Frontend)
- Paper composition with LaTeX support
- Citation management (BibTeX, APA, MLA, Chicago)
- Version tracking with draft/review/published workflow
- AI-assisted writing tools

### ✅ AI Assistant
- Multi-agent RAG pipeline: Planner → Retriever → Analyst → Writer → Reviewer
- Tools wired to real data: SearchTool, ExperimentTool, NotebookTool, PaperTool
- Persistent chat sessions with full message history
- Database-backed session storage

### ✅ Event System
- Redis Streams for event-driven architecture
- PostgreSQL append-only event store
- Consumer groups for parallel processing (projectors, notifiers, embedders, auditors)
- Dead Letter Queue (DLQ) with retry support
- Idempotent processing via event_id deduplication

### ✅ Python SDK (Offline-First)
- Write-Ahead Log (WAL) for offline durability
- Background sync engine with conflict resolution
- Protocol buffer definitions for efficient transmission
- Full experiment tracking API

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Node.js 18+ (for frontend development)

### 1. Clone and Start

```bash
git clone https://github.com/jeeva-m-21/ResearchOS.git
cd ResearchOS

# Start infrastructure (PostgreSQL 16 + Redis 7)
make docker-up

# or manually:
docker compose up -d postgres redis
```

### 2. Start the Application

```bash
# Start backend server (FastAPI on port 8000)
make dev

# In a separate terminal, start frontend (Next.js on port 3000)
cd frontend && npm run dev
```

### 3. Verify Health

```bash
curl http://localhost:8000/health/
# {"status":"healthy"}
```

### 4. Test Authentication

```bash
# Login with test credentials
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "researcher@test.com", "password": "password123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Verify token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/profile
```

### Test Credentials

| Field | Value |
|-------|-------|
| Email | `researcher@test.com` |
| Password | `password123` |
| Organization | Test Research Lab (`02b5991b-d971-41fc-b257-4ded07d94aac`) |
| Project | Test Project (`90c7cb47-cc1f-472f-99c5-2b17a9e088a8`) |

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make docker-up` | Start Postgres 16 + Redis 7 |
| `make docker-down` | Stop all containers |
| `make dev` | Start full development stack |
| `make test` | Run backend tests + frontend type check |
| `make lint` | Run ruff linter on backend |
| `make typecheck` | Run mypy type checker on backend |
| `make build` | Build frontend for production |

---

## API Overview

### Authentication

```bash
POST /auth/login          # Login → returns access + refresh tokens
POST /auth/refresh        # Refresh access token
POST /auth/logout         # Invalidate refresh token
GET  /auth/profile        # Get current user profile
GET  /auth/organizations  # List user's organizations
POST /auth/api-keys       # Create API key for SDK
```

### Experiment Tracking

```bash
# Full lifecycle
POST   /v1/experiments/                        # Create experiment
GET    /v1/experiments/{exp_id}                 # Get experiment
POST   /v1/experiments/{exp_id}/runs            # Create run
GET    /v1/experiments/{exp_id}/runs            # List runs
POST   /v1/experiments/{exp_id}/runs/{run_id}/metrics   # Log metric
GET    /v1/experiments/{exp_id}/runs/{run_id}/metrics   # Get metrics
POST   /v1/experiments/{exp_id}/runs/{run_id}/complete  # Complete run
```

### Search

```bash
GET    /v1/search?q=<query>                            # Hybrid search
GET    /v1/search/suggestions?q=<query>                # Autocomplete
```

### Notebooks

```bash
POST   /v1/notebooks/                                  # Create notebook
GET    /v1/notebooks/{id}                              # Get notebook
PATCH  /v1/notebooks/{id}/blocks                       # Update blocks
POST   /v1/notebooks/{id}/execute                      # Execute all blocks
POST   /v1/notebooks/{id}/blocks/{block_id}/execute    # Execute single block
```

### Papers

```bash
POST   /v1/papers/                                     # Create paper
GET    /v1/papers/{id}                                 # Get paper
PATCH  /v1/papers/{id}                                 # Update paper
POST   /v1/papers/{id}/compile                         # Compile LaTeX
```

### AI Assistant

```bash
POST   /v1/ask                                         # Ask AI assistant
GET    /v1/ask/sessions                                # List sessions
GET    /v1/ask/sessions/{id}                           # Get session
DELETE /v1/ask/sessions/{id}                           # Delete session
```

---

## Project Structure

```
ResearchOS/
├── backend/                          # FastAPI backend (Python 3.11+)
│   ├── src/
│   │   ├── domain/                   # Domain layer (pure Python, no external deps)
│   │   │   ├── experiments/          # Experiment aggregates, events, repositories
│   │   │   ├── notebooks/            # Notebook aggregates, events, repositories
│   │   │   ├── papers/               # Paper aggregates, events, repositories
│   │   │   ├── artifacts/            # Artifact aggregates, events, repositories
│   │   │   └── shared/               # Value objects, base events, common interfaces
│   │   ├── application/              # Application layer (use-case services)
│   │   │   ├── ai/                   # AI orchestrator, tools, DTOs
│   │   │   ├── search/               # Hybrid search service
│   │   │   ├── experiments/          # Experiment application services
│   │   │   ├── notebooks/            # Notebook application services
│   │   │   └── papers/               # Paper application services
│   │   ├── infrastructure/           # Infrastructure layer (adapters, implementations)
│   │   │   ├── persistence/          # PostgreSQL + Redis implementations
│   │   │   ├── events/               # Event bus (producer, consumer, DLQ, store)
│   │   │   ├── auth/                 # JWT + password hashing
│   │   │   ├── adapters/             # LLM, embeddings, storage adapters
│   │   │   └── workers/              # Background workers
│   │   └── api/                      # Presentation layer (FastAPI routes)
│   │       ├── routes/               # 13 route modules
│   │       ├── dependencies/         # FastAPI dependency injection
│   │       ├── middleware/           # Auth, org isolation middleware
│   │       └── schemas/              # Request/response schemas
│   ├── alembic/                      # Database migrations (immutable)
│   ├── tests/                        # 75+ tests
│   └── pyproject.toml                # Poetry dependencies
│
├── frontend/                         # Next.js 15 (App Router)
│   ├── app/                          # Pages (dashboard, experiments, notebooks, etc.)
│   ├── components/                   # UI components (shadcn/ui, custom)
│   ├── lib/                          # API client, hooks, store (Zustand)
│   └── package.json
│
├── sdk/python/                       # Python SDK (offline-first)
│   ├── researchos/                   # Client, experiment tracking, WAL, sync engine
│   └── pyproject.toml
│
├── docs/                             # 16 architecture documents + ADRs
├── helm/                             # Kubernetes Helm charts
├── infra/terraform/                  # Infrastructure as Code
├── monitoring/                       # Prometheus/Grafana configs
└── docker-compose.yml                # Development services
```

---

## Key Design Decisions

### 1. Property-Graph Data Model
Every research object (experiment, hypothesis, paper, notebook, dataset) is a **node** with typed **edges** in a property graph. This enables traversal queries, version history (git-like DAG), forking, branching, and impact analysis — all within PostgreSQL.

### 2. No Elasticsearch — PostgreSQL Only
Search is powered entirely by PostgreSQL: **pgvector** for semantic search (HNSW indexes), **tsvector** for BM25 full-text, and **pg_trgm** for fuzzy matching. This eliminates operational complexity while meeting the <100ms p99 latency target.

### 3. Event-Driven Architecture with Redis Streams
State changes emit domain events to Redis Streams, which are consumed by parallel consumer groups (projectors, notifiers, embedders, auditors). Events are durably stored in a PostgreSQL append-only log for replay and audit.

### 4. Notebooks ≠ Jupyter
Notebooks use **block-level versioning** instead of full-snapshot versioning. Each block has independent versions, enabling efficient diffs, reusable blocks across notebooks, and git-compatible storage.

### 5. Offline-First SDK
The Python SDK uses a **Write-Ahead Log (WAL)** to ensure durability even offline. Operations are queued locally and synced to the server when connectivity is restored, with conflict resolution.

### 6. Multi-Tenant by Design
Every table carries an `organization_id` with foreign key enforcement. Row-level security (RLS) policies ensure complete data isolation between tenants.

---

## Testing

All Python tooling runs inside Docker containers. Never run Python commands directly on the host.

```bash
# Run all backend tests
docker exec researchos-backend-1 pytest tests/ -v

# Run with coverage
docker exec researchos-backend-1 pytest tests/ --cov

# Lint
docker exec researchos-backend-1 ruff check backend/src/ backend/tests/

# Type check
docker exec researchos-backend-1 mypy backend/src/

# Run specific test file
docker exec researchos-backend-1 pytest tests/test_ecosystem.py -v

# Frontend type check
cd frontend && npx tsc --noEmit
```

**Current test count**: 75+ tests covering:
- Authentication & API keys
- Experiment lifecycle (CRUD, metrics, runs)
- Notebook CRUD + inline editing
- Paper CRUD + LaTeX compilation
- Search (highlights, suggestions, node type badges)
- AI assistant chat sessions
- Event system (producer, consumer, store, DLQ, idempotency)
- Logout flow

---

## Phase 2 Roadmap

| Priority | Feature | Status |
|----------|---------|--------|
| 1 | **Event System** — Redis Streams, consumer groups, DLQ | 🔄 In Progress |
| 2 | **Search** — pgvector embeddings, HNSW, hybrid search | ✅ Enhanced (T-036) |
| 3 | **Notebooks** — Block execution engine + versioning | 🗓️ Planned |
| 4 | **AI Assistant** — RAG pipeline, multi-agent orchestration | 🗓️ Planned |
| 5 | **Python SDK** — Offline-first WAL sync | 🗓️ Planned |
| 6 | **Artifact Storage** — S3/MinIO integration | 🗓️ Planned |
| 7 | **Graph Features** — Research graph traversal | 🗓️ Planned |
| 8 | **Paper Writing** — Citations, LaTeX export | 🗓️ Planned |
| 9 | **Monitoring** — Prometheus, Grafana dashboards | 🗓️ Planned |

---

## Documentation

Comprehensive architecture and design documentation is available in the [`docs/`](./docs) directory:

| Document | Description |
|----------|-------------|
| [01 Architecture](docs/01-high-level-architecture.md) | System architecture, layers, bounded contexts |
| [02 Domain Model](docs/02-domain-model.md) | DDD aggregates, entities, value objects, events |
| [03 Database Schema](docs/03-database-schema.md) | All tables, indexes, partitions, RLS |
| [04 Python SDK](docs/04-python-sdk.md) | SDK design, WAL, sync protocol |
| [05 AI Architecture](docs/05-ai-architecture.md) | RAG pipeline, agent orchestration |
| [06 Search](docs/06-search-architecture.md) | Hybrid search, pgvector, RRF fusion |
| [07 Research Graph](docs/07-research-graph.md) | Graph model, traversal, versioning |
| [08 Notebooks](docs/08-notebook-architecture.md) | Block-based notebooks, execution engine |
| [09 Events](docs/09-event-architecture.md) | Redis Streams, event sourcing, DLQ |
| [10 Deployment](docs/10-deployment-architecture.md) | Production deployment architecture |

---

## Contributing

ResearchOS follows a strict hexagonal architecture with DDD principles. Before contributing:

1. Read the [architecture docs](docs/01-high-level-architecture.md) and [domain model](docs/02-domain-model.md)
2. Respect the **dependency rule**: domain imports nothing from outer layers
3. Follow **one failing test at a time** — make it pass, verify, commit, repeat
4. All Python tooling runs **inside Docker** — never install packages on the host
5. Never modify protected paths (Dockerfiles, compose files, Helm charts, Terraform, CI, existing Alembic migrations)

### Development Workflow

```bash
# 1. Start infrastructure
make docker-up

# 2. Pick a task, plan the change
# 3. Implement with tests (one at a time)
# 4. Run feedback loop: ruff → mypy → pytest
# 5. Commit with descriptive message
# 6. Run evolution cycle
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>ResearchOS</strong> — Accelerating research through better tooling.<br>
  Built with ❤️ for the AI/ML research community.
</p>
