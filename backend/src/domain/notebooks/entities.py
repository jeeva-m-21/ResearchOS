"""Notebook domain entities"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    MARKDOWN = "markdown"
    PYTHON = "python"
    RUST = "rust"
    SQL = "sql"
    MERMAID = "mermaid"
    LATEX = "latex"
    DIAGRAM = "diagram"
    EXPERIMENT_CARD = "experiment_card"
    METRIC = "metric"
    CITATION = "citation"
    AI_SUMMARY = "ai_summary"


class Notebook(BaseModel):
    """Notebook aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    branch: str = "main"
    parent_commit: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID
    updated_by: UUID


class Block(BaseModel):
    """Block entity"""
    id: UUID = Field(default_factory=uuid4)
    notebook_id: UUID
    organization_id: UUID
    block_type: BlockType
    position: int = Field(ge=0)
    current_version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BlockContent(BaseModel):
    """BlockContent value object - immutable version of block content"""
    id: UUID = Field(default_factory=uuid4)
    block_id: UUID
    organization_id: UUID
    version: int = Field(ge=1)
    content: str
    language: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
