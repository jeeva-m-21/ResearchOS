"""Notebook domain events"""
from typing import Optional
from uuid import UUID

from domain.shared.events import DomainEvent


class NotebookUpdated(DomainEvent):
    """Event: Notebook updated"""
    event_type: str = "notebook.updated"
    aggregate_type: str = "Notebook"
    version: int = 1
    notebook_id: UUID
    organization_id: UUID
    operation: Optional[str] = None


class BlockExecuted(DomainEvent):
    """Event: Block executed"""
    event_type: str = "block.executed"
    aggregate_type: str = "Block"
    version: int = 1
    block_id: UUID
    notebook_id: UUID
    execution_id: UUID
    organization_id: UUID
    status: str
    duration_ms: Optional[int] = None
