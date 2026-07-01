import httpx


class DeepSeekProvider:
    """Concrete LLMProvider. Swap freely via the registry."""

    def __init__(self, model: str = "deepseek-v4-pro") -> None:
        self.model = model
        self._client = httpx.Client(timeout=600)

    def complete(self, prompt: str, **kwargs: object) -> str:
        # TODO: wire the real DeepSeek / opencode-compatible endpoint
        raise NotImplementedError
