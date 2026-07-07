"""AI Chat Assistant API endpoints."""
import json
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.dependencies.auth import get_current_org
from src.application.ai import (
    AIOrchestrator,
    AskRequest,
    GetBlockContentTool,
    GetExperimentTool,
    GetNotebookTool,
    GetPaperTool,
    ListExperimentsTool,
    ListNotebooksTool,
    ListPapersTool,
    ModelInfo,
    SearchTool,
)
from src.infrastructure.adapters.llm import (
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
)

router = APIRouter(prefix="/v1/ask", tags=["ask"])


# --- Provider registry ---

def _get_llm_providers() -> dict[str, dict]:
    """Discover available LLM providers from environment config."""
    providers = {}

    if os.getenv("OPENAI_API_KEY"):
        providers["openai"] = {
            "provider": OpenAIProvider(),
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        }

    if os.getenv("ANTHROPIC_API_KEY"):
        providers["anthropic"] = {
            "provider": AnthropicProvider(),
            "models": [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
            ],
        }

    # Ollama is always available (local)
    providers["ollama"] = {
        "provider": OllamaProvider(),
        "models": ["llama3.2", "llama3.1", "mistral", "codellama"],
    }

    return providers


def _create_orchestrator() -> AIOrchestrator:
    """Create the AI orchestrator with all available providers and tools."""
    providers = _get_llm_providers()
    # Use first available provider, defaulting to Ollama
    primary_provider = next(iter(providers.values()))["provider"]

    tools = [
        SearchTool(),
        GetExperimentTool(),
        GetNotebookTool(),
        ListExperimentsTool(),
        ListNotebooksTool(),
        GetBlockContentTool(),
        GetPaperTool(),
        ListPapersTool(),
    ]

    return AIOrchestrator(llm_provider=primary_provider, tools=tools)


# --- Dependencies ---

_orchestrator_cache: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    global _orchestrator_cache
    if _orchestrator_cache is None:
        _orchestrator_cache = _create_orchestrator()
    return _orchestrator_cache


# --- Endpoints ---


@router.post("")
async def ask(
    request: AskRequest,
    org_id: Optional[UUID] = Depends(get_current_org),
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
):
    """Send a message to the AI chat assistant.

    Returns a Server-Sent Events (SSE) stream with:
      - token events: the AI's response tokens
      - tool_call events: when the AI calls a tool
      - tool_result events: results of tool execution
      - done event: signals completion
    """
    if not request.stream:
        # Non-streaming support
        collected = []
        org_str = str(org_id) if org_id else ""
        async for chunk in orchestrator.ask(request, org_str):
            if chunk["type"] == "token":
                collected.append(chunk["content"])
            elif chunk["type"] == "done":
                return {
                    "message": "".join(collected),
                    "session_id": chunk["content"]["session_id"],
                }
        return {"message": "".join(collected), "session_id": ""}

    async def event_stream():
        org_str = str(org_id) if org_id else ""
        async for chunk in orchestrator.ask(request, org_str):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models")
async def list_models() -> list[ModelInfo]:
    """List available AI models."""
    providers = _get_llm_providers()
    models: list[ModelInfo] = []
    for provider_name, config in providers.items():
        for model_id in config["models"]:
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider=provider_name,
                    description=f"{provider_name.title()} model: {model_id}",
                    available=True,
                )
            )
    return models
