"""Experiment domain events"""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ExperimentStarted(BaseModel):
    """Event: Experiment started"""
    event_type: str = "experiment.started"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Experiment"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    experiment_id: UUID
    organization_id: UUID
    project_id: UUID
    started_by: UUID

class MetricLogged(BaseModel):
    """Event: Metric logged"""
    event_type: str = "metric.logged"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Run"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: UUID
    experiment_id: UUID
    metric_key: str
    metric_value: float
    step: int

class RunCompleted(BaseModel):
    """Event: Run completed"""
    event_type: str = "run.completed"
    event_id: UUID = Field(default_factory=lambda: __import__('uuid').uuid4())
    aggregate_id: UUID
    aggregate_type: str = "Run"
    version: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: UUID
    experiment_id: UUID
    status: str
    duration_ms: Optional[int] = None
