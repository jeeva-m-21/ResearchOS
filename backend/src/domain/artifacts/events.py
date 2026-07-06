"""Artifact domain events"""
from typing import Optional
from uuid import UUID

from src.domain.shared.events import DomainEvent


class ArtifactUploaded(DomainEvent):
    """Event: Artifact uploaded"""
    event_type: str = "artifact.uploaded"
    aggregate_type: str = "Artifact"
    version: int = 1
    artifact_id: UUID
    organization_id: UUID
    name: str
    artifact_type: str
    mime_type: str
    size_bytes: int
    hash_sha256: str
    experiment_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
