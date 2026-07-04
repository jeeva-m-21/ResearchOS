"""ResearchOS Python SDK"""

from .client import ResearchOSClient
from .experiment import Experiment
from .wal import WAL
from .protocol.events import (
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
from .protocol.validation import serialize_event, deserialize_event

_client: ResearchOSClient = None


def init(experiment: str, project: str = None, api_key: str = None, **kwargs) -> None:
    """Initialize ResearchOS"""
    global _client
    _client = ResearchOSClient(api_key=api_key, **kwargs)
    _client.init_experiment(experiment, project=project)


def log_metric(key: str, value: float, step: int = None, **metadata) -> None:
    """Log a metric"""
    if _client is None:
        raise RuntimeError("Call researchos.init() first")
    _client.log_metric(key, value, step=step, **metadata)


def log_parameters(params: dict) -> None:
    """Log parameters"""
    for key, value in params.items():
        _client.log_parameter(key, value)


def finish(status: str = "completed") -> None:
    """Finish the run"""
    if _client:
        _client.finish(status=status)


__all__ = [
    "init",
    "log_metric",
    "log_parameters",
    "finish",
    "Experiment",
    "WAL",
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
