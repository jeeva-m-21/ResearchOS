"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class LLMProvider(ABC):
    """Abstract LLM provider that supports streaming chat with tool calling."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the default model identifier (e.g. 'gpt-4o')."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g. 'openai', 'anthropic')."""
        ...

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a chat completion.

        Each yielded dict must have a "type" key:
          - {"type": "token", "content": "..."}  for a text token
          - {"type": "tool_call", "id": "...", "name": "...",
             "arguments": {...}}  for a tool call

        Args:
            messages: List of message dicts with "role" and "content" keys.
            tools: List of tool definition dicts (OpenAI-compatible JSON Schema format).
            model: Optional model override.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature.

        Yields:
            Dicts with type "token" or "tool_call".
        """
        ...
