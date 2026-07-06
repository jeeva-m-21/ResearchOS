"""Anthropic LLM provider (Claude)."""
import os
from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic-compatible LLM provider (Claude 3 Opus, Sonnet, Haiku)."""

    def __init__(self, api_key: Optional[str] = None):
        self._client = AsyncAnthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
        )
        self._default_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    @property
    def model_id(self) -> str:
        return self._default_model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[dict]:
        # Convert OpenAI-format messages to Anthropic format
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "tool":
                # Anthropic tool results use a different format
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": msg["content"],
                        }
                    ],
                })
            else:
                anthropic_messages.append(msg)

        # Convert tools to Anthropic format
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for t in tools:
                has_fn = "function" in t
                fn = t.get("function", {})
                name = fn.get("name") if has_fn else t.get("name")
                desc = fn.get("description", "") if has_fn else t.get("description", "")
                params = fn.get("parameters", {}) if has_fn else t.get("parameters", {})
                anthropic_tools.append({
                    "name": name,
                    "description": desc,
                    "input_schema": params,
                })

        kwargs = dict(
            model=model or self._default_model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        if system_msg:
            kwargs["system"] = system_msg
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        async with self._client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"type": "token", "content": event.delta.text}
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        yield {
                            "type": "tool_call",
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "arguments": (
                                event.content_block.input
                                if isinstance(event.content_block.input, dict)
                                else {}
                            ),
                        }
