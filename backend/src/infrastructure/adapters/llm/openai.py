"""OpenAI LLM provider."""
import json
import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible LLM provider (GPT-4o, GPT-4, GPT-3.5, etc.)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        self._default_model = os.getenv("OPENAI_MODEL", "gpt-4o")

    @property
    def model_id(self) -> str:
        return self._default_model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[dict]:
        kwargs = dict(
            model=model or self._default_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": False},
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**kwargs)

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # Text token
            if delta.content:
                yield {"type": "token", "content": delta.content}

            # Tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    # The first chunk has the function name, subsequent have arguments
                    if tc.function and tc.function.name:
                        yield {
                            "type": "tool_call",
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": (
                                json.loads(tc.function.arguments)
                                if tc.function.arguments
                                else {}
                            ),
                        }
