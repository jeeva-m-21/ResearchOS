"""Notebook endpoints"""
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from src.api.dependencies.events import get_event_producer
from src.domain.notebooks.entities import BlockType
from src.domain.notebooks.events import BlockExecuted, NotebookUpdated
from src.infrastructure.auth.jwt import TokenData
from src.infrastructure.database import db
from src.infrastructure.events.producer import EventProducer
from src.infrastructure.executor import execute_block


class CreateBlockRequest(BaseModel):
    """Request model for creating a block"""
    block_type: str
    content: str
    language: Optional[str] = None
    position: Optional[int] = None

router = APIRouter()


@router.post("/")
async def create_notebook(
    title: str,
    project_id: UUID,
    description: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
) -> dict[str, Any]:
    """Create a new notebook"""
    # Verify project belongs to organization
    project = await db.fetch_one(
        """
        SELECT id FROM projects
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        project_id,
        organization_id
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    notebook_id = uuid4()
    await db.execute(
        """
        INSERT INTO notebooks (
            id, organization_id, project_id, title, description,
            created_by, updated_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $6)
        """,
        notebook_id,
        organization_id,
        project_id,
        title,
        description,
        user.user_id
    )

    # Emit notebook.updated event
    event = NotebookUpdated(
        aggregate_id=notebook_id,
        notebook_id=notebook_id,
        organization_id=organization_id,
        operation="created",
    )
    await event_producer.emit(event)

    return {"id": notebook_id, "title": title, "project_id": str(project_id)}


@router.get("/{notebook_id}")
async def get_notebook(
    notebook_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> dict[str, Any]:
    """Get notebook by ID"""
    notebook = await db.fetch_one(
        """
        SELECT
            n.id, n.title, n.description, n.project_id,
            n.branch, n.parent_commit,
            n.created_at, n.updated_at
        FROM notebooks n
        WHERE n.id = $1
        AND n.organization_id = $2
        AND n.deleted_at IS NULL
        """,
        notebook_id,
        organization_id
    )

    if not notebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    return dict(notebook)


@router.get("/")
async def list_notebooks(
    project_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List notebooks, optionally filtered by project"""
    if project_id:
        notebooks = await db.fetch_all(
            """
            SELECT
                n.id, n.title, n.description, n.project_id,
                n.branch, n.created_at, n.updated_at
            FROM notebooks n
            WHERE n.organization_id = $1
            AND n.project_id = $2
            AND n.deleted_at IS NULL
            ORDER BY n.created_at DESC
            LIMIT $3 OFFSET $4
            """,
            organization_id,
            project_id,
            limit,
            offset
        )
    else:
        notebooks = await db.fetch_all(
            """
            SELECT
                n.id, n.title, n.description, n.project_id,
                n.branch, n.created_at, n.updated_at
            FROM notebooks n
            WHERE n.organization_id = $1
            AND n.deleted_at IS NULL
            ORDER BY n.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            organization_id,
            limit,
            offset
        )

    return [dict(nb) for nb in notebooks]


# ── Block CRUD ─────────────────────────────────────────────────────────


@router.get("/{notebook_id}/blocks")
async def list_blocks(
    notebook_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List all blocks in a notebook with their current content"""
    # Verify notebook exists and belongs to organization
    notebook = await db.fetch_one(
        """
        SELECT id FROM notebooks
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        notebook_id,
        organization_id
    )
    if not notebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    rows = await db.fetch_all(
        """
        SELECT
            b.id, b.notebook_id, b.block_type, b.position,
            b.current_version, b.created_at, b.updated_at,
            bc.content, bc.language, bc.version as content_version
        FROM blocks b
        LEFT JOIN block_contents bc
            ON bc.block_id = b.id
            AND bc.version = b.current_version
        WHERE b.notebook_id = $1
        AND b.organization_id = $2
        AND b.deleted_at IS NULL
        ORDER BY b.position ASC
        """,
        notebook_id,
        organization_id
    )

    result = []
    for row in rows:
        block = dict(row)
        block["content"] = block.pop("content", None)
        block["language"] = block.pop("language", None)
        block["content_version"] = block.pop("content_version", None)
        result.append(block)

    return result


@router.post("/{notebook_id}/blocks")
async def create_block(
    notebook_id: UUID,
    body: CreateBlockRequest,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
) -> dict[str, Any]:
    """Create a new block in a notebook"""
    # Verify notebook exists
    notebook = await db.fetch_one(
        """
        SELECT id FROM notebooks
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        notebook_id,
        organization_id
    )
    if not notebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    # Validate block_type
    if body.block_type not in [bt.value for bt in BlockType]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid block_type '{body.block_type}'. "
                f"Valid types: {[bt.value for bt in BlockType]}"
            ),
        )

    # Determine position
    if body.position is None:
        pos_row = await db.fetch_one(
            """
            SELECT COALESCE(MAX(position), -1) + 1 AS next_pos
            FROM blocks
            WHERE notebook_id = $1 AND deleted_at IS NULL
            """,
            notebook_id
        )
        position = pos_row["next_pos"] if pos_row else 0
    else:
        position = body.position

    block_id = uuid4()
    await db.execute(
        """
        INSERT INTO blocks (id, notebook_id, organization_id, block_type, position)
        VALUES ($1, $2, $3, $4, $5)
        """,
        block_id, notebook_id, organization_id, body.block_type, position
    )

    # Insert initial content (version 1)
    content_id = uuid4()
    await db.execute(
        """
        INSERT INTO block_contents
            (id, block_id, organization_id, version, content, language, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        content_id, block_id, organization_id,
        1, body.content, body.language, user.user_id
    )

    # Emit event
    event = NotebookUpdated(
        aggregate_id=notebook_id,
        notebook_id=notebook_id,
        organization_id=organization_id,
        operation="add_block",
    )
    await event_producer.emit(event)

    return {
        "id": str(block_id),
        "notebook_id": str(notebook_id),
        "block_type": body.block_type,
        "position": position,
        "content": body.content,
        "language": body.language,
        "current_version": 1,
    }


@router.get("/{notebook_id}/blocks/{block_id}")
async def get_block(
    notebook_id: UUID,
    block_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> dict[str, Any]:
    """Get a single block with its current content"""
    row = await db.fetch_one(
        """
        SELECT
            b.id, b.notebook_id, b.block_type, b.position,
            b.current_version, b.created_at, b.updated_at,
            bc.content, bc.language, bc.version as content_version
        FROM blocks b
        LEFT JOIN block_contents bc
            ON bc.block_id = b.id
            AND bc.version = b.current_version
        WHERE b.id = $1
        AND b.notebook_id = $2
        AND b.organization_id = $3
        AND b.deleted_at IS NULL
        """,
        block_id, notebook_id, organization_id
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    result = dict(row)
    result["content"] = result.pop("content", None)
    result["language"] = result.pop("language", None)
    result["content_version"] = result.pop("content_version", None)
    return result


# ── Block Execution ────────────────────────────────────────────────────


@router.post("/{notebook_id}/blocks/{block_id}/execute")
async def execute_block_endpoint(
    notebook_id: UUID,
    block_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
) -> dict[str, Any]:
    """Execute a block — runs the block's current content and stores the result."""
    # Verify the block exists and belongs to the notebook/org
    row = await db.fetch_one(
        """
        SELECT b.id, b.block_type, b.current_version,
               bc.id as content_id, bc.content
        FROM blocks b
        LEFT JOIN block_contents bc
            ON bc.block_id = b.id
            AND bc.version = b.current_version
        WHERE b.id = $1
        AND b.notebook_id = $2
        AND b.organization_id = $3
        AND b.deleted_at IS NULL
        """,
        block_id, notebook_id, organization_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    block_type = row["block_type"]
    content = row["content"]
    content_id = row["content_id"]

    if not content or not content_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Block has no content to execute",
        )

    if block_type not in ("python", "rust", "sql"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Block type '{block_type}' does not support execution. "
                   f"Supported types: python, rust, sql",
        )

    result = await execute_block(
        block_id=block_id,
        notebook_id=notebook_id,
        block_content_id=content_id,
        block_type=block_type,
        content=content,
        organization_id=organization_id,
        created_by=user.user_id,
    )

    # Emit event
    event = BlockExecuted(
        aggregate_id=block_id,
        block_id=block_id,
        notebook_id=notebook_id,
        execution_id=UUID(result["execution_id"]),
        organization_id=organization_id,
        status=result["status"],
        duration_ms=result.get("duration_ms"),
    )
    await event_producer.emit(event)

    return result


@router.get("/{notebook_id}/blocks/{block_id}/executions")
async def list_executions(
    notebook_id: UUID,
    block_id: UUID,
    limit: int = 10,
    offset: int = 0,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List execution history for a block."""
    rows = await db.fetch_all(
        """
        SELECT id, block_content_id, status, started_at, ended_at,
               duration_ms, output, error
        FROM executions
        WHERE block_id = $1
        AND notebook_id = $2
        AND organization_id = $3
        ORDER BY started_at DESC
        LIMIT $4 OFFSET $5
        """,
        block_id, notebook_id, organization_id, limit, offset,
    )

    return [dict(r) for r in rows]
