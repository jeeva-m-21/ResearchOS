"""Project endpoints — CRUD for the current organization."""
from typing import Any, Optional
from uuid import UUID, uuid4

from api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.auth.jwt import TokenData
from infrastructure.database import db

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    name: str,
    description: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> dict[str, Any]:
    """Create a new project in the current organization."""
    project_id = uuid4()

    await db.execute(
        """
        INSERT INTO projects
            (id, organization_id, name, description, created_by)
        VALUES ($1, $2, $3, $4, $5)
        """,
        project_id,
        organization_id,
        name,
        description or "",
        user.user_id,
    )

    return {
        "id": str(project_id),
        "name": name,
        "description": description or "",
    }


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
