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
        org_id = kwargs.get("organization_id")
        try:
            from src.infrastructure.database import db

            notebook = await db.fetch_one(
                """
                SELECT id, title, description, branch, created_at
                FROM notebooks
                WHERE id = $1::uuid AND organization_id = $2::uuid
                  AND deleted_at IS NULL
                """,
                notebook_id,
                org_id,
            )
            if not notebook:
                return f"Notebook {notebook_id} not found."

            blocks = await db.fetch_all(
                """
                SELECT b.id, b.block_type, b.position, b.current_version,
                       bc.content, bc.language
                FROM blocks b
                LEFT JOIN block_contents bc
                  ON bc.block_id = b.id AND bc.version = b.current_version
                WHERE b.notebook_id = $1::uuid
                  AND b.organization_id = $2::uuid
                  AND b.deleted_at IS NULL
                ORDER BY b.position ASC
                """,
                notebook_id,
                org_id,
            )

            created_str = (
                notebook["created_at"].strftime("%Y-%m-%d")
                if notebook["created_at"]
                else "N/A"
            )
            lines = [
                f"**Notebook: {notebook['title']}**",
                f"- Branch: {notebook['branch']}",
                f"- Description: {notebook['description'] or 'N/A'}",
                f"- Created: {created_str}",
                "",
                f"**Blocks ({len(blocks)}):**",
            ]
            for blk in blocks:
                preview = (blk["content"] or "")[:80].replace("\n", " ")
                lang = f" ({blk['language']})" if blk["language"] else ""
                lines.append(
                    f"- [{blk['block_type']}{lang}] pos {blk['position']}: "
                    f"{preview}"
                )

            return "\n".join(lines)
        except Exception as exc:
            return f"Error fetching notebook: {exc}"


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
        org_id = kwargs.get("organization_id")
        project_id = kwargs.get("project_id")
        limit = kwargs.get("limit", 20)
        try:
            from src.infrastructure.database import db

            if project_id:
                rows = await db.fetch_all(
                    """
                    SELECT id, title, branch, created_at
                    FROM notebooks
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
                    SELECT id, title, branch, created_at
                    FROM notebooks
                    WHERE organization_id = $1::uuid
                      AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    org_id,
                    limit,
                )

            if not rows:
                return "No notebooks found."

            lines = [f"**Notebooks ({len(rows)}):**\n"]
            for r in rows:
                created = (
                    r["created_at"].strftime("%Y-%m-%d")
                    if r["created_at"]
                    else "N/A"
                )
                lines.append(
                    f"- {r['title']} (branch: {r['branch']}, created: {created})"
                )
            return "\n".join(lines)
        except Exception as exc:
            return f"Error listing notebooks: {exc}"


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
        org_id = kwargs.get("organization_id")
        try:
            from src.infrastructure.database import db

            block = await db.fetch_one(
                """
                SELECT b.id, b.block_type, b.position, b.current_version,
                       b.notebook_id, bc.content, bc.language, bc.version
                FROM blocks b
                LEFT JOIN block_contents bc
                  ON bc.block_id = b.id AND bc.version = b.current_version
                WHERE b.id = $1::uuid AND b.organization_id = $2::uuid
                  AND b.deleted_at IS NULL
                """,
                block_id,
                org_id,
            )
            if not block:
                return f"Block {block_id} not found."

            content = block["content"] or "(empty)"
            lang = f" ({block['language']})" if block["language"] else ""
            return (
                f"**Block {block_id}**\n"
                f"- Type: {block['block_type']}{lang}\n"
                f"- Position: {block['position']}\n"
                f"- Version: {block['version']}\n"
                f"- Notebook: {block['notebook_id']}\n"
                f"\n```\n{content}\n```"
            )
        except Exception as exc:
            return f"Error fetching block content: {exc}"


class GetPaperTool(ResearchTool):
    """Get paper details with citations."""

    @property
    def name(self) -> str:
        return "get_paper"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a research paper "
            "including its citations."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "The paper UUID",
                }
            },
            "required": ["paper_id"],
        }

    async def execute(self, paper_id: str, **kwargs) -> str:
        org_id = kwargs.get("organization_id")
        try:
            from src.infrastructure.database import db

            paper = await db.fetch_one(
                """
                SELECT id, title, abstract, status, version,
                       authors, doi, arxiv_id, created_at
                FROM papers
                WHERE id = $1::uuid AND organization_id = $2::uuid
                  AND deleted_at IS NULL
                """,
                paper_id,
                org_id,
            )
            if not paper:
                return f"Paper {paper_id} not found."

            citations = await db.fetch_all(
                """
                SELECT id, citation_key, title, authors, year, venue, url
                FROM citations
                WHERE paper_id = $1::uuid AND organization_id = $2::uuid
                ORDER BY citation_key ASC
                """,
                paper_id,
                org_id,
            )

            authors_list = paper["authors"] or []
            authors_str = (
                ", ".join(str(a) for a in authors_list)
                if authors_list
                else "N/A"
            )
            created_str = (
                paper["created_at"].strftime("%Y-%m-%d")
                if paper["created_at"]
                else "N/A"
            )
            lines = [
                f"**Paper: {paper['title']}**",
                f"- Status: {paper['status']} v{paper['version']}",
                f"- Authors: {authors_str}",
                f"- DOI: {paper['doi'] or 'N/A'}",
                f"- arXiv: {paper['arxiv_id'] or 'N/A'}",
                f"- Created: {created_str}",
            ]
            if paper["abstract"]:
                lines.append(f"\n**Abstract:**\n{paper['abstract']}")

            lines.append(f"\n**Citations ({len(citations)}):**")
            for c in citations:
                cauthors = c["authors"] or []
                cauthors_str = ", ".join(str(a) for a in cauthors[:3])
                if len(cauthors) > 3:
                    cauthors_str += " et al."
                lines.append(
                    f"- {c['citation_key']}: {cauthors_str} ({c['year']}) "
                    f"'{c['title']}'"
                )

            return "\n".join(lines)
        except Exception as exc:
            return f"Error fetching paper: {exc}"


class ListPapersTool(ResearchTool):
    """List papers in a project."""

    @property
    def name(self) -> str:
        return "list_papers"

    @property
    def description(self) -> str:
        return "List research papers in the current project."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Optional project UUID to filter by",
                },
                "status": {
                    "type": "string",
                    "description": (
                        "Filter by status (draft, in_review, published, archived)"
                    ),
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
        status_filter = kwargs.get("status")
        limit = kwargs.get("limit", 20)
        try:
            from src.infrastructure.database import db

            params = [org_id]
            conditions = [
                "organization_id = $1::uuid",
                "deleted_at IS NULL",
            ]
            idx = 2

            if project_id:
                conditions.append(f"project_id = ${idx}::uuid")
                params.append(project_id)
                idx += 1

            if status_filter:
                conditions.append(f"status = ${idx}")
                params.append(status_filter)
                idx += 1

            params.append(limit)

            rows = await db.fetch_all(
                f"""
                SELECT id, title, status, version, authors, created_at
                FROM papers
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ${idx}
                """,
                *params,
            )

            if not rows:
                return "No papers found."

            lines = [f"**Papers ({len(rows)}):**\n"]
            for r in rows:
                created = (
                    r["created_at"].strftime("%Y-%m-%d")
                    if r["created_at"]
                    else "N/A"
                )
                a = r["authors"] or []
                author_str = ", ".join(str(x) for x in a[:2])
                if len(a) > 2:
                    author_str += " et al."
                lines.append(
                    f"- {r['title']} [{r['status']} v{r['version']}] "
                    f"({author_str}, {created})"
                )
            return "\n".join(lines)
        except Exception as exc:
            return f"Error listing papers: {exc}"
