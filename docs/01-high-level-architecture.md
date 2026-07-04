# ResearchOS - High-Level Architecture

## Overview

ResearchOS is a research operating system designed for AI/ML researchers. It provides a unified platform for managing research workflows through a graph-based data model, multi-agent AI assistance, semantic search, and block-based notebooks.

## Design Philosophy

### Core Principles

1. **Graph-Centric**: Every research object (idea, hypothesis, experiment, paper, dataset) is a node in a property graph
2. **Event-Driven**: State changes emit events; supports CQRS, replay, and audit trails
3. **API-First**: Every feature accessible via REST API
4. **Multi-Tenant**: SaaS deployment with organization-level isolation
5. **Plugin Architecture**: Extensible through adapters and plugins
6. **Offline-First SDK**: Python SDK with WAL-style durability and sync

### Target Users

- AI/ML researchers
- Research teams (collaborative features)
- Self-hosted deployments (enterprises, universities)

---

## System Architecture

### Hexagonal Architecture (Ports & Adapters)

```
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                           PRESENTATION LAYER                         │
                    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
                    │  │  Next.js 15  │  │   REST API   │  │  WebSocket   │              │
                    │  │   Frontend   │  │   (FastAPI)  │  │   Server     │              │
                    │  └──────────────┘  └──────────────┘  └──────────────┘              │
                    └─────────────────────────────────────────────────────────────────────┘
                                                      │
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                           APPLICATION LAYER                           │
                    │  ┌────────────────────────────────────────────────────────────────┐ │
                    │  │                     Application Services                       │ │
                    │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
                    │  │  │ Experiment   │  │  Notebook    │  │   Search     │        │ │
                    │  │  │ Service      │  │  Service     │  │   Service    │        │ │
                    │  │  └──────────────┘  └──────────────┘  └──────────────┘        │ │
                    │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
                    │  │  │ Research     │  │   Paper      │  │  Artifact    │        │ │
                    │  │  │ Graph Service │  │  Service     │  │  Service     │        │ │
                    │  │  └──────────────┘  └──────────────┘  └──────────────┘        │ │
                    │  └────────────────────────────────────────────────────────────────┘ │
                    │  ┌────────────────────────────────────────────────────────────────┐ │
                    │  │                      AI Agent Orchestrator                     │ │
                    │  │  ┌──────────────────────────────────────────────────────────┐ │ │
                    │  │  │  Planner → Retriever → Analyst → Writer → Reviewer      │ │ │
                    │  │  └──────────────────────────────────────────────────────────┘ │ │
                    │  └────────────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────────────┘
                                                      │
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                              DOMAIN LAYER                             │
                    │  ┌────────────────────────────────────────────────────────────────┐ │
                    │  │                      Domain Entities                            │ │
                    │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │ │
                    │  │  │ Experiment │  │ Hypothesis │  │ Notebook   │              │ │
                    │  │  │  (Aggregate)│  │            │  │  (Aggregate)│              │ │
                    │  │  └────────────┘  └────────────┘  └────────────┘              │ │
                    │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │ │
                    │  │  │ Paper      │  │ Artifact   │  │ Metric    │              │ │
                    │  │  │(Aggregate) │  │            │  │            │              │ │
                    │  │  └────────────┘  └────────────┘  └────────────┘              │ │
                    │  └────────────────────────────────────────────────────────────────┘ │
                    │  ┌────────────────────────────────────────────────────────────────┐ │
                    │  │                    Domain Events                               │ │
                    │  │  ExperimentStarted │ MetricLogged │ ArtifactUploaded           │ │
                    │  └────────────────────────────────────────────────────────────────┘ │
                    │  ┌────────────────────────────────────────────────────────────────┐ │
                    │  │                  Repository Interfaces                         │ │
                    │  │  IExperimentRepository │ INotebookRepository │ IGraphRepository │ │
                    │  └────────────────────────────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────────────────────────────┘
                                                      │
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                          INFRASTRUCTURE LAYER                         │
                    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
                    │  │  PostgreSQL  │  │    Redis     │  │Object Storage│              │
                    │  │  + pgvector  │  │   Streams    │  │   (S3/MinIO) │              │
                    │  └──────────────┘  └──────────────┘  └──────────────┘              │
                    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
                    │  │ LLM Adapters │  │Embedding     │  │ Git Service  │              │
                    │  │(OpenAI,etc)  │  │Adapters      │  │              │              │
                    │  └──────────────┘  └──────────────┘  └──────────────┘              │
                    └─────────────────────────────────────────────────────────────────────┘
```

---

## Bounded Contexts

### Core Contexts

| Context | Purpose | Aggregates |
|---------|---------|------------|
| **Research Graph** | Core graph operations, node/edge management, versioning | Node, Edge, Branch, Fork |
| **Experiments** | Experiment lifecycle, metrics, parameters | Experiment, Run, Metric |
| **Notebooks** | Block-based notebook creation and execution | Notebook, Block, BlockContent |
| **Papers** | Paper composition, citations, references | Paper, Citation, Reference |
| **Artifacts** | File storage, versioning, lineage | Artifact, ArtifactVersion |
| **Search** | Semantic + keyword search across all entities | (No aggregates - read model) |
| **AI** | Multi-agent orchestration, RAG, tools | AgentSession, ToolCall |

### Shared Kernel

- Event definitions
- Value objects (OrganizationId, UserId, Timestamps)
- Common interfaces

---

## Technology Stack

### Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Architecture**: Hexagonal with DDD
- **Validation**: Pydantic v2
- **Async**: asyncio, asyncpg

### Frontend

- **Framework**: Next.js 15 (App Router)
- **UI**: React 18, TypeScript
- **Components**: shadcn/ui, Tailwind CSS
- **Editor**: TipTap (block-based editor)
- **Terminal**: xterm.js

### Data Stores

- **Primary**: PostgreSQL 16+ with pgvector
- **Cache/Queue**: Redis 7+ (Streams, Pub/Sub)
- **Object Storage**: S3-compatible (MinIO for self-hosted)
- **Search**: PostgreSQL pgvector + trigram (no Elasticsearch)

### AI/ML

- **LLM**: OpenAI, Anthropic, local models via Ollama
- **Embeddings**: OpenAI text-embedding-3-small, Cohere, local models
- **Vector Search**: HNSW indexes in pgvector

---

## Project Structure

```
researchos/
├── backend/
│   ├── src/
│   │   ├── domain/                 # Domain Layer
│   │   │   ├── experiments/
│   │   │   │   ├── entities.py     # Experiment, Run, Metric
│   │   │   │   ├── value_objects.py
│   │   │   │   ├── events.py       # ExperimentStarted, etc.
│   │   │   │   ├── repositories.py # Interfaces
│   │   │   │   └── services.py     # Domain services
│   │   │   ├── notebooks/
│   │   │   ├── papers/
│   │   │   ├── artifacts/
│   │   │   └── shared/
│   │   ├── application/           # Application Layer
│   │   │   ├── experiments/
│   │   │   │   ├── services.py
│   │   │   │   ├── handlers.py     # Event handlers
│   │   │   │   └── dto.py
│   │   │   ├── notebooks/
│   │   │   ├── search/
│   │   │   └── ai/
│   │   ├── infrastructure/        # Infrastructure Layer
│   │   │   ├── persistence/
│   │   │   │   ├── postgres/
│   │   │   │   └── redis/
│   │   │   ├── adapters/
│   │   │   │   ├── llm/
│   │   │   │   ├── embeddings/
│   │   │   │   └── storage/
│   │   │   └── events/
│   │   │       ├── producer.py
│   │   │       ├── consumer.py
│   │   │       └── dlq.py
│   │   └── api/                   # Presentation Layer
│   │       ├── routes/
│   │       ├── dependencies/
│   │       └── middleware/
│   ├── tests/
│   ├── alembic/                    # Migrations
│   └── pyproject.toml
├── frontend/
│   ├── app/                        # Next.js App Router
│   ├── components/
│   ├── lib/
│   └── package.json
├── sdk/
│   └── python/
│       ├── researchos/
│       │   ├── client.py
│       │   ├── experiment.py
│       │   ├── wal.py
│       │   └── sync.py
│       └── pyproject.toml
└── docs/
    ├── 01-high-level-architecture.md
    ├── 02-domain-model.md
    ├── 03-database-schema.md
    ├── 04-python-sdk.md
    ├── 05-ai-architecture.md
    ├── 06-search-architecture.md
    ├── 07-research-graph.md
    ├── 08-notebook-architecture.md
    └── 09-event-architecture.md
```

---

## API Design

### RESTful Endpoints

```
/api/v1/
├── organizations/{org_id}/
│   ├── projects/{project_id}/
│   │   ├── experiments/
│   │   │   ├── POST   /                    # Create experiment
│   │   │   ├── GET    /{exp_id}            # Get experiment
│   │   │   ├── GET    /{exp_id}/runs       # List runs
│   │   │   └── GET    /{exp_id}/metrics    # Get metrics
│   │   ├── notebooks/
│   │   │   ├── POST   /                    # Create notebook
│   │   │   ├── GET    /{nb_id}             # Get notebook
│   │   │   ├── PATCH  /{nb_id}/blocks      # Update blocks
│   │   │   └── POST   /{nb_id}/execute     # Execute notebook
│   │   ├── papers/
│   │   ├── artifacts/
│   │   └── graph/
│   │       ├── GET    /nodes                # Query nodes
│   │       ├── GET    /nodes/{id}/edges    # Get edges
│   │       └── GET    /traverse             # Graph traversal
│   ├── search/
│   │   ├── POST   /                         # Search
│   │   └── GET    /suggestions              # Autocomplete
│   └── ask/
│       └── POST   /                         # AI Q&A
```

### Authentication

- JWT tokens (access + refresh)
- Organization membership validation
- API key support for SDK

---

## Non-Functional Requirements

### Performance

- Search latency: < 100ms (p99)
- API response: < 200ms (p95)
- Notebook block execution: Depends on block type
- Concurrent users: 10,000 per tenant

### Scalability

- Horizontal scaling via stateless API servers
- Redis for session state and event streaming
- Read replicas for PostgreSQL
- CDN for static assets

### Reliability

- Event-driven durability (no data loss)
- Idempotent operations
- Graceful degradation (offline SDK)
- Circuit breakers for external services

### Security

- Row-level security (PostgreSQL)
- Organization isolation
- Audit logging via events
- Secrets management (not in repo)

---

## Key Design Decisions

### 1. Property Graph Model

Every research object is a node with typed edges. This enables:
- Traversal queries (show me all experiments of this hypothesis)
- Version history (git-like DAG)
- Forking and branching
- Impact analysis

### 2. Event Sourcing for Critical Paths

Experiments and notebooks use event sourcing:
- Full audit trail
- Replay capability
- Temporal queries
- Event-driven projections

### 3. Hybrid Search

PostgreSQL pgvector + trigram (no dedicated search engine):
- Simplified infrastructure
- Strong consistency
- Good enough performance (<100ms)
- Lower operational cost

### 4. Notebook as Code

Notebooks are versioned, executable, and reusable:
- NOT Jupyter
- Block-level versioning (not notebook snapshots)
- Reusable blocks across notebooks
- Git-compatible storage

---

## Deployment

### SaaS

- Kubernetes (EKS/GKE)
- RDS PostgreSQL
- ElastiCache Redis
- S3 for object storage

### Self-Hosted

- Docker Compose (simple)
- Kubernetes Helm charts (enterprise)
- MinIO for object storage
- PostgreSQL + pgvector container

---

## Next Steps

1. Domain model details → [02-domain-model.md](./02-domain-model.md)
2. Database schema → [03-database-schema.md](./03-database-schema.md)
3. Python SDK design → [04-python-sdk.md](./04-python-sdk.md)
4. AI architecture → [05-ai-architecture.md](./05-ai-architecture.md)
5. Search architecture → [06-search-architecture.md](./06-search-architecture.md)
6. Research graph design → [07-research-graph.md](./07-research-graph.md)
7. Notebook architecture → [08-notebook-architecture.md](./08-notebook-architecture.md)
8. Event architecture → [09-event-architecture.md](./09-event-architecture.md)
