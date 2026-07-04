"""Paper domain events"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaperEdited(BaseModel):
    """Event: Paper edited"""
    event_type: str = "paper.edited"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Paper"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    paper_id: UUID
    organization_id: UUID
