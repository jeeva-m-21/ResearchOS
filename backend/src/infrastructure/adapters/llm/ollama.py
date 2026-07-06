"""Ollama LLM provider for local models."""
import json
import os
from typing import AsyncIterator, Optional

import httpx

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama provider for local models (llama3, mistral, codellama, etc.).

    Requires Ollama running locally (default: http://localhost:11434).
    """

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120)
        self._default_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    @property
    def model_id(self) -> str:
        return self._default_model

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[dict]:
        payload = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("done"):
                    break

                msg = data.get("message", {})
                if msg.get("content"):
                    yield {"type": "token", "content": msg["content"]}

                # Ollama supports tool calls in newer versions
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        yield {
                            "type": "tool_call",
                            "id": tc.get("id", ""),
                            "name": tc["function"]["name"],
                            "arguments": tc["function"].get("arguments", {}),
                        }
