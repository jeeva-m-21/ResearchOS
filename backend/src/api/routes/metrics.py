"""Metric endpoints"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from api.dependencies.events import get_event_producer
from domain.experiments.events import MetricLogged
from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.auth.jwt import TokenData
from infrastructure.database import db
from infrastructure.events.producer import EventProducer

router = APIRouter()

router = APIRouter()

@router.post("/experiments/{experiment_id}/runs/{run_id}/metrics")
async def log_metric(
    experiment_id: UUID,
    run_id: UUID,
    key: str,
    value: float,
    step: int = 0,
    metadata: Optional[dict] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Log a metric for a run"""

    # Verify run exists and belongs to organization
    run = await db.fetch_one(
        """
        SELECT 1 FROM runs r
        JOIN experiments e ON r.experiment_id = e.id
        WHERE r.id = $1
        AND e.id = $2
        AND e.organization_id = $3
        AND r.deleted_at IS NULL
        """,
        run_id,
        experiment_id,
        organization_id
    )

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied",
        )

    # Log metric to database
    metric_id = await db.fetch_val(
        """
        INSERT INTO metrics (
            id, run_id, organization_id, key, value, step,
            timestamp, metadata, created_by
        ) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), $6, $7)
        RETURNING id
        """,
        run_id,
        organization_id,
        key,
        value,
        step,
        metadata if metadata is not None else None,
        user.user_id
    )

    # Emit metric.logged event
    event = MetricLogged(
        aggregate_id=run_id,
        organization_id=organization_id,
        run_id=run_id,
        experiment_id=experiment_id,
        metric_key=key,
        metric_value=value,
        step=step,
    )
    await event_producer.emit(event)

    return {"id": metric_id, "key": key, "value": value, "step": step}

@router.get("/experiments/{experiment_id}/runs/{run_id}/metrics")
async def get_metrics(
    experiment_id: UUID,
    run_id: UUID,
    key: Optional[str] = None,
    limit: int = 100,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Get metrics for a run"""

    # Verify run exists and belongs to organization
    run = await db.fetch_one(
        """
        SELECT 1 FROM runs r
        JOIN experiments e ON r.experiment_id = e.id
        WHERE r.id = $1
        AND e.id = $2
        AND e.organization_id = $3
        AND r.deleted_at IS NULL
        """,
        run_id,
        experiment_id,
        organization_id
    )

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied",
        )

    # Build query
    if key:
        metrics = await db.fetch_all("""
            SELECT
                id, key, value, step, timestamp, metadata
            FROM metrics
            WHERE run_id = $1
            AND organization_id = $2
            AND key = $3
            ORDER BY timestamp DESC
            LIMIT $4
        """, run_id, organization_id, key, limit)
    else:
        metrics = await db.fetch_all("""
            SELECT
                id, key, value, step, timestamp, metadata
            FROM metrics
            WHERE run_id = $1
            AND organization_id = $2
            ORDER BY timestamp DESC
            LIMIT $3
        """, run_id, organization_id, limit)

    return [dict(metric) for metric in metrics]

@router.post("/experiments/{experiment_id}/runs/{run_id}/complete")
async def complete_run(
    experiment_id: UUID,
    run_id: UUID,
    run_status: str = "completed",
    error: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Complete a run"""

    # Verify run exists and belongs to organization
    run = await db.fetch_one(
        """
        SELECT 1 FROM runs r
        JOIN experiments e ON r.experiment_id = e.id
        WHERE r.id = $1
        AND e.id = $2
        AND e.organization_id = $3
        AND r.deleted_at IS NULL
        AND r.status = 'created'
        """,
        run_id,
        experiment_id,
        organization_id
    )

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found, access denied, or already completed",
        )

    # Update run status
    await db.execute(
        """
        UPDATE runs
        SET status = $1,
            ended_at = NOW(),
            duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
        WHERE id = $2
        """,
        run_status,
        run_id
    )

    # Also update experiment if all runs are completed?
    # This could be handled by a projection from events

    return {
        "run_id": str(run_id),
        "status": run_status,
        "completed_at": datetime.utcnow().isoformat(),
    }
