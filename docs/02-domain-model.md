# ResearchOS - Domain Model & Bounded Contexts

## Overview

This document defines the domain model for ResearchOS using Domain-Driven Design (DDD) principles. Each bounded context has clear aggregates, entities, value objects, and domain events.

---

## Bounded Contexts

### Context Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCHOS BOUNDED CONTEXTS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐│
│  │ Research Graph   │◄───────│   Experiments    │───────►│   Notebooks      ││
│  │    Context       │         │    Context       │         │   Context        ││
│  │                  │         │                  │         │                  ││
│  │ • Node           │         │ • Experiment     │         │ • Notebook       ││
│  │ • Edge           │         │ • Run            │         │ • Block          ││
│  │ • Branch         │         │ • Metric         │         │ • BlockContent   ││
│  │ • Fork           │         │ • Parameter      │         │ • Execution      ││
│  └──────────────────┘         └──────────────────┘         └──────────────────┘│
│          ▲                            │                            │          │
│          │                            ▼                            ▼          │
│  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐│
│  │    Artifacts     │◄───────│   Search Context  │───────►│     Papers       ││
│  │    Context       │         │   (Read Model)    │         │    Context       ││
│  │                  │         │                  │         │                  ││
│  │ • Artifact       │         │ • SearchResult   │         │ • Paper          ││
│  │ • ArtifactVersion│        │ • SearchIndex    │         │ • Citation       ││
│  │ • Lineage       │         │ • Embedding      │         │ • Reference      ││
│  └──────────────────┘         └──────────────────┘         └──────────────────┘│
│          ▲                                                                   │
│          │           ┌────────────────────────────────────────┐             │
│          │           │          AI Context                     │             │
│          └───────────│ • AgentSession                         │             │
│                      │ • ToolCall                             │             │
│                      │ • Conversation                         │             │
│                      └────────────────────────────────────────┘             │
│                                                                               │
│  Shared Kernel: Event Definitions, Value Objects, Common Interfaces          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Shared Kernel

### Value Objects

```python
# src/domain/shared/value_objects.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class OrganizationId(BaseModel):
    value: UUID

class UserId(BaseModel):
    value: UUID

class ProjectId(BaseModel):
    value: UUID

class Timestamps(BaseModel):
    created_at: datetime
    updated_at: datetime
    created_by: UserId
    updated_by: UserId

class Version(BaseModel):
    major: int = Field(ge=0)
    minor: int = Field(ge=0)
    patch: int = Field(ge=0)
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def bump_major(self) -> 'Version':
        return Version(major=self.major + 1, minor=0, patch=0)
    
    def bump_minor(self) -> 'Version':
        return Version(major=self.major, minor=self.minor + 1, patch=0)
    
    def bump_patch(self) -> 'Version':
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)

class GitSHA(BaseModel):
    value: str = Field(min_length=40, max_length=40)

class BranchName(BaseModel):
    value: str = Field(pattern=r'^[\w\-/]+$')

class Tags(BaseModel):
    values: list[str] = Field(default_factory=list)
```

### Base Domain Event

```python
# src/domain/shared/events.py

from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_id: UUID
    aggregate_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(ge=1)
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
```

---

## Experiments Context

### Aggregate Root: Experiment

```python
# src/domain/experiments/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional
from domain.shared.value_objects import OrganizationId, ProjectId, UserId, Timestamps, Tags
from domain.shared.events import DomainEvent
from pydantic import BaseModel, Field

class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Experiment(BaseModel):
    """Experiment aggregate root - manages experiment lifecycle"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: OrganizationId
    project_id: ProjectId
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis_id: Optional[UUID] = None  # Reference to hypothesis in graph
    status: ExperimentStatus = ExperimentStatus.CREATED
    parameters: dict = Field(default_factory=dict)
    tags: Tags = Field(default_factory=Tags)
    timestamps: Timestamps
    
    # Aggregates runs
    _runs: list['Run'] = []
    
    def start(self, started_by: UserId) -> 'ExperimentStarted':
        if self.status != ExperimentStatus.CREATED:
            raise ValueError(f"Cannot start experiment in {self.status} status")
        
        self.status = ExperimentStatus.RUNNING
        event = ExperimentStarted(
            aggregate_id=self.id,
            aggregate_type="Experiment",
            version=1,
            experiment_id=self.id,
            organization_id=self.organization_id.value,
            project_id=self.project_id.value,
            started_by=started_by.value
        )
        return event
    
    def pause(self) -> None:
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Can only pause running experiments")
        self.status = ExperimentStatus.PAUSED
    
    def complete(self) -> None:
        if self.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
            raise ValueError("Can only complete running or paused experiments")
        self.status = ExperimentStatus.COMPLETED
    
    def fail(self, error: str) -> None:
        self.status = ExperimentStatus.FAILED

class Run(BaseModel):
    """Run entity - single execution of an experiment"""
    
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    run_number: int = Field(ge=1)
    status: ExperimentStatus = ExperimentStatus.CREATED
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    metrics: list['Metric'] = Field(default_factory=list)
    
    def log_metric(self, key: str, value: float, step: int, timestamp: datetime) -> 'MetricLogged':
        metric = Metric(
            run_id=self.id,
            key=key,
            value=value,
            step=step,
            timestamp=timestamp
        )
        self.metrics.append(metric)
        return MetricLogged(
            aggregate_id=self.id,
            aggregate_type="Run",
            version=1,
            run_id=self.id,
            experiment_id=self.experiment_id,
            metric_key=key,
            metric_value=value,
            step=step
        )

class Metric(BaseModel):
    """Metric value object"""
    
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int = Field(ge=0)
    timestamp: datetime
```

### Events

```python
# src/domain/experiments/events.py

from domain.shared.events import DomainEvent
from uuid import UUID

class ExperimentStarted(DomainEvent):
    event_type: str = "experiment.started"
    experiment_id: UUID
    organization_id: UUID
    project_id: UUID
    started_by: UUID

class MetricLogged(DomainEvent):
    event_type: str = "metric.logged"
    run_id: UUID
    experiment_id: UUID
    metric_key: str
    metric_value: float
    step: int

class ExperimentCompleted(DomainEvent):
    event_type: str = "experiment.completed"
    experiment_id: UUID
    run_count: int
    final_status: str
```

### Repository Interface

```python
# src/domain/experiments/repositories.py

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from domain.experiments.entities import Experiment, Run

class IExperimentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        pass
    
    @abstractmethod
    async def get_by_project(self, project_id: UUID, limit: int = 100, offset: int = 0) -> list[Experiment]:
        pass
    
    @abstractmethod
    async def save(self, experiment: Experiment) -> None:
        pass
    
    @abstractmethod
    async def delete(self, experiment_id: UUID) -> None:
        pass

class IRunRepository(ABC):
    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> Optional[Run]:
        pass
    
    @abstractmethod
    async def get_by_experiment(self, experiment_id: UUID) -> list[Run]:
        pass
    
    @abstractmethod
    async def save(self, run: Run) -> None:
        pass
```

---

## Notebooks Context

### Aggregate Root: Notebook

```python
# src/domain/notebooks/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional
from domain.shared.value_objects import OrganizationId, ProjectId, Timestamps, Version, BranchName
from pydantic import BaseModel, Field

class Notebook(BaseModel):
    """Notebook aggregate root - block-based notebook with versioning"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: OrganizationId
    project_id: ProjectId
    title: str = Field(min_length=1, max_length=255)
    branch: BranchName = Field(default_factory=lambda: BranchName(value="main"))
    parent_commit: Optional[str] = None  # Git-like commit SHA
    timestamps: Timestamps
    
    # Blocks are separate entities (not owned)
    _block_ids: list[UUID] = []
    
    def add_block(self, block_id: UUID, position: int) -> 'NotebookUpdated':
        self._block_ids.insert(position, block_id)
        return NotebookUpdated(
            aggregate_id=self.id,
            aggregate_type="Notebook",
            version=1,
            operation="add_block",
            block_id=block_id,
            position=position
        )
    
    def remove_block(self, block_id: UUID) -> 'NotebookUpdated':
        self._block_ids.remove(block_id)
        return NotebookUpdated(
            aggregate_id=self.id,
            aggregate_type="Notebook",
            version=1,
            operation="remove_block",
            block_id=block_id
        )
    
    def reorder_blocks(self, block_ids: list[UUID]) -> 'NotebookUpdated':
        self._block_ids = block_ids
        return NotebookUpdated(
            aggregate_id=self.id,
            aggregate_type="Notebook",
            version=1,
            operation="reorder_blocks",
            block_order=block_ids
        )

class BlockType(str, Enum):
    MARKDOWN = "markdown"
    PYTHON = "python"
    RUST = "rust"
    SQL = "sql"
    MERMAID = "mermaid"
    LATEX = "latex"
    DIAGRAM = "diagram"
    EXPERIMENT_CARD = "experiment_card"
    METRIC = "metric"
    CITATION = "citation"
    AI_SUMMARY = "ai_summary"

class Block(BaseModel):
    """Block entity - has identity, position, and metadata. Content is separate."""
    
    id: UUID = Field(default_factory=uuid4)
    notebook_id: UUID
    block_type: BlockType
    position: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    
    # Current content snapshot reference
    current_content_id: Optional[UUID] = None

class BlockContent(BaseModel):
    """BlockContent value object - immutable snapshot of block content"""
    
    id: UUID = Field(default_factory=uuid4)
    block_id: UUID
    version: int = Field(ge=1)
    content: str
    language: Optional[str] = None  # For code blocks
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    created_by: UUID

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class Execution(BaseModel):
    """Execution entity - result of executing a block"""
    
    id: UUID = Field(default_factory=uuid4)
    block_content_id: UUID
    status: ExecutionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    artifacts: list[UUID] = Field(default_factory=list)  # Generated artifacts
```

### Events

```python
# src/domain/notebooks/events.py

from domain.shared.events import DomainEvent
from uuid import UUID

class NotebookUpdated(DomainEvent):
    event_type: str = "notebook.updated"
    operation: str  # add_block, remove_block, reorder_blocks, etc.
    block_id: Optional[UUID] = None
    position: Optional[int] = None
    block_order: Optional[list[UUID]] = None

class BlockExecuted(DomainEvent):
    event_type: str = "block.executed"
    block_id: UUID
    notebook_id: UUID
    execution_id: UUID
    status: str
    duration_ms: int
```

---

## Research Graph Context

### Aggregate Root: Node

```python
# src/domain/graph/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    IDEA = "idea"
    HYPOTHESIS = "hypothesis"
    EXPERIMENT = "experiment"
    RUN = "run"
    PAPER = "paper"
    DATASET = "dataset"
    MODEL = "model"
    NOTEBOOK = "notebook"
    BLOCK = "block"
    CITATION = "citation"
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    TASK = "task"
    INSIGHT = "insight"
    QUESTION = "question"
    ANSWER = "answer"
    METRIC = "metric"
    ARTIFACT = "artifact"
    CODE = "code"

class EdgeType(str, Enum):
    DERIVES_FROM = "derives_from"
    TESTS = "tests"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFERENCES = "references"
    USES = "uses"
    GENERATES = "generates"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    AUTHORED_BY = "authored_by"
    CITES = "cites"
    BASED_ON = "based_on"
    EXTENDS = "extends"
    REPLACES = "replaces"
    VERSION_OF = "version_of"
    FORK_OF = "fork_of"
    MERGED_FROM = "merged_from"

class Node(BaseModel):
    """Node aggregate root - vertex in the research graph"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    node_type: NodeType
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    
    # Version history
    version: int = Field(ge=1, default=1)
    parent_version_id: Optional[UUID] = None
    
    # Branching
    branch: str = "main"
    is_fork: bool = False
    forked_from_id: Optional[UUID] = None

class Edge(BaseModel):
    """Edge entity - typed connection between nodes"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    properties: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(ge=0.0, le=1.0, default=1.0)
    created_at: datetime
    created_by: UUID
    
    # Version history
    version: int = Field(ge=1, default=1)

class Branch(BaseModel):
    """Branch entity - git-like branch for notebook/experiment versioning"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    name: str = Field(pattern=r'^[\w\-/]+$')
    parent_branch: Optional[str] = None
    head_commit: Optional[str] = None  # SHA of latest commit
    created_at: datetime
    created_by: UUID
    is_merged: bool = False
    merged_at: Optional[datetime] = None
    merged_into: Optional[str] = None

class Fork(BaseModel):
    """Fork entity - copy of a node/graph with lineage"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    source_node_id: UUID
    source_branch: str
    target_branch: str
    created_at: datetime
    created_by: UUID
```

### Events

```python
# src/domain/graph/events.py

from domain.shared.events import DomainEvent
from uuid import UUID

class NodeCreated(DomainEvent):
    event_type: str = "node.created"
    node_id: UUID
    node_type: str
    title: str

class EdgeCreated(DomainEvent):
    event_type: str = "edge.created"
    edge_id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: str

class NodeVersioned(DomainEvent):
    event_type: str = "node.versioned"
    node_id: UUID
    version: int
    parent_version_id: Optional[UUID]

class BranchCreated(DomainEvent):
    event_type: str = "branch.created"
    branch_name: str
    parent_branch: Optional[str]

class BranchMerged(DomainEvent):
    event_type: str = "branch.merged"
    source_branch: str
    target_branch: str
    merged_by: UUID

class NodeForked(DomainEvent):
    event_type: str = "node.forked"
    source_node_id: UUID
    new_node_id: UUID
    fork_branch: str
```

---

## Papers Context

### Aggregate Root: Paper

```python
# src/domain/papers/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PaperStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Paper(BaseModel):
    """Paper aggregate root - research paper composition"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    title: str = Field(min_length=1, max_length=500)
    abstract: Optional[str] = None
    status: PaperStatus = PaperStatus.DRAFT
    version: int = Field(ge=1, default=1)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    
    # Sections (stored as blocks in graph)
    _sections: list[UUID] = []
    
    # Citations
    _citations: list['Citation'] = []

class Citation(BaseModel):
    """Citation value object"""
    
    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    cited_paper_id: Optional[UUID] = None  # Internal reference
    cited_doi: Optional[str] = None  # External reference
    citation_key: str
    authors: list[str]
    title: str
    year: int
    venue: Optional[str] = None
    page_numbers: Optional[str] = None

class Reference(BaseModel):
    """Reference entity - where in paper a citation is used"""
    
    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    citation_id: UUID
    section_id: UUID
    block_id: UUID
    context: Optional[str] = None  # Surrounding text
```

### Events

```python
# src/domain/papers/events.py

from domain.shared.events import DomainEvent
from uuid import UUID

class PaperEdited(DomainEvent):
    event_type: str = "paper.edited"
    paper_id: UUID
    version: int
    changes: dict  # Field changes

class CitationAdded(DomainEvent):
    event_type: str = "citation.added"
    paper_id: UUID
    citation_id: UUID
    cited_doi: Optional[str]
```

---

## Artifacts Context

### Aggregate: Artifact

```python
# src/domain/artifacts/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class ArtifactType(str, Enum):
    MODEL = "model"
    DATASET = "dataset"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    BINARY = "binary"
    CHECKPOINT = "checkpoint"
    LOG = "log"
    CONFIG = "config"

class Artifact(BaseModel):
    """Artifact aggregate root - stored file with metadata and lineage"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    artifact_type: ArtifactType
    mime_type: str
    size_bytes: int = Field(ge=0)
    hash_sha256: str
    created_at: datetime
    created_by: UUID
    
    # Current version
    current_version: int = 1
    
    # Lineage
    experiment_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    notebook_id: Optional[UUID] = None

class ArtifactVersion(BaseModel):
    """ArtifactVersion entity - immutable version of an artifact"""
    
    id: UUID = Field(default_factory=uuid4)
    artifact_id: UUID
    version: int = Field(ge=1)
    storage_path: str  # S3 path
    size_bytes: int = Field(ge=0)
    hash_sha256: str
    created_at: datetime
    created_by: UUID
    metadata: dict = Field(default_factory=dict)

class Lineage(BaseModel):
    """Lineage entity - tracks artifact lineage"""
    
    id: UUID = Field(default_factory=uuid4)
    artifact_version_id: UUID
    parent_artifact_version_id: Optional[UUID] = None
    transform_description: Optional[str] = None
    transform_code: Optional[str] = None  # Code used to generate
```

### Events

```python
# src/domain/artifacts/events.py

from domain.shared.events import DomainEvent
from uuid import UUID

class ArtifactUploaded(DomainEvent):
    event_type: str = "artifact.uploaded"
    artifact_id: UUID
    artifact_type: str
    size_bytes: int
    hash_sha256: str
    experiment_id: Optional[UUID]
    run_id: Optional[UUID]

class ArtifactVersioned(DomainEvent):
    event_type: str = "artifact.versioned"
    artifact_id: UUID
    version: int
    storage_path: str
```

---

## AI Context

### Aggregate: AgentSession

```python
# src/domain/ai/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

class AgentType(str, Enum):
    PLANNER = "planner"
    RETRIEVER = "retriever"
    RESEARCH_ANALYST = "research_analyst"
    EXPERIMENT_ANALYST = "experiment_analyst"
    PAPER_WRITER = "paper_writer"
    CODE_REVIEWER = "code_reviewer"
    TOOL_EXECUTOR = "tool_executor"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class AgentSession(BaseModel):
    """AgentSession aggregate root - AI conversation session"""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    user_id: UUID
    agent_types: list[AgentType]
    created_at: datetime
    messages: list['Message'] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)  # Retrieved context

class Message(BaseModel):
    """Message value object"""
    
    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    created_at: datetime
    tool_calls: list['ToolCall'] = Field(default_factory=list)

class ToolCall(BaseModel):
    """ToolCall entity - invocation of a tool"""
    
    id: UUID = Field(default_factory=uuid4)
    tool_name: str
    arguments: dict[str, Any]
    result: Optional[str] = None
    status: str = "pending"  # pending, success, failed
    created_at: datetime
    completed_at: Optional[datetime] = None
```

---

## Value Object Catalog

| Value Object | Purpose | Used In |
|--------------|---------|---------|
| OrganizationId | Tenant isolation | All aggregates |
| ProjectId | Project scope | Experiments, Notebooks, Papers |
| UserId | Actor identification | All aggregates |
| Timestamps | Created/updated tracking | All entities |
| Version | Semantic versioning | Artifacts, Papers |
| GitSHA | Git commit reference | Runs, Notebooks |
| BranchName | Git-like branch name | Notebooks, Experiments |
| Tags | Labeling/filtering | Experiments, Papers |

---

## Aggregate Roots Summary

| Aggregate Root | Bounded Context | Invariants |
|----------------|------------------|------------|
| Experiment | Experiments | Status transitions, owns runs |
| Notebook | Notebooks | Block ordering, versioning |
| Node | Research Graph | Type consistency, version history |
| Paper | Papers | Version tracking, citation consistency |
| Artifact | Artifacts | Immutability of versions |
| AgentSession | AI | Message ordering, tool call tracking |

---

## Next Steps

- Database schema design → [03-database-schema.md](./03-database-schema.md)
- Event architecture → [09-event-architecture.md](./09-event-architecture.md)
