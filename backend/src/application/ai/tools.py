"""Research-aware tools for the AI assistant."""
from abc import ABC, abstractmethod
from typing import Any


class ResearchTool(ABC):
    """Abstract base for a research tool the AI can call."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result."""
        ...


class SearchTool(ResearchTool):
    """Search across all research objects using hybrid search."""

    @property
    def name(self) -> str:
        return "search_research"

    @property
    def description(self) -> str:
        return (
            "Search across experiments, notebooks, artifacts, and papers "
            "using semantic and keyword search."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by node type",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 10,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, **kwargs) -> str:
        types = kwargs.get("types")
        limit = kwargs.get("limit", 10)
        org_id = kwargs.get("organization_id")
        try:
            from src.application.search.service import SearchService
            from src.infrastructure.adapters.embeddings.local import (
                LocalEmbeddingAdapter,
            )
            from src.infrastructure.database import db

            search = SearchService(
                db=db,
                embedding_adapter=LocalEmbeddingAdapter(),
            )
            results = await search.search(
                query=query,
                organization_id=org_id,
                types=types,
                limit=limit,
            )
            if not results.results:
                return f"No results found for '{query}'."
            lines = [f"**Search results for '{query}'**:\n"]
            for r in results.results:
                lines.append(f"- [{r.node_type}] {r.title} (score: {r.score:.2f})")
            return "\n".join(lines)
        except Exception as exc:
            return f"Search error: {exc}"


class GetExperimentTool(ResearchTool):
    """Get experiment details with runs and metrics."""

    @property
    def name(self) -> str:
        return "get_experiment"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about an experiment including "
            "its runs and metrics."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "experiment_id": {
                    "type": "string",
                    "description": "The experiment UUID",
                }
            },
            "required": ["experiment_id"],
        }

    async def execute(self, experiment_id: str, **kwargs) -> str:
        org_id = kwargs.get("organization_id")
        try:
            from src.infrastructure.database import db

            experiment = await db.fetch_one(
                """
                SELECT id, name, description, status, project_id,
                       parameters, tags, created_by, created_at
                FROM experiments
                WHERE id = $1::uuid AND organization_id = $2::uuid
                  AND deleted_at IS NULL
                """,
                experiment_id,
                org_id,
            )
            if not experiment:
                return f"Experiment {experiment_id} not found."

            runs = await db.fetch_all(
                """
                SELECT id, run_number, status, started_at, ended_at,
                       duration_ms
                FROM runs
                WHERE experiment_id = $1::uuid AND organization_id = $2::uuid
                  AND deleted_at IS NULL
                ORDER BY run_number DESC
                LIMIT 20
                """,
                experiment_id,
                org_id,
            )

            created_str = (
                experiment["created_at"].strftime("%Y-%m-%d %H:%M")
                if experiment["created_at"]
                else "N/A"
            )
            lines = [
                f"**Experiment: {experiment['name']}**",
                f"- Status: {experiment['status']}",
                f"- Description: {experiment['description'] or 'N/A'}",
                f"- Created: {created_str}",
                "",
                f"**Runs ({len(runs)}):**",
            ]
            for run in runs:
                dur = run["duration_ms"]
                dur_str = f"{dur}ms" if dur else "N/A"
                lines.append(
                    f"- Run #{run['run_number']}: {run['status']} "
                    f"(duration: {dur_str})"
                )

            return "\n".join(lines)
        except Exception as exc:
            return f"Error fetching experiment: {exc}"


class GetNotebookTool(ResearchTool):
    """Get notebook with blocks and content."""

    @property
    def name(self) -> str:
        return "get_notebook"

    @property
    def description(self) -> str:
        return (
            "Get a notebook with all its blocks and their current content."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "notebook_id": {
                    "type": "string",
                    "description": "The notebook UUID",
                }
            },
            "required": ["notebook_id"],
        }

    async def execute(self, notebook_id: str, **kwargs) -> str:
        return (
            f"[Notebook {notebook_id}] "
            "Details would be fetched here when DB is available."
        )


class ListExperimentsTool(ResearchTool):
    """List experiments in a project."""

    @property
    def name(self) -> str:
        return "list_experiments"

    @property
    def description(self) -> str:
        return "List experiments in the current project."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Optional project UUID to filter by",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 20,
                },
            },
        }

    async def execute(self, **kwargs) -> str:
        org_id = kwargs.get("organization_id")
        project_id = kwargs.get("project_id")
        limit = kwargs.get("limit", 20)
        try:
            from src.infrastructure.database import db

            if project_id:
                rows = await db.fetch_all(
                    """
                    SELECT id, name, status, created_at
                    FROM experiments
                    WHERE organization_id = $1::uuid
                      AND project_id = $2::uuid
                      AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    org_id,
                    project_id,
                    limit,
                )
            else:
                rows = await db.fetch_all(
                    """
                    SELECT id, name, status, created_at
                    FROM experiments
                    WHERE organization_id = $1::uuid
                      AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    org_id,
                    limit,
                )

            if not rows:
                return "No experiments found."

            lines = [f"**Experiments ({len(rows)}):**\n"]
            for r in rows:
                created = (
                    r["created_at"].strftime("%Y-%m-%d")
                    if r["created_at"]
                    else "N/A"
                )
                lines.append(f"- {r['name']} [{r['status']}] (created: {created})")
            return "\n".join(lines)
        except Exception as exc:
            return f"Error listing experiments: {exc}"


class ListNotebooksTool(ResearchTool):
    """List notebooks in a project."""

    @property
    def name(self) -> str:
        return "list_notebooks"

    @property
    def description(self) -> str:
        return "List notebooks in the current project."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Optional project UUID to filter by",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 20,
                },
            },
        }

    async def execute(self, **kwargs) -> str:
        limit = kwargs.get("limit", 20)
        return (
            f"[List notebooks (limit={limit})] "
            "Would return notebook list here when DB is available."
        )


class GetBlockContentTool(ResearchTool):
    """Get specific block content."""

    @property
    def name(self) -> str:
        return "get_block_content"

    @property
    def description(self) -> str:
        return (
            "Get the content of a specific notebook block by its block ID."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "The block UUID",
                }
            },
            "required": ["block_id"],
        }

    async def execute(self, block_id: str, **kwargs) -> str:
        return (
            f"[Block {block_id}] "
            "Content would be fetched here when DB is available."
        )
