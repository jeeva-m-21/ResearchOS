"""Paper domain events"""
from typing import Any
from uuid import UUID

from pydantic import Field

from domain.shared.events import DomainEvent


class PaperCreated(DomainEvent):
    """Event: Paper created"""
    event_type: str = "paper.created"
    aggregate_type: str = "Paper"
    version: int = 1
    paper_id: UUID
    project_id: UUID
    title: str
    status: str


class PaperEdited(DomainEvent):
    """Event: Paper edited"""
    event_type: str = "paper.edited"
    aggregate_type: str = "Paper"
    version: int = 1
    paper_id: UUID
    project_id: UUID
    changes: dict[str, Any] = Field(default_factory=dict)
    created_by: UUID


class PaperDeleted(DomainEvent):
    """Event: Paper deleted"""
    event_type: str = "paper.deleted"
    aggregate_type: str = "Paper"
    version: int = 1
    paper_id: UUID


class CitationAdded(DomainEvent):
    """Event: Citation added to paper"""
    event_type: str = "citation.added"
    aggregate_type: str = "Paper"
    version: int = 1
    paper_id: UUID
    citation_id: UUID
    citation_key: str


class CitationRemoved(DomainEvent):
    """Event: Citation removed from paper"""
    event_type: str = "citation.removed"
    aggregate_type: str = "Paper"
    version: int = 1
    paper_id: UUID
    citation_id: UUID
