"""Project endpoints — list and get projects for the current organization."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from src.infrastructure.auth.jwt import TokenData
from src.infrastructure.database import db

router = APIRouter()


@router.get("/")
async def list_projects(
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List all projects in the current organization."""
    projects = await db.fetch_all(
        """
        SELECT id, name, description, visibility, created_at, updated_at
        FROM projects
        WHERE organization_id = $1
        AND deleted_at IS NULL
        ORDER BY created_at ASC
        """,
        organization_id,
    )
    return [dict(p) for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> dict[str, Any]:
    """Get a single project by ID."""
    project = await db.fetch_one(
        """
        SELECT id, name, description, visibility, created_at, updated_at
        FROM projects
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        project_id,
        organization_id,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return dict(project)
