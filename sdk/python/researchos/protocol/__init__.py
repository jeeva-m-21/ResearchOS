"""Event protocol definitions for ResearchOS SDK."""
from .events import (
    EventType,
    BaseEvent,
    ExperimentStartedEvent,
    RunStartedEvent,
    RunCompletedEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
    ArtifactUploadedEvent,
    GitCommitEvent,
)
from .validation import serialize_event, deserialize_event

__all__ = [
    "EventType",
    "BaseEvent",
    "ExperimentStartedEvent",
    "RunStartedEvent",
    "RunCompletedEvent",
    "MetricLoggedEvent",
    "ParameterSetEvent",
    "ArtifactUploadedEvent",
    "GitCommitEvent",
    "serialize_event",
    "deserialize_event",
]
