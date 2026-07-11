"""Graph domain entities — edges for the property graph."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EdgeType(str, Enum):
    """Typed relationships between nodes in the research graph."""

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


class Edge(BaseModel):
    """Edge entity — a typed, directed connection between two nodes.

    Edges form the relationships in the property graph, enabling
    traversal queries such as "find all experiments that test hypothesis X".
    """

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    properties: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    version: int = Field(default=1, ge=1)
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class TraversalResult(BaseModel):
    """Result of a graph traversal — a related node reached via edges."""

    node_id: UUID
    edge_id: UUID
    edge_type: str
    direction: str  # "outgoing" or "incoming"
    depth: int = Field(ge=1)
    path: list[UUID] = Field(default_factory=list)
