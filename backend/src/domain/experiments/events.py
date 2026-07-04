"""Experiment domain events"""
from typing import Optional
from uuid import UUID

from src.domain.shared.events import DomainEvent


class ExperimentStarted(DomainEvent):
    """Event: Experiment started"""
    event_type: str = "experiment.started"
    aggregate_type: str = "Experiment"
    version: int = 1
    experiment_id: UUID
    organization_id: UUID
    project_id: UUID
    started_by: UUID


class RunStarted(DomainEvent):
    """Event: Run started"""
    event_type: str = "run.started"
    aggregate_type: str = "Run"
    version: int = 1
    run_id: UUID
    experiment_id: UUID
    organization_id: UUID
    run_number: int
    started_by: UUID


class MetricLogged(DomainEvent):
    """Event: Metric logged"""
    event_type: str = "metric.logged"
    aggregate_type: str = "Run"
    version: int = 1
    organization_id: UUID
    run_id: UUID
    experiment_id: UUID
    metric_key: str
    metric_value: float
    step: int


class RunCompleted(DomainEvent):
    """Event: Run completed"""
    event_type: str = "run.completed"
    aggregate_type: str = "Run"
    run_id: UUID
    experiment_id: UUID
    status: str
    duration_ms: Optional[int] = None
