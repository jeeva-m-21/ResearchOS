"""Tests for compute factory and execution providers."""
from uuid import UUID, uuid4

import pytest
from application.compute import ComputeFactory, ExecutionRequest, ExecutionResult
from application.compute.provider import ComputeProvider
from infrastructure.compute import InAppProvider

# ── Fake provider for testing ──────────────────────────────────────────


class FakeProvider(ComputeProvider):
    """A compute provider that returns canned results (no subprocess)."""

    def __init__(self, name: str = "fake") -> None:
        self._name = name
        self._ok = True

    @property
    def name(self) -> str:
        return self._name

    async def health(self) -> bool:
        return self._ok

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            execution_id=uuid4(),
            status="success",
            output=f"Fake executed: {request.content[:20]}...",
            error=None,
            duration_ms=42,
            provider=self._name,
        )


class FailingProvider(ComputeProvider):
    """A compute provider that always fails."""

    @property
    def name(self) -> str:
        return "failing"

    async def health(self) -> bool:
        return False

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            execution_id=uuid4(),
            status="failed",
            output=None,
            error="Intentional failure",
            duration_ms=10,
            provider="failing",
        )


# ── Factory tests ──────────────────────────────────────────────────────


class TestComputeFactory:
    def test_register_and_get(self) -> None:
        factory = ComputeFactory()
        provider = FakeProvider("mock")
        factory.register(provider)
        assert factory.get("mock") is provider

    def test_register_duplicate_raises(self) -> None:
        factory = ComputeFactory()
        factory.register(FakeProvider("dup"))
        with pytest.raises(ValueError, match="already registered"):
            factory.register(FakeProvider("dup"))

    def test_get_unknown_raises(self) -> None:
        factory = ComputeFactory()
        with pytest.raises(KeyError, match="Unknown compute provider"):
            factory.get("nonexistent")

    def test_available_providers(self) -> None:
        factory = ComputeFactory()
        factory.register(FakeProvider("a"))
        factory.register(FakeProvider("b"))
        assert sorted(factory.available_providers) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_execute_through_factory(self) -> None:
        factory = ComputeFactory()
        factory.register(FakeProvider("mock"))

        result = await factory.execute(
            ExecutionRequest(
                block_id=uuid4(),
                notebook_id=uuid4(),
                block_content_id=uuid4(),
                block_type="python",
                content="print('hello')",
                organization_id=uuid4(),
                created_by=uuid4(),
                provider="mock",
            )
        )
        assert result.status == "success"
        assert "hello" in (result.output or "")


# ── InAppProvider tests ────────────────────────────────────────────────


class TestInAppProvider:
    @pytest.mark.asyncio
    async def test_name(self) -> None:
        provider = InAppProvider()
        assert provider.name == "in_app"

    @pytest.mark.asyncio
    async def test_health(self) -> None:
        provider = InAppProvider()
        assert await provider.health() is True

    @pytest.mark.asyncio
    async def test_execute_python_success(self) -> None:
        provider = InAppProvider()
        result = await provider.execute(
            ExecutionRequest(
                block_id=uuid4(),
                notebook_id=uuid4(),
                block_content_id=uuid4(),
                block_type="python",
                content="print('hello world')",
                organization_id=uuid4(),
                created_by=uuid4(),
                provider="in_app",
            )
        )
        assert result.status == "success", f"Got {result.status}: {result.error}"
        assert result.output is not None
        assert "hello world" in result.output
        assert result.duration_ms is not None
        assert result.provider == "in_app"
        assert isinstance(result.execution_id, UUID)

    @pytest.mark.asyncio
    async def test_execute_python_timeout(self) -> None:
        provider = InAppProvider()
        result = await provider.execute(
            ExecutionRequest(
                block_id=uuid4(),
                notebook_id=uuid4(),
                block_content_id=uuid4(),
                block_type="python",
                content="import time; time.sleep(5)",
                organization_id=uuid4(),
                created_by=uuid4(),
                timeout_ms=500,  # Short timeout
                provider="in_app",
            )
        )
        assert result.status == "failed", f"Expected failed, got {result.status}"
        assert "timed out" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_execute_unsupported_type(self) -> None:
        provider = InAppProvider()
        result = await provider.execute(
            ExecutionRequest(
                block_id=uuid4(),
                notebook_id=uuid4(),
                block_content_id=uuid4(),
                block_type="rust",
                content="fn main() {}",
                organization_id=uuid4(),
                created_by=uuid4(),
                provider="in_app",
            )
        )
        assert result.status == "failed"
        assert "not yet supported" in (result.error or "")


# ── Full integration: factory + InAppProvider ──────────────────────────


class TestComputeIntegration:
    @pytest.mark.asyncio
    async def test_factory_with_in_app(self) -> None:
        factory = ComputeFactory()
        factory.register(InAppProvider())

        result = await factory.execute(
            ExecutionRequest(
                block_id=uuid4(),
                notebook_id=uuid4(),
                block_content_id=uuid4(),
                block_type="python",
                content="print('integration test')",
                organization_id=uuid4(),
                created_by=uuid4(),
                provider="in_app",
            )
        )
        assert result.status == "success"
        assert "integration test" in (result.output or "")
        assert result.provider == "in_app"

    @pytest.mark.asyncio
    async def test_factory_with_unknown_provider(self) -> None:
        factory = ComputeFactory()
        factory.register(InAppProvider())

        with pytest.raises(KeyError, match="Unknown compute provider"):
            await factory.execute(
                ExecutionRequest(
                    block_id=uuid4(),
                    notebook_id=uuid4(),
                    block_content_id=uuid4(),
                    block_type="python",
                    content="print('x')",
                    organization_id=uuid4(),
                    created_by=uuid4(),
                    provider="does_not_exist",
                )
            )
