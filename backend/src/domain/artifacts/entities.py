"""Artifact domain entities"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    MODEL = "model"
    DATASET = "dataset"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    BINARY = "binary"
    CHECKPOINT = "checkpoint"
    LOG = "log"
    CONFIG = "config"


class Artifact(BaseModel):
    """Artifact aggregate root — a stored file with metadata."""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    artifact_type: ArtifactType
    mime_type: str
    size_bytes: int = Field(ge=0)
    hash_sha256: str
    current_version: int = 1
    experiment_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    notebook_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArtifactVersion(BaseModel):
    """ArtifactVersion entity — immutable version of an artifact."""
    id: UUID = Field(default_factory=uuid4)
    artifact_id: UUID
    organization_id: UUID
    version: int = Field(ge=1)
    storage_path: str
    size_bytes: int = Field(ge=0)
    hash_sha256: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
