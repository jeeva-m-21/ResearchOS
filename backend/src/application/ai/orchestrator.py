"""Orchestrates the AI chat: context, LLM calls, tool execution, streaming."""
from typing import AsyncIterator, Optional
from uuid import UUID, uuid4

from infrastructure.database import Database

from .dto import (
    AskRequest,
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
        db: Optional[Database] = None,
    ):
        self._llm = llm_provider
        self._tools = tools or []
        self._db = db

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

    async def _load_session_history(
        self, session_id: str, organization_id: str
    ) -> list[dict]:
        """Load message history from DB for an existing session."""
        if not self._db or not self._db.pool:
            return []
        rows = await self._db.fetch_all(
            """
            SELECT role, content
            FROM ai_messages
            WHERE session_id = (
                SELECT id FROM agent_sessions
                WHERE session_id = $1 AND organization_id = $2
                AND deleted_at IS NULL
            )
            ORDER BY created_at ASC
            """,
            session_id,
            organization_id,
        )
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def _save_user_message(
        self, session_id: str, organization_id: str, user_id: str,
        content: str, model: str,
    ) -> str:
        """Persist a user message to the DB. Returns the session row UUID."""
        if not self._db or not self._db.pool:
            return session_id

        # Upsert session
        row = await self._db.fetch_one(
            """
            SELECT id FROM agent_sessions
            WHERE session_id = $1 AND organization_id = $2
            """,
            session_id,
            organization_id,
        )
        if row:
            session_row_id = row["id"]
            await self._db.execute(
                "UPDATE agent_sessions SET updated_at = NOW() WHERE id = $1",
                session_row_id,
            )
        else:
            session_row_id = uuid4()
            await self._db.execute(
                """
                INSERT INTO agent_sessions
                    (id, organization_id, user_id, session_id, model)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_row_id,
                UUID(organization_id),
                UUID(user_id) if user_id else UUID(organization_id),
                session_id,
                model,
            )

        # Save user message
        await self._db.execute(
            """
            INSERT INTO ai_messages (session_id, organization_id, role, content)
            VALUES ($1, $2, 'user', $3)
            """,
            session_row_id,
            UUID(organization_id),
            content,
        )
        return str(session_row_id)

    async def _save_assistant_message(
        self, session_row_id: str, organization_id: str, content: str,
    ) -> None:
        """Persist an assistant message to the DB."""
        if not self._db or not self._db.pool:
            return
        await self._db.execute(
            """
            INSERT INTO ai_messages (session_id, organization_id, role, content)
            VALUES ($1, $2, 'assistant', $3)
            """,
            UUID(session_row_id),
            UUID(organization_id),
            content,
        )

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

        # Restore session history from DB
        history = await self._load_session_history(session_id, organization_id)
        messages.extend(history)

        messages.append({"role": "user", "content": request.message})

        # Persist user message + get session row ID
        session_row_id = await self._save_user_message(
            session_id, organization_id, "",
            request.message, request.model,
        )

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

        # Persist assistant response to DB
        await self._save_assistant_message(
            session_row_id, organization_id, collected_content,
        )

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
            "with their metrics, inspect notebook blocks, and query papers\n"
            "- Present data in a structured, readable format\n"
            "- When discussing metrics, show relevant numbers and trends\n"
            "- If a tool returns nothing, suggest alternative searches\n"
            "- Keep responses focused on research content\n"
            "- Never make up data — if you don't know something, "
            "use a tool to find out or say so\n"
        )
        return "".join(parts)
