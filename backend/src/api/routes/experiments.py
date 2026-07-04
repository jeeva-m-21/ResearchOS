"""Experiment endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID, uuid4
from typing import List, Optional

from src.api.dependencies.auth import (
    get_current_user,
    get_current_org_with_membership,
    require_role,
)
from src.api.routes.auth import get_authenticated_user_dep
from src.infrastructure.auth.jwt import TokenData
from src.infrastructure.database import db

router = APIRouter()

@router.post("/")
async def create_experiment(
    name: str,
    project_id: UUID,
    description: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Create a new experiment"""
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
    
    # Create experiment
    experiment_id = uuid4()
    await db.execute(
        """
        INSERT INTO experiments (
            id, organization_id, project_id, name, description,
            created_by, updated_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $6)
        """,
        experiment_id,
        organization_id,
        project_id,
        name,
        description,
        user.user_id
    )
    
    return {"id": experiment_id, "name": name, "project_id": str(project_id)}

@router.get("/{experiment_id}")
async def get_experiment(
    experiment_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Get experiment by ID"""
    experiment = await db.fetch_one(
        """
        SELECT 
            e.id, e.name, e.description, e.project_id,
            e.status, e.parameters, e.tags,
            e.created_at, e.updated_at
        FROM experiments e
        WHERE e.id = $1 
        AND e.organization_id = $2
        AND e.deleted_at IS NULL
        """,
        experiment_id,
        organization_id
    )
    
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    
    return dict(experiment)

@router.get("/{experiment_id}/runs")
async def list_runs(
    experiment_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """List runs for experiment"""
    runs = await db.fetch_all(
        """
        SELECT 
            r.id, r.run_number, r.status, r.started_at,
            r.ended_at, r.duration_ms, r.git_commit,
            r.created_at
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.id
        WHERE e.id = $1
        AND e.organization_id = $2
        AND e.deleted_at IS NULL
        AND r.deleted_at IS NULL
        ORDER BY r.created_at DESC
        LIMIT 100
        """,
        experiment_id,
        organization_id
    )
    
    return [dict(run) for run in runs]

@router.post("/{experiment_id}/runs")
async def start_run(
    experiment_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Start a new run"""
    # Verify experiment exists and belongs to organization
    experiment = await db.fetch_one(
        """
        SELECT 1 FROM experiments
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        experiment_id,
        organization_id
    )
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )
    
    # Get next run number
    result = await db.fetch_one(
        """
        SELECT COALESCE(MAX(run_number), 0) + 1 as next_run_number
        FROM runs
        WHERE experiment_id = $1
        AND deleted_at IS NULL
        """,
        experiment_id
    )
    
    run_number = result["next_run_number"]
    run_id = uuid4()
    
    await db.execute(
        """
        INSERT INTO runs (
            id, experiment_id, organization_id, run_number,
            status, created_by
        ) VALUES ($1, $2, $3, $4, 'created', $5)
        """,
        run_id,
        experiment_id,
        organization_id,
        run_number,
        user.user_id
    )
    
    return {"run_id": str(run_id), "run_number": run_number}
