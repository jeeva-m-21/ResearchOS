"""Abstract compute provider interface for pluggable execution backends."""
from abc import ABC, abstractmethod

from .dto import ExecutionRequest, ExecutionResult


class ComputeProvider(ABC):
    """Abstract interface for notebook block execution providers.

    Implementations:
      - ``InAppProvider`` — runs code in-process via subprocess
      - ``LocalJupyterProvider`` — connects to a local Jupyter kernel
      - ``CloudGcpProvider`` — runs on GCP Vertex AI / AI Platform
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider name, e.g. 'in_app', 'local_jupyter', 'cloud_gcp'."""

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a block and return the result.

        Must handle timeouts gracefully and raise exceptions only for
        infrastructure errors (not execution failures). Execution errors
        are captured in ``ExecutionResult.status`` / ``error``.
        """

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the provider is available and ready to execute."""
