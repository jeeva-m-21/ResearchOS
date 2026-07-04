"""Experiment domain entities"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Experiment(BaseModel):
    """Experiment aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis_id: Optional[UUID] = None
    status: ExperimentStatus = ExperimentStatus.CREATED
    parameters: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID

class Run(BaseModel):
    """Run entity"""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    run_number: int = Field(ge=1)
    status: ExperimentStatus = ExperimentStatus.CREATED
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    git_commit: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    metrics: list["Metric"] = Field(default_factory=list)

class Metric(BaseModel):
    """Metric value object"""
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
