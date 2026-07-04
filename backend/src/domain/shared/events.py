"""Base domain event"""
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base event model"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    organization_id: UUID
    aggregate_id: UUID
    aggregate_type: str
    version: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
