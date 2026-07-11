"""Graph domain events."""
from uuid import UUID

from domain.shared.events import DomainEvent


class EdgeCreated(DomainEvent):
    """Event: A new edge was created between two nodes."""
    event_type: str = "edge.created"
    aggregate_type: str = "Edge"
    version: int = 1
    source_id: UUID
    target_id: UUID
    edge_type: str
    organization_id: UUID


class NodeTraversed(DomainEvent):
    """Event: A graph traversal was performed (for audit/logging)."""
    event_type: str = "node.traversed"
    aggregate_type: str = "Graph"
    version: int = 1
    source_node_id: UUID
    edge_type: str
    depth: int
    organization_id: UUID
