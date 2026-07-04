"""Notebook repository interfaces"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import Notebook


class INotebookRepository(ABC):
    """Notebook repository interface"""

    @abstractmethod
    async def get_by_id(
        self, notebook_id: UUID, organization_id: UUID
    ) -> Optional[Notebook]:
        pass

    @abstractmethod
    async def get_by_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notebook]:
        pass

    @abstractmethod
    async def save(self, notebook: Notebook) -> None:
        pass

    @abstractmethod
    async def delete(self, notebook_id: UUID, organization_id: UUID) -> None:
        pass
