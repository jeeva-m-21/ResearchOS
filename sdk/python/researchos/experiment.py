"""High-level Experiment context manager with WAL persistence.

Usage:
    with Experiment("my-experiment", project="my-project") as exp:
        exp.log_metric("accuracy", 0.95)
        exp.log_parameter("lr", 0.001)
"""

from typing import Optional
from uuid import UUID

from .client import ResearchOSClient


class Experiment:
    """Experiment context manager that auto-initializes and persists via WAL.

    The context manager wraps ResearchOSClient and handles:
    - Creating the experiment and first run on __enter__
    - Finishing the run and cleaning up on __exit__
    - Auto-failing the run if an exception occurred
    """

    def __init__(
        self,
        name: str,
        project: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        offline: bool = False,
    ):
        self._name = name
        self._project = project
        self._offline = offline

        self._client = ResearchOSClient(
            api_key=api_key,
            organization_id=organization_id,
            offline=offline,
        )

    def __enter__(self) -> "Experiment":
        """Initialize experiment + start a run."""
        self._client.init_experiment(self._name, project=self._project)
        self._client.start_run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Finish the run and close WAL."""
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
