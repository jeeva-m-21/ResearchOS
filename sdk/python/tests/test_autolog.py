"""Tests for the autolog module (system/GPU metrics auto-logging)."""

import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import pytest

from researchos.autolog import AutoLogger, GPUCollector, collect_system_metrics
from researchos.autolog.system import (
    collect_all,
    collect_cpu,
    collect_disk,
    collect_memory,
)
from researchos.client import ResearchOSClient
from researchos.protocol.events import MetricLoggedEvent


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


@pytest.fixture
def proj_id() -> UUID:
    return uuid4()


# ── system.py tests ───────────────────────────────────────────────────


class TestSystemCollectors:
    """Tests for system metric collectors."""

    def test_collect_cpu_returns_expected_keys(self):
        """collect_cpu returns percent and count."""
        cpu = collect_cpu()
        assert "percent" in cpu
        assert "count" in cpu
        assert 0 <= cpu["percent"] <= 100
        assert cpu["count"] > 0

    def test_collect_memory_returns_expected_keys(self):
        """collect_memory returns total, available, used, percent."""
        mem = collect_memory()
        assert "total_gb" in mem
        assert "available_gb" in mem
        assert "used_gb" in mem
        assert "percent" in mem
        assert mem["total_gb"] > 0
        assert mem["available_gb"] > 0
        assert 0 <= mem["percent"] <= 100

    def test_collect_disk_returns_expected_keys(self):
        """collect_disk returns total, used, free, percent."""
        disk = collect_disk()
        assert "total_gb" in disk
        assert "used_gb" in disk
        assert "free_gb" in disk
        assert "percent" in disk
        assert disk["total_gb"] > 0

    def test_collect_all_returns_prefixed_keys(self):
        """collect_all returns flat dict with sys/ prefix."""
        metrics = collect_all()
        assert "sys/cpu_percent" in metrics
        assert "sys/memory_percent" in metrics
        assert "sys/disk_percent" in metrics
        assert "sys/memory_total_gb" in metrics
        assert "sys/memory_available_gb" in metrics
        assert "sys/memory_used_gb" in metrics
        assert "sys/disk_total_gb" in metrics
        assert "sys/disk_used_gb" in metrics
        assert "sys/disk_free_gb" in metrics
        assert isinstance(metrics["sys/cpu_percent"], float)
        assert 0 <= metrics["sys/memory_percent"] <= 100


# ── gpu.py tests ──────────────────────────────────────────────────────


class TestGPUCollector:
    """Tests for GPU collector (graceful fallback)."""

    def test_gpu_collector_not_available_in_ci(self):
        """GPUCollector.available returns False when no nvidia-smi."""
        collector = GPUCollector()
        assert not collector.available

    def test_gpu_collector_returns_empty_dict_when_not_available(self):
        """GPUCollector.collect returns empty dict when no GPU."""
        collector = GPUCollector()
        metrics = collector.collect()
        assert metrics == {}


# ── monitor.py tests ──────────────────────────────────────────────────


class TestAutoLogger:
    """Tests for the background AutoLogger."""

    def test_start_stop_does_not_crash(self):
        """AutoLogger starts and stops cleanly."""
        logged: List[Tuple[str, float, Optional[int]]] = []

        def log_fn(key: str, value: float, step: Optional[int] = None) -> None:
            logged.append((key, value, step))

        monitor = AutoLogger(log_metric_fn=log_fn)
        monitor.start(interval=0.5)
        assert monitor.is_running

        # Let it collect a few samples
        time.sleep(1.2)

        monitor.stop()
        assert not monitor.is_running

        # Should have logged some metrics
        assert len(logged) > 0

    def test_logger_metrics_have_sys_prefix(self):
        """Logged metrics from autolog use the 'sys/' prefix."""
        logged: Dict[str, List[float]] = {}

        def log_fn(key: str, value: float, step: Optional[int] = None) -> None:
            if key not in logged:
                logged[key] = []
            logged[key].append(value)

        monitor = AutoLogger(log_metric_fn=log_fn)
        monitor.start(interval=0.5)
        time.sleep(1.2)
        monitor.stop()

        assert any(k.startswith("sys/") for k in logged), (
            f"No sys/ prefixed metrics found in {list(logged.keys())}"
        )

    def test_double_start_is_idempotent(self):
        """Calling start() twice does not start two threads."""
        logged: List[str] = []

        def log_fn(key: str, value: float, step: Optional[int] = None) -> None:
            logged.append(key)

        monitor = AutoLogger(log_metric_fn=log_fn)
        monitor.start(interval=0.5)
        monitor.start(interval=0.5)  # Second call should be no-op
        time.sleep(0.6)
        monitor.stop()

        # Verify it collected something
        assert len(logged) > 0


# ── Integration test (client + autolog) ──────────────────────────────


class TestClientAutologIntegration:
    """Tests integrating autolog with the ResearchOSClient."""

    def test_autolog_logs_to_wal_via_client(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """AutoLogger writes metrics to the WAL through a ResearchOSClient."""
        c = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        c.base_dir = tmp_path
        c.init_experiment("autolog-test", project_id=proj_id)
        c.start_run()

        # Attach autologger
        monitor = AutoLogger(log_metric_fn=c.log_metric)
        monitor.start(interval=0.3)
        time.sleep(1.0)
        monitor.stop()

        # Read WAL — should have MetricLoggedEvent entries with sys/ prefix
        wal_events = c.wal.read(0)
        metric_events = [
            e for _, e in wal_events if isinstance(e, MetricLoggedEvent)
        ]
        sys_metrics = [e for e in metric_events if e.key.startswith("sys/")]

        assert len(sys_metrics) > 0, (
            f"No sys/ metrics found in WAL. Events: {[e.key for e in metric_events]}"
        )
        assert any("sys/cpu_percent" == e.key for e in sys_metrics)
        assert any("sys/memory_percent" == e.key for e in sys_metrics)

        c._cleanup()

    def test_enable_autolog_via_top_level(  # noqa: PLR0915
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """enable_autolog() function starts logging via global client."""
        # Reset module state
        import researchos
        researchos._client = None
        researchos._autologger = None

        # Init through top-level API
        researchos.init(
            "top-autolog-test",
            project="test-proj",
            api_key="test-key",
            organization_id=org_id,
        )

        # Monkey-patch for test isolation
        researchos._client.base_dir = tmp_path
        researchos._client.project_id = proj_id
        # Re-init with proper IDs
        researchos._client.init_experiment("top-autolog-test", project_id=proj_id)
        researchos._client.start_run()

        # Enable autolog
        researchos.enable_autolog(interval=0.3)
        time.sleep(1.0)
        researchos.disable_autolog()

        # Check WAL for sys/ metrics
        wal_events = researchos._client.wal.read(0)
        metric_events = [
            e for _, e in wal_events if isinstance(e, MetricLoggedEvent)
        ]
        sys_metrics = [e for e in metric_events if e.key.startswith("sys/")]

        assert len(sys_metrics) > 0, (
            f"No sys/ metrics found. Events: {[e.key for e in metric_events]}"
        )
        assert any("sys/cpu_percent" == e.key for e in sys_metrics)

        researchos._client._cleanup()
        researchos._client = None
        researchos._autologger = None


# ── Experiment context manager integration ──────────────────────────


class TestExperimentAutolog:
    """Tests for Experiment context manager with autolog enabled."""

    def test_experiment_with_autolog(
        self, tmp_path: Path, org_id: UUID, proj_id: UUID
    ):
        """Experiment with autolog=True auto-logs system metrics."""
        # We read the WAL before context exit to avoid closed-WAL issue
        client = ResearchOSClient(
            api_key="test-key",
            organization_id=org_id,
            offline=True,
        )
        client.base_dir = tmp_path
        client.init_experiment("autolog-exp", project_id=proj_id)
        client.start_run()

        monitor = AutoLogger(log_metric_fn=client.log_metric)
        monitor.start(interval=0.3)
        time.sleep(1.0)
        monitor.stop()

        client.log_metric("manual", 1.0, step=1)

        # Read WAL while client is still active
        wal_events = client.wal.read(0) if client.wal else []
        metric_events = [
            e for _, e in wal_events if isinstance(e, MetricLoggedEvent)
        ]
        sys_metrics = [e for e in metric_events if e.key.startswith("sys/")]

        assert len(sys_metrics) > 0, (
            f"No sys/ metrics found. All metric keys: {[e.key for e in metric_events]}"
        )

        client._cleanup()

    def test_collect_system_metrics_function(self):
        """collect_system_metrics (re-exported) returns expected metrics."""
        metrics = collect_system_metrics()
        assert "sys/cpu_percent" in metrics
        assert "sys/memory_percent" in metrics
        assert "sys/disk_percent" in metrics
