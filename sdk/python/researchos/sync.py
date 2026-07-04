"""Sync: Push WAL events to ResearchOS backend.

Reads events from the Write-Ahead Log, converts them to the backend's
DomainEvent-compatible format, and POSTs them to /v1/events/batch.
"""

from typing import Optional

import httpx

from .protocol.events import BaseEvent
from .wal import WAL


class Syncer:
    """Syncs WAL events to the ResearchOS backend.

    Reads events from WAL starting at the last sync offset,
    converts them to backend-compatible format, sends them
    to /v1/events/batch, and updates the sync offset on success.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def sync(self, wal: WAL, limit: int = 100) -> dict[str, object]:
        """Sync events from WAL to backend.

        Args:
            wal: WAL instance to read from.
            limit: Max events to sync in one batch.

        Returns:
            Dict with keys: synced_count, failed_count, new_offset, error (optional)
        """
        start_offset = wal.get_sync_offset()

        events = wal.read(start_offset, batch_size=limit)
        if not events:
            return {"synced_count": 0, "failed_count": 0, "new_offset": start_offset}

        batch = []
        for _offset, event in events:
            domain_event = self._convert_to_domain_event(event)
            batch.append(domain_event)

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = httpx.post(
                f"{self.base_url}/v1/events/batch",
                json=batch,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                last_offset, _ = events[-1]
                next_offset = self._find_next_offset(wal, last_offset)
                wal.update_sync_offset(next_offset)

                data = response.json()
                return {
                    "synced_count": data.get("count", len(events)),
                    "failed_count": 0,
                    "new_offset": next_offset,
                }

            return {
                "synced_count": 0,
                "failed_count": len(events),
                "new_offset": start_offset,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }

        except Exception as e:
            return {
                "synced_count": 0,
                "failed_count": len(events),
                "new_offset": start_offset,
                "error": str(e),
            }

    @staticmethod
    def _convert_to_domain_event(event: BaseEvent) -> dict[str, object]:
        """Convert SDK BaseEvent to backend DomainEvent-compatible dict."""
        event_dict = event.model_dump(mode="json")

        domain_event = {
            "event_id": event_dict["event_id"],
            "event_type": event_dict["event_type"],
            "organization_id": event_dict["organization_id"],
            "aggregate_id": event_dict.get("experiment_id", event_dict["event_id"]),
            "aggregate_type": Syncer._infer_aggregate_type(event_dict["event_type"]),
            "version": 1,
            "timestamp": event_dict["timestamp"],
        }

        # Include all original event data for the backend's full payload
        domain_event["payload"] = event_dict
        return domain_event

    @staticmethod
    def _infer_aggregate_type(event_type: str) -> str:
        """Infer aggregate type from event type string."""
        mapping = {
            "experiment.started": "Experiment",
            "run.started": "Run",
            "run.completed": "Run",
            "metric.logged": "Run",
            "parameter.set": "Run",
            "artifact.uploaded": "Artifact",
            "git.commit": "Run",
        }
        return mapping.get(event_type, "Experiment")

    @staticmethod
    def _find_next_offset(wal: WAL, last_offset: int) -> int:
        """Find the byte offset after the last event."""
        with open(wal.file_path, "r") as f:
            f.seek(last_offset)
            line = f.readline()
            if line:
                return f.tell()
            return last_offset
