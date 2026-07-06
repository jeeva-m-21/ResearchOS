"""Orchestrates the AI chat: context, LLM calls, tool execution, streaming."""
from typing import AsyncIterator, Optional
from uuid import uuid4

from .dto import (
    AskRequest,
    ChatMessage,
    MessageRole,
    ToolDefinition,
)
from .tools import ResearchTool


class AIOrchestrator:
    """Orchestrates the AI chat — gathers context, calls LLM, executes tools,
    and streams the response back."""

    def __init__(
        self,
        llm_provider,
        tools: Optional[list[ResearchTool]] = None,
        db=None,
    ):
        self._llm = llm_provider
        self._tools = tools or []
        self._db = db
        self._sessions: dict[str, list[ChatMessage]] = {}

    @property
    def tool_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
            )
            for t in self._tools
        ]

    async def ask(
        self,
        request: AskRequest,
        organization_id: str,
    ) -> AsyncIterator[dict]:
        """Process a user message and stream the response.

        Yields dicts with keys:
          - type: "token" | "tool_call" | "tool_result" | "done"
          - content: varies by type
        """
        session_id = request.session_id or str(uuid4())

        # Build conversation
        system_prompt = self._build_system_prompt(
            organization_id, request.project_id
        )
        messages = [{"role": "system", "content": system_prompt}]

        # Restore session history
        for msg in self._sessions.get(session_id, []):
            messages.append(
                {"role": msg.role.value, "content": msg.content}
            )

        messages.append({"role": "user", "content": request.message})

        collected_content = ""
        max_rounds = 5

        for _ in range(max_rounds):
            tool_calls_to_process = []

            # Stream from LLM
            async for chunk in self._llm.chat_stream(
                messages=messages,
                tools=[t.model_dump() for t in self.tool_definitions],
                model=request.model,
            ):
                if chunk["type"] == "token":
                    collected_content += chunk["content"]
                    yield {"type": "token", "content": chunk["content"]}
                elif chunk["type"] == "tool_call":
                    tool_calls_to_process.append(chunk)
                    yield {
                        "type": "tool_call",
                        "content": {
                            "id": chunk["id"],
                            "name": chunk["name"],
                            "arguments": chunk["arguments"],
                        },
                    }

            if not tool_calls_to_process:
                break

            for tc in tool_calls_to_process:
                tool = next(
                    (t for t in self._tools if t.name == tc["name"]), None
                )
                if tool:
                    try:
                        result = await tool.execute(
                            **tc["arguments"],
                            organization_id=organization_id,
                        )
                    except Exception as exc:
                        result = f"Error executing {tc['name']}: {exc}"
                else:
                    result = f"Unknown tool: {tc['name']}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    }
                )
                yield {
                    "type": "tool_result",
                    "content": {"name": tc["name"], "result": result},
                }

        # Persist session
        self._sessions.setdefault(session_id, [])
        self._sessions[session_id].append(
            ChatMessage(
                role=MessageRole.USER, content=request.message
            )
        )
        self._sessions[session_id].append(
            ChatMessage(
                role=MessageRole.ASSISTANT, content=collected_content
            )
        )
        # Keep last 50 messages
        if len(self._sessions[session_id]) > 50:
            self._sessions[session_id] = self._sessions[session_id][-50:]

        yield {"type": "done", "content": {"session_id": session_id}}

    def _build_system_prompt(
        self,
        organization_id: str,
        project_id: Optional[str] = None,
    ) -> str:
        """Build the system prompt with context about available tools."""
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}" for t in self._tools
        )
        parts = [
            (
                "You are ResearchOS AI, an expert research assistant "
                "integrated into a research platform.\n\n"
            ),
            (
                "You have access to the user's research workspace "
                f"(organization: {organization_id})\n"
            ),
        ]
        if project_id:
            parts.append(f"Current project: {project_id}\n")
        parts.append(f"\nAvailable tools:\n{tools_desc}\n\n")
        parts.append(
            "Guidelines:\n"
            "- Be concise but thorough in your analysis\n"
            "- When referencing experiments, notebooks, or other research objects, "
            "always include their IDs\n"
            "- If you need more information, use the tools available to you\n"
            "- You can search across all research objects, read experiments "
            "with their metrics, and inspect notebook blocks\n"
            "- Present data in a structured, readable format\n"
            "- When discussing metrics, show relevant numbers and trends\n"
            "- If a tool returns nothing, suggest alternative searches\n"
            "- Keep responses focused on research content\n"
            "- Never make up data — if you don't know something, "
            "use a tool to find out or say so\n"
        )
        return "".join(parts)
