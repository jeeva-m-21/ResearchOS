"""Graph repository interfaces."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import Edge, TraversalResult


class IEdgeRepository(ABC):
    """Interface for edge persistence and graph traversal."""

    @abstractmethod
    async def get_by_id(self, edge_id: UUID) -> Optional[Edge]:
        """Fetch a single edge by ID."""
        ...

    @abstractmethod
    async def get_outgoing_edges(
        self, node_id: UUID, organization_id: UUID,
        edge_type: Optional[str] = None,
    ) -> list[Edge]:
        """Fetch edges originating from a node."""
        ...

    @abstractmethod
    async def get_incoming_edges(
        self, node_id: UUID, organization_id: UUID,
        edge_type: Optional[str] = None,
    ) -> list[Edge]:
        """Fetch edges pointing to a node."""
        ...

    @abstractmethod
    async def save(self, edge: Edge) -> None:
        """Persist a new edge."""
        ...

    @abstractmethod
    async def traverse(
        self,
        start_node_id: UUID,
        organization_id: UUID,
        edge_type: Optional[str] = None,
        direction: str = "outgoing",
        max_depth: int = 3,
    ) -> list[TraversalResult]:
        """Traverse the graph from a starting node, returning all reachable nodes."""
        ...
