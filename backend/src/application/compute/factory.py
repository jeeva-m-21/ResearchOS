"""Compute factory — register and resolve execution providers."""

from .dto import ExecutionRequest, ExecutionResult
from .provider import ComputeProvider


class ComputeFactory:
    """Registry of ``ComputeProvider`` implementations.

    Usage::

        factory = ComputeFactory()
        factory.register(InAppProvider())

        provider = factory.get("in_app")
        result = await provider.execute(request)
    """

    def __init__(self) -> None:
        self._providers: dict[str, ComputeProvider] = {}

    def register(self, provider: ComputeProvider) -> None:
        """Register a compute provider by its ``.name``."""
        if provider.name in self._providers:
            raise ValueError(
                f"Provider '{provider.name}' is already registered"
            )
        self._providers[provider.name] = provider

    def get(self, name: str) -> ComputeProvider:
        """Resolve a provider by name.

        Raises:
            KeyError: If no provider is registered with the given name.
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise KeyError(
                f"Unknown compute provider '{name}'. "
                f"Available providers: {available}"
            )
        return self._providers[name]

    @property
    def available_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    async def execute(
        self, request: ExecutionRequest
    ) -> ExecutionResult:
        """Execute a block through the appropriate provider."""
        provider = self.get(request.provider)
        return await provider.execute(request)
