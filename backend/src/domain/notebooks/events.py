"""Notebook domain events"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotebookUpdated(BaseModel):
    """Event: Notebook updated"""
    event_type: str = "notebook.updated"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Notebook"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notebook_id: UUID
    organization_id: UUID
