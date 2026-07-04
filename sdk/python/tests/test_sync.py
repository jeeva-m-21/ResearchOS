"""Tests for the Syncer class (WAL → backend sync)."""

import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from researchos import WAL
from researchos.protocol.events import ExperimentStartedEvent, MetricLoggedEvent
from researchos.sync import Syncer

BACKEND_URL = "http://localhost:8000"

# Test credentials from AGENTS.md
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"


def _get_access_token() -> str:
    """Authenticate against the backend and return a JWT access token."""
    resp = httpx.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    resp.raise_for_status()
    token: Any = resp.json().get("access_token")
    return str(token)


def test_syncer_pushes_wal_events_to_backend() -> None:
    """Syncer reads events from WAL, POSTs them to /v1/events/batch,
    and updates the sync offset."""
    token = _get_access_token()
    org_id = uuid4()
    proj_id = uuid4()
    exp_id = uuid4()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        wal = WAL(
            base_dir=base,
            organization_id=org_id,
            project_id=proj_id,
            experiment_id=exp_id,
        )

        # Append 2 events
        e1 = ExperimentStartedEvent(
            organization_id=org_id,
            project_id=proj_id,
            experiment_id=exp_id,
            name="sync-test-experiment",
        )
        e2 = MetricLoggedEvent(
            organization_id=org_id,
            project_id=proj_id,
            experiment_id=exp_id,
            key="accuracy",
            value=0.95,
            step=1,
            wall_time=1000.0,
        )
        wal.append(e1)
        wal.append(e2)

        # Initial sync offset should be 0
        assert wal.get_sync_offset() == 0

        # Create Syncer against local backend (auth via JWT as api_key)
        syncer = Syncer(base_url=BACKEND_URL, api_key=token)

        # Sync events
        result = syncer.sync(wal)

        # Verify result
        assert result["synced_count"] == 2, (
            f"Expected 2 synced, got {result}"
        )
        assert result["failed_count"] == 0, f"Expected 0 failures, got {result}"

        new_offset = result["new_offset"]
        assert isinstance(new_offset, int) and new_offset > 0, (
            f"Expected positive int offset, got {result}"
        )

        # Verify sync offset was updated in WAL
        assert wal.get_sync_offset() == new_offset, (
            f"WAL offset ({wal.get_sync_offset()}) != result offset ({new_offset})"
        )

        # Syncing again should sync 0 events (nothing new)
        result2 = syncer.sync(wal)
        assert result2["synced_count"] == 0, (
            f"Expected 0 new events on second sync, got {result2}"
        )

        wal.close()
