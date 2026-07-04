"""Tests for the Write-Ahead Log."""

import tempfile
from pathlib import Path
from uuid import uuid4

from researchos import WAL
from researchos.protocol.events import ExperimentStartedEvent, MetricLoggedEvent


def test_wal_append_and_read():
    """WAL append stores an event; read returns it with correct fields."""
    org_id = uuid4()
    proj_id = uuid4()
    exp_id = uuid4()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        wal = WAL(base_dir=base, organization_id=org_id, project_id=proj_id, experiment_id=exp_id)

        event = ExperimentStartedEvent(
            organization_id=org_id,
            project_id=proj_id,
            experiment_id=exp_id,
            name="test-exp",
        )
        offset = wal.append(event)
        assert offset == 0  # first write starts at byte 0

        results = wal.read(0)
        assert len(results) == 1
        read_offset, read_event = results[0]
        assert read_offset == 0
        assert read_event.event_type == "experiment.started"
        assert read_event.experiment_id == exp_id
        assert read_event.organization_id == org_id
        assert read_event.name == "test-exp"

        wal.close()


def test_wal_offset_tracking():
    """Sync offset persists and filters already-synced events."""
    org_id = uuid4()
    proj_id = uuid4()
    exp_id = uuid4()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        wal = WAL(base_dir=base, organization_id=org_id, project_id=proj_id, experiment_id=exp_id)

        # Append two events
        e1 = ExperimentStartedEvent(
            organization_id=org_id, project_id=proj_id,
            experiment_id=exp_id, name="exp-a",
        )
        e2 = ExperimentStartedEvent(
            organization_id=org_id, project_id=proj_id,
            experiment_id=exp_id, name="exp-b",
        )
        off1 = wal.append(e1)
        off2 = wal.append(e2)
        assert off2 > off1

        # Initially sync offset is 0
        assert wal.get_sync_offset() == 0

        # Mark everything up to off2 as synced
        wal.update_sync_offset(off2)

        # Read from synced offset should give us the unread event(s)
        # off2 is the start of the second event
        results = wal.read(off2)
        assert len(results) == 1
        assert results[0][1].name == "exp-b"

        wal.close()


def test_wal_context_manager():
    """WAL works as a context manager and closes properly."""
    org_id = uuid4()
    proj_id = uuid4()
    exp_id = uuid4()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        with WAL(base_dir=base, organization_id=org_id, project_id=proj_id, experiment_id=exp_id) as wal:
            event = ExperimentStartedEvent(
                organization_id=org_id, project_id=proj_id,
                experiment_id=exp_id, name="ctx-test",
            )
            wal.append(event)

            # File should exist
            assert wal.file_path.exists()

        # After context exit, file handle should be closed
        assert wal.file.closed


def test_wal_multiple_append_batch_read():
    """Append many events; read in batches."""
    org_id = uuid4()
    proj_id = uuid4()
    exp_id = uuid4()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        wal = WAL(base_dir=base, organization_id=org_id, project_id=proj_id, experiment_id=exp_id)

        # Append 5 metrics
        for i in range(5):
            ev = MetricLoggedEvent(
                organization_id=org_id,
                project_id=proj_id,
                experiment_id=exp_id,
                key="acc",
                value=float(i),
                step=i,
                wall_time=1000.0,
            )
            wal.append(ev)

        # Read first batch of 3
        batch1 = wal.read(0, batch_size=3)
        assert len(batch1) == 3

        # Read next batch starting after the last offset from batch1
        last_offset, _ = batch1[-1]
        next_start = last_offset + 1  # skip past the byte
        # But the real offset is the start of the *next* event, so use read to find it
        # Actually, read(start_offset) starts at that byte; we need the size of the last event
        # Simpler: just read from a large offset and expect 0
        # Let's do it right: the offset returned by read() is the start position
        # So to read remaining, we need the offset of the *next* event after batch1
        # The offset returned is the start byte. The last event spans [last_offset, last_offset+len(line)]
        # Let's compute: read the file and seek past the first 3 events

        # Re-open file to count bytes
        with open(wal.file_path, "rb") as f:
            for _ in range(3):
                line = f.readline()
            byte_pos = f.tell()

        batch2 = wal.read(byte_pos, batch_size=5)
        assert len(batch2) == 2  # remaining 2 events

        wal.close()
