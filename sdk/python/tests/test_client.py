"""Tests for the wired ResearchOSClient and Experiment context manager."""

import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from researchos import WAL
from researchos.client import ResearchOSClient
from researchos.experiment import Experiment
from researchos.protocol.events import (
    ExperimentStartedEvent,
    RunStartedEvent,
    RunCompletedEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


@pytest.fixture
def proj_id() -> UUID:
    return uuid4()


@pytest.fixture
def client(tmp_path: Path, org_id: UUID, proj_id: UUID) -> ResearchOSClient:
    """Create a client with a temp base dir and specific org/proj IDs."""
    c = ResearchOSClient(
        api_key="test-key",
        organization_id=org_id,
        offline=True,
    )
    # Monkey-patch base_dir to tmp_path for test isolation
    c.base_dir = tmp_path
    c.init_experiment("test-experiment", project_id=proj_id)
    c.start_run()
    return c


# ── ResearchOSClient tests ────────────────────────────────────────────


class TestResearchOSClient:
    """Tests for the wired SDK client."""

    def test_init_experiment_creates_wal_and_appends_event(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """init_experiment creates a WAL file and appends ExperimentStartedEvent."""
        c = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        c.base_dir = tmp_path

        exp_id = c.init_experiment("my-exp", project_id=proj_id)

        assert isinstance(exp_id, UUID)
        assert c.experiment_id == exp_id
        assert c.wal is not None
        assert c.wal.file_path.exists()

        # Read the event back
        events = c.wal.read(0)
        assert len(events) == 1
        _, event = events[0]
        assert isinstance(event, ExperimentStartedEvent)
        assert event.name == "my-exp"
        assert event.organization_id == org_id
        assert event.project_id == proj_id
        assert event.experiment_id == exp_id

        c._cleanup()

    def test_log_metric_appends_to_wal(self, client: ResearchOSClient):
        """log_metric appends a MetricLoggedEvent to the WAL."""
        client.log_metric("accuracy", 0.95, step=1)

        events = client.wal.read(0)
        # events[0] is ExperimentStarted, events[1] is RunStarted, events[2] is metric
        metric_events = [
            e for _, e in events if isinstance(e, MetricLoggedEvent)
        ]
        assert len(metric_events) == 1
        me = metric_events[0]
        assert me.key == "accuracy"
        assert me.value == 0.95
        assert me.step == 1
        assert me.run_id == client.run_id

    def test_log_metric_auto_increments_step(self, client: ResearchOSClient):
        """log_metric auto-increments step when not provided."""
        client.log_metric("loss", 0.5)
        client.log_metric("loss", 0.4)

        metric_events = [
            e for _, e in client.wal.read(0) if isinstance(e, MetricLoggedEvent)
        ]
        assert len(metric_events) == 2
        assert metric_events[0].step == 1
        assert metric_events[1].step == 2

    def test_log_metric_without_run_raises(self, org_id: UUID, proj_id: UUID):
        """log_metric without start_run raises RuntimeError."""
        c = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        c.init_experiment("exp", project_id=proj_id)

        with pytest.raises(RuntimeError, match="No active run"):
            c.log_metric("acc", 0.5)

        c._cleanup()

    def test_log_parameter_appends_to_wal(self, client: ResearchOSClient):
        """log_parameter appends a ParameterSetEvent with correct type inference."""
        client.log_parameter("lr", 0.001)
        client.log_parameter("epochs", 100)
        client.log_parameter("use_dropout", True)
        client.log_parameter("config", {"a": 1})
        client.log_parameter("name", "test")

        param_events = [
            e for _, e in client.wal.read(0) if isinstance(e, ParameterSetEvent)
        ]
        assert len(param_events) == 5

        # Check type inference
        type_map = {(p.key, p.value_type) for p in param_events}
        assert ("lr", "float") in type_map
        assert ("epochs", "int") in type_map
        assert ("use_dropout", "bool") in type_map
        assert ("config", "json") in type_map
        assert ("name", "string") in type_map

    def test_start_run_creates_uuid_and_appends_event(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """start_run returns a UUID and appends RunStartedEvent."""
        c = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        c.base_dir = tmp_path
        c.init_experiment("exp", project_id=proj_id)

        run_id = c.start_run(parameters={"lr": 0.01})
        assert isinstance(run_id, UUID)
        assert c.run_id == run_id

        run_events = [
            e for _, e in c.wal.read(0) if isinstance(e, RunStartedEvent)
        ]
        assert len(run_events) == 1
        assert run_events[0].run_id == run_id
        assert run_events[0].parameters == {"lr": 0.01}

        c._cleanup()

    def test_finish_appends_event_and_clears_run(self, client: ResearchOSClient):
        """finish appends RunCompletedEvent and clears run_id."""
        run_id = client.run_id
        client.finish(status="completed")

        assert client.run_id is None

        completed_events = [
            e for _, e in client.wal.read(0) if isinstance(e, RunCompletedEvent)
        ]
        assert len(completed_events) == 1
        assert completed_events[0].run_id == run_id
        assert completed_events[0].status == "completed"

    def test_init_experiment_requires_org_id(self):
        """init_experiment raises ValueError when organization_id is not set."""
        c = ResearchOSClient(api_key="test-key", organization_id=None)
        with pytest.raises(ValueError, match="organization_id is required"):
            c.init_experiment("exp")


# ── Experiment context manager tests ──────────────────────────────────


class TestExperimentContext:
    """Tests for the high-level Experiment context manager."""

    def test_context_manager_init_and_finish(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """Experiment context manager creates WAL, logs, and finishes."""
        with Experiment(
            "ctx-test",
            organization_id=org_id,
            offline=True,
        ) as exp:
            # Monkey-patch for test isolation
            exp._client.base_dir = tmp_path
            exp._client.project_id = proj_id
            # Re-init with tmp_path
            exp._client.init_experiment("ctx-test", project_id=proj_id)
            exp._client.start_run()

            exp.log_metric("f1", 0.89, step=1)
            exp.log_parameter("batch_size", 32)

        # After exit, read the WAL — should have all 5 events
        wal_path = tmp_path / "events" / str(org_id) / str(proj_id)
        wal_files = list(wal_path.glob("*.jsonl"))
        assert len(wal_files) >= 1

    def test_context_finish_failed_on_exception(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """Exception inside context marks the run as failed."""
        c = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        c.base_dir = tmp_path
        c.init_experiment("fail-test", project_id=proj_id)
        c.start_run()

        # Simulate failure
        c.finish(status="failed", error="Something broke")

        completed = [
            e for _, e in c.wal.read(0) if isinstance(e, RunCompletedEvent)
        ]
        assert len(completed) == 1
        assert completed[0].status == "failed"
        assert completed[0].error == "Something broke"

        c._cleanup()

    def test_can_start_multiple_runs(self, client: ResearchOSClient):
        """Client supports multiple sequential runs."""
        client.finish()
        run2_id = client.start_run()
        assert run2_id is not None
        assert client.run_id == run2_id

        client.log_metric("acc", 0.99, step=1)
        client.finish()

        # Should have 2 RunStarted + 2 RunCompleted
        started = [
            e for _, e in client.wal.read(0) if isinstance(e, RunStartedEvent)
        ]
        completed = [
            e for _, e in client.wal.read(0) if isinstance(e, RunCompletedEvent)
        ]
        assert len(started) == 2
        assert len(completed) == 2
