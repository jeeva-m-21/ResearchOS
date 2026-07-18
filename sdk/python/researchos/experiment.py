"""High-level Experiment context manager with WAL persistence and optional autolog.

Usage:
    with Experiment("my-experiment", project="my-project") as exp:
        exp.log_metric("accuracy", 0.95)
        exp.log_parameter("lr", 0.001)

    # With automatic system/GPU metrics:
    with Experiment("my-experiment", autolog=True, autolog_interval=5.0) as exp:
        # CPU, memory, disk, and GPU metrics logged automatically
        ...
"""

from typing import Optional
from uuid import UUID

from .autolog import AutoLogger
from .client import ResearchOSClient


class Experiment:
    """Experiment context manager that auto-initializes and persists via WAL.

    The context manager wraps ResearchOSClient and handles:
    - Creating the experiment and first run on __enter__
    - Finishing the run and cleaning up on __exit__
    - Auto-failing the run if an exception occurred
    - Optionally auto-logging system/GPU metrics (via autolog)
    """

    def __init__(
        self,
        name: str,
        project: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        offline: bool = False,
        autolog: bool = False,
        autolog_interval: float = 5.0,
    ):
        self._name = name
        self._project = project
        self._offline = offline
        self._autolog_enabled = autolog
        self._autolog_interval = autolog_interval

        self._client = ResearchOSClient(
            api_key=api_key,
            organization_id=organization_id,
            offline=offline,
        )
        self._autologger: Optional[AutoLogger] = None

    def __enter__(self) -> "Experiment":
        """Initialize experiment + start a run."""
        self._client.init_experiment(self._name, project=self._project)
        self._client.start_run()

        # Start autolog if enabled
        if self._autolog_enabled:
            self._autologger = AutoLogger(
                log_metric_fn=self._client.log_metric,
            )
            self._autologger.start(interval=self._autolog_interval)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Finish the run, stop autolog, and close WAL."""
        # Stop autolog first
        if self._autologger is not None:
            self._autologger.stop()
            self._autologger = None

        if exc_type is not None:
            self._client.finish(status="failed", error=str(exc_val))
        else:
            self._client.finish()
        self._client._cleanup()

    # ── convenience proxies ──────────────────────────────────────────────

    def log_metric(
        self,
        key: str,
        value: float,
        step: Optional[int] = None,
        **metadata,
    ) -> None:
        """Log a metric to the current run."""
        self._client.log_metric(key, value, step=step, **metadata)

    def log_parameter(self, key: str, value) -> None:
        """Log a parameter to the current run."""
        self._client.log_parameter(key, value)
