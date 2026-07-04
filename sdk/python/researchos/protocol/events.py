"""Event type definitions for ResearchOS SDK."""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    EXPERIMENT_STARTED = "experiment.started"
    RUN_STARTED = "run.started"
    METRIC_LOGGED = "metric.logged"
    ARTIFACT_UPLOADED = "artifact.uploaded"
    PARAMETER_SET = "parameter.set"
    RUN_COMPLETED = "run.completed"
    GIT_COMMIT = "git.commit"


class BaseEvent(BaseModel):
    """Base event with common fields."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: UUID
    project_id: UUID
    experiment_id: UUID
    run_id: Optional[UUID] = None

    model_config = {"use_enum_values": True, "from_attributes": True}


class MetricLoggedEvent(BaseEvent):
    event_type: Literal["metric.logged"] = "metric.logged"
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int = Field(ge=0)
    wall_time: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParameterSetEvent(BaseEvent):
    event_type: Literal["parameter.set"] = "parameter.set"
    key: str
    value: str
    value_type: Literal["string", "int", "float", "bool", "json"]


class ArtifactUploadedEvent(BaseEvent):
    event_type: Literal["artifact.uploaded"] = "artifact.uploaded"
    artifact_id: UUID
    name: str
    artifact_type: str
    mime_type: str
    size_bytes: int
    hash_sha256: str
    storage_path: Optional[str] = None


class GitCommitEvent(BaseEvent):
    event_type: Literal["git.commit"] = "git.commit"
    commit_sha: str = Field(min_length=40, max_length=40)
    branch: Optional[str] = None
    message: Optional[str] = None
    author: Optional[str] = None
    is_dirty: bool = False
    remote_url: Optional[str] = None


class RunStartedEvent(BaseEvent):
    event_type: Literal["run.started"] = "run.started"
    run_number: int
    git_commit: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class RunCompletedEvent(BaseEvent):
    event_type: Literal["run.completed"] = "run.completed"
    status: Literal["completed", "failed", "cancelled"]
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ExperimentStartedEvent(BaseEvent):
    event_type: Literal["experiment.started"] = "experiment.started"
    name: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
