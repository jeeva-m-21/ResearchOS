"""ResearchOS Python SDK"""

from typing import Optional

from .autolog import AutoLogger
from .client import ResearchOSClient
from .experiment import Experiment
from .protocol.events import (
    ArtifactUploadedEvent,
    BaseEvent,
    EventType,
    ExperimentStartedEvent,
    GitCommitEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
    RunCompletedEvent,
    RunStartedEvent,
)
from .protocol.validation import deserialize_event, serialize_event
from .sync import Syncer
from .utils.backoff import ExponentialBackoff
from .utils.hash import sha256_bytes, sha256_file
from .wal import WAL

_client: Optional[ResearchOSClient] = None
_autologger: Optional[AutoLogger] = None


def init(
    experiment: str,
    project: str = None,
    api_key: str = None,
    organization_id=None,
    **kwargs,
) -> None:
    """Initialize ResearchOS"""
    global _client
    _client = ResearchOSClient(
        api_key=api_key,
        organization_id=organization_id,
        **kwargs,
    )
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


def enable_autolog(interval: float = 5.0) -> None:
    """Enable automatic system/GPU metric logging for the active experiment.

    Starts a background thread that periodically captures CPU, memory, disk,
    and (when available) GPU metrics and logs them as experiment metrics.

    Args:
        interval: Seconds between metric polls (default 5.0).

    Raises:
        RuntimeError: If no experiment has been initialized via ``init()``.
    """
    global _autologger
    if _client is None:
        raise RuntimeError("Call researchos.init() first")

    if _autologger is not None and _autologger.is_running:
        return  # Already running

    _autologger = AutoLogger(log_metric_fn=_client.log_metric)
    _autologger.start(interval=interval)


def disable_autolog() -> None:
    """Disable automatic metric logging and stop the background thread."""
    global _autologger
    if _autologger is not None:
        _autologger.stop()
        _autologger = None


__all__ = [
    "init",
    "log_metric",
    "log_parameters",
    "finish",
    "enable_autolog",
    "disable_autolog",
    "Experiment",
    "ExponentialBackoff",
    "sha256_file",
    "sha256_bytes",
    "Syncer",
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
