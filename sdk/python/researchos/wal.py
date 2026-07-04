"""Write-Ahead Log for crash-safe event persistence.

File format: JSONL (one event per line)
Location: ~/.researchos/events/{org_id}/{project_id}/{experiment_id}.jsonl

Features:
- Append-only
- Fsync on every write
- File locking for multi-process safety
- Offset tracking for incremental sync
"""

import os
import json
import fcntl
from pathlib import Path
from uuid import UUID
from typing import Optional, Union
from datetime import datetime

from .protocol.events import BaseEvent
from .protocol.validation import serialize_event, deserialize_event


class WAL:
    """Write-Ahead Log for crash-safe event persistence."""

    def __init__(
        self,
        base_dir: Union[str, Path],
        organization_id: UUID,
        project_id: UUID,
        experiment_id: UUID,
    ):
        self.base_dir = Path(base_dir)
        self.organization_id = organization_id
        self.project_id = project_id
        self.experiment_id = experiment_id

        self.file_path = (
            self.base_dir
            / "events"
            / str(organization_id)
            / str(project_id)
            / f"{experiment_id}.jsonl"
        )
        self.offset_path = self.file_path.with_suffix(".offset")
        self.lock_path = self.file_path.with_suffix(".lock")

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file for appending
        self.file = open(self.file_path, "a")
        self.lock_file = open(self.lock_path, "w")

    def append(self, event: BaseEvent) -> int:
        """Append event to WAL.

        Returns:
            Offset (byte position) of written event
        """
        # Acquire exclusive lock
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

        try:
            # Get current offset
            offset = self.file.tell()

            # Serialize event
            line = serialize_event(event) + "\n"

            # Write and sync
            self.file.write(line)
            self.file.flush()
            os.fsync(self.file.fileno())

            return offset
        finally:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)

    def read(self, start_offset: int = 0, batch_size: int = 100) -> list[tuple[int, BaseEvent]]:
        """Read events starting from offset.

        Returns:
            List of (offset, event) tuples
        """
        events: list[tuple[int, BaseEvent]] = []

        with open(self.file_path, "r") as f:
            f.seek(start_offset)

            for _ in range(batch_size):
                line = f.readline()
                if not line:
                    break

                offset = f.tell() - len(line)
                event = deserialize_event(line.strip())
                events.append((offset, event))

        return events

    def get_sync_offset(self) -> int:
        """Get last synced offset."""
        if self.offset_path.exists():
            return int(self.offset_path.read_text().strip())
        return 0

    def update_sync_offset(self, offset: int) -> None:
        """Update last synced offset."""
        self.offset_path.write_text(str(offset))

    def close(self) -> None:
        """Close WAL file."""
        self.file.close()
        self.lock_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
