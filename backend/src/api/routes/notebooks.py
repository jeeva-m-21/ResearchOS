"""Notebook endpoints"""
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from src.api.dependencies.events import get_event_producer
from src.domain.notebooks.events import NotebookUpdated
from src.infrastructure.auth.jwt import TokenData
from src.infrastructure.database import db
from src.infrastructure.events.producer import EventProducer

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
