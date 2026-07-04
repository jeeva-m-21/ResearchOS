"""Notebook domain events"""
from typing import Optional
from uuid import UUID

from src.domain.shared.events import DomainEvent


class NotebookUpdated(DomainEvent):
    """Event: Notebook updated"""
    event_type: str = "notebook.updated"
    aggregate_type: str = "Notebook"
    version: int = 1
    notebook_id: UUID
    organization_id: UUID
    operation: Optional[str] = None
