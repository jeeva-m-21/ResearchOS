"""Event serialization and deserialization."""

import json
from .events import (
    BaseEvent,
    ExperimentStartedEvent,
    RunStartedEvent,
    RunCompletedEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
    ArtifactUploadedEvent,
    GitCommitEvent,
)


def serialize_event(event: BaseEvent) -> str:
    """Serialize an event to a JSONL line."""
    return event.model_dump_json()


def deserialize_event(line: str) -> BaseEvent:
    """Deserialize a JSONL line to an event."""
    data = json.loads(line)
    event_type = data.get("event_type")

    event_classes = {
        "metric.logged": MetricLoggedEvent,
        "parameter.set": ParameterSetEvent,
        "artifact.uploaded": ArtifactUploadedEvent,
        "git.commit": GitCommitEvent,
        "run.started": RunStartedEvent,
        "run.completed": RunCompletedEvent,
        "experiment.started": ExperimentStartedEvent,
    }

    event_class = event_classes.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")

    return event_class(**data)
