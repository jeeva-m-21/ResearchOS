"""Artifact repository interfaces"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import Artifact, ArtifactVersion


class IArtifactRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self, artifact_id: UUID, organization_id: UUID
    ) -> Optional[Artifact]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Artifact]:
        pass

    @abstractmethod
    async def save(self, artifact: Artifact) -> None:
        pass

    @abstractmethod
    async def delete(self, artifact_id: UUID, organization_id: UUID) -> None:
        pass


class IArtifactVersionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, version_id: UUID) -> Optional[ArtifactVersion]:
        pass

    @abstractmethod
    async def list_by_artifact(self, artifact_id: UUID) -> list[ArtifactVersion]:
        pass

    @abstractmethod
    async def save(self, version: ArtifactVersion) -> None:
        pass
