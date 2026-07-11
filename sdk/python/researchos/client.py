"""ResearchOS SDK client with offline-first WAL persistence.

The client writes all events to a crash-safe Write-Ahead Log (JSONL)
and syncs them to the backend in a background thread.
"""

import os
import threading
import time
from pathlib import Path
from typing import Optional, Any, Union
from uuid import UUID, uuid4

from .protocol.events import (
    ExperimentStartedEvent,
    RunStartedEvent,
    RunCompletedEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
)
from .sync import Syncer
from .utils.backoff import ExponentialBackoff
from .wal import WAL


class ResearchOSClient:
    """Main SDK client with offline-first WAL persistence.

    Usage:
        client = ResearchOSClient(api_key="...", organization_id=UUID(...))
        client.init_experiment("my-experiment", project_id=UUID(...))
        client.start_run(parameters={"lr": 0.001})
        client.log_metric("accuracy", 0.95, step=1)
        client.log_parameter("learning_rate", 0.001)
        client.finish()
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        offline: bool = False,
    ):
        self.api_url = api_url or os.getenv(
            "RESEARCHOS_API_URL", "http://localhost:8000"
        )
        self.api_key = api_key or os.getenv("RESEARCHOS_API_KEY")
        self.organization_id = organization_id
        self.offline = offline

        # Runtime state
        self.experiment_id: Optional[UUID] = None
        self.project_id: Optional[UUID] = None
        self.run_id: Optional[UUID] = None
        self.step_counters: dict[str, int] = {}

        # Persistence
        self.base_dir = Path.home() / ".researchos"
        self.wal: Optional[WAL] = None
        self._syncer: Optional[Syncer] = None
        self._sync_thread: Optional[threading.Thread] = None
        self._running = False

    # ── Experiment lifecycle ────────────────────────────────────────────

    def init_experiment(
        self,
        name: str,
        project: Optional[str] = None,
        project_id: Optional[UUID] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> UUID:
        """Initialize a new experiment and create its WAL.

        Args:
            name: Experiment name.
            project: Project name or ID string.
            project_id: Explicit project UUID (overrides project string).
            description: Optional description.
            tags: Optional list of tags.

        Returns:
            The experiment UUID.
        """
        if not self.organization_id:
            raise ValueError(
                "organization_id is required. Pass it to the constructor "
                "or set the RESEARCHOS_ORG_ID environment variable."
            )

        # Resolve project ID
        if project_id:
            self.project_id = project_id
        elif project:
            # For now, use a deterministic UUID from the project name
            # In production, this would call the backend to resolve
            self.project_id = uuid4()

        if not self.project_id:
            self.project_id = uuid4()

        # Generate experiment ID
        self.experiment_id = uuid4()

        # Create WAL
        self.wal = WAL(
            base_dir=self.base_dir,
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
        )

        # Append experiment started event
        event = ExperimentStartedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            name=name,
            description=description,
            tags=tags or [],
        )
        self.wal.append(event)

        # Start background sync
        if not self.offline:
            self._start_sync()

        return self.experiment_id

    def start_run(self, parameters: Optional[dict] = None) -> UUID:
        """Start a new run within the experiment.

        Args:
            parameters: Optional dict of run parameters.

        Returns:
            The run UUID.

        Raises:
            RuntimeError: If no experiment has been initialized.
        """
        if not self.experiment_id or not self.wal:
            raise RuntimeError(
                "No active experiment. Call init_experiment() first."
            )
        assert self.wal is not None  # narrow for type checker
        assert self.organization_id is not None

        self.run_id = uuid4()

        # Auto-increment run number from existing WAL events
        run_number = 1  # TODO: count existing runs from WAL

        event = RunStartedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            run_number=run_number,
            parameters=parameters or {},
        )
        self.wal.append(event)

        return self.run_id

    # ── Data logging ───────────────────────────────────────────────────

    def log_metric(
        self,
        key: str,
        value: float,
        step: Optional[int] = None,
        wall_time: Optional[float] = None,
        **metadata: Any,
    ) -> None:
        """Log a metric value to the current run.

        Raises:
            RuntimeError: If no active run.
        """
        if not self.run_id:
            raise RuntimeError(
                "No active run. Call start_run() first."
            )
        assert self.wal is not None
        assert self.organization_id is not None

        if step is None:
            self.step_counters[key] = self.step_counters.get(key, 0) + 1
            step = self.step_counters[key]

        event = MetricLoggedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            key=key,
            value=value,
            step=step,
            wall_time=wall_time or time.time(),
            metadata=metadata,
        )
        self.wal.append(event)

    def log_parameter(self, key: str, value: Any) -> None:
        """Log a parameter to the current run.

        Raises:
            RuntimeError: If no active run.
        """
        if not self.run_id:
            raise RuntimeError(
                "No active run. Call start_run() first."
            )
        assert self.wal is not None
        assert self.organization_id is not None

        value_type = self._infer_type(value)

        event = ParameterSetEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            key=key,
            value=str(value),
            value_type=value_type,
        )
        self.wal.append(event)

    def finish(
        self,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> None:
        """Finish the current run.

        Args:
            status: One of "completed", "failed", "cancelled".
            error: Optional error description (for failed runs).
        """
        if not self.run_id:
            return
        assert self.wal is not None

        event = RunCompletedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            status=status,  # type: ignore
            error=error,
            duration_ms=self._compute_duration(),
        )
        self.wal.append(event)
        self.run_id = None

    # ── Synchronization ────────────────────────────────────────────────

    def _start_sync(self) -> None:
        """Start the background sync thread."""
        self._syncer = Syncer(
            base_url=self.api_url,
            api_key=self.api_key,
        )

        self._running = True

        def _sync_loop() -> None:
            backoff = ExponentialBackoff(
                base_delay=1.0,
                max_delay=60.0,
                jitter=True,
            )
            assert self._syncer is not None
            syncer: Syncer = self._syncer  # local ref for type narrowing
            while self._running:
                if not self.wal:
                    time.sleep(5.0)
                    continue
                try:
                    result = syncer.sync(self.wal)
                    if result.get("error"):
                        # Log error but don't spam on transient failures
                        delay = backoff.get_delay()
                        time.sleep(delay)
                    else:
                        backoff.reset()
                except Exception:
                    delay = backoff.get_delay()
                    time.sleep(delay)

                # Poll interval even when idle
                time.sleep(5.0)

        self._sync_thread = threading.Thread(target=_sync_loop, daemon=True)
        self._sync_thread.start()

    # ── Cleanup ─────────────────────────────────────────────────────────

    def _cleanup(self) -> None:
        """Close the WAL and stop sync."""
        self._running = False
        if self._syncer:
            self._syncer = None
        if self.wal:
            self.wal.close()
            self.wal = None

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _infer_type(value: Any) -> str:
        """Infer the parameter value type string."""
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, dict):
            return "json"
        return "string"

    def _compute_duration(self) -> Optional[int]:
        """Compute run duration in ms (placeholder)."""
        # TODO: Track run start time and compute actual duration
        return None
