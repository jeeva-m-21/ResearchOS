from typing import Any, Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str, **kwargs: Any) -> str: ...
