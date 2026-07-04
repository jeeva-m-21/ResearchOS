"""Experiment repository interfaces"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from .entities import Experiment, Run, Metric

class IExperimentRepository(ABC):
    """Experiment repository interface"""
    
    @abstractmethod
    async def get_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        pass
    
    @abstractmethod
    async def get_by_project(self, project_id: UUID, limit: int = 100, offset: int = 0) -> List[Experiment]:
        pass
    
    @abstractmethod
    async def save(self, experiment: Experiment) -> None:
        pass
    
    @abstractmethod
    async def delete(self, experiment_id: UUID) -> None:
        pass

class IRunRepository(ABC):
    """Run repository interface"""
    
    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> Optional[Run]:
        pass
    
    @abstractmethod
    async def get_by_experiment(self, experiment_id: UUID) -> List[Run]:
        pass
    
    @abstractmethod
    async def save(self, run: Run) -> None:
        pass

class IMetricRepository(ABC):
    """Metric repository interface"""
    
    @abstractmethod
    async def log(self, metric: Metric) -> None:
        pass
    
    @abstractmethod
    async def get_by_run(self, run_id: UUID, keys: Optional[List[str]] = None) -> List[Metric]:
        pass
