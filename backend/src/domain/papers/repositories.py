"""Paper repository interfaces"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import Citation, Paper


class IPaperRepository(ABC):
    """Paper repository interface"""

    @abstractmethod
    async def get_by_id(self, paper_id: UUID) -> Optional[Paper]:
        pass

    @abstractmethod
    async def get_by_project(
        self, project_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Paper]:
        pass

    @abstractmethod
    async def save(self, paper: Paper) -> None:
        pass

    @abstractmethod
    async def delete(self, paper_id: UUID) -> None:
        pass


class ICitationRepository(ABC):
    """Citation repository interface"""

    @abstractmethod
    async def get_by_id(self, citation_id: UUID) -> Optional[Citation]:
        pass

    @abstractmethod
    async def get_by_paper(self, paper_id: UUID) -> list[Citation]:
        pass

    @abstractmethod
    async def save(self, citation: Citation) -> None:
        pass

    @abstractmethod
    async def delete(self, citation_id: UUID) -> None:
        pass
