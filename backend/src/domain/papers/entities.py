"""Paper domain entities"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PaperStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Paper(BaseModel):
    """Paper aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    title: str = Field(min_length=1, max_length=500)
    abstract: Optional[str] = None
    status: PaperStatus = PaperStatus.DRAFT
    version: int = Field(default=1, ge=1)
    authors: list[str] = Field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    latex_content: Optional[str] = None
    node_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID


class Citation(BaseModel):
    """Citation entity - a bibliographic reference"""
    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    organization_id: UUID
    citation_key: str = Field(min_length=1, max_length=255)
    cited_paper_id: Optional[UUID] = None
    cited_doi: Optional[str] = None
    title: str = Field(min_length=1, max_length=500)
    authors: list[str] = Field(default_factory=list)
    year: int = Field(ge=1000, le=2100)
    venue: Optional[str] = None
    url: Optional[str] = None
    citation_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Reference(BaseModel):
    """Reference entity - where a citation is used in a paper"""
    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    citation_id: UUID
    section_id: Optional[UUID] = None
    context: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
