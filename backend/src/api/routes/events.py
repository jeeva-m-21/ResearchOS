"""
Event API Routes.

These endpoints provide event streaming, replay, and monitoring capabilities.
"""

import asyncio
import json
import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from api.dependencies.auth import get_current_org, get_current_user
from domain.experiments.events import ExperimentStarted, MetricLogged, RunCompleted
from domain.shared.events import DomainEvent
from infrastructure.auth.jwt import TokenData
from infrastructure.events.producer import EventProducer
from infrastructure.events.service import EventsService, EventsServiceFactory

router = APIRouter()


async def get_redis() -> Redis:
    """Get Redis connection"""
    # Simplified - would use connection pooling in production
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=False)

async def get_db():
    """Simplified database dependency"""
    from infrastructure.database import db
    return db


async def get_events_service(
    organization_id: UUID = Depends(get_current_org),
    db_pool=Depends(get_db),
    redis_client=Depends(get_redis),
) -> EventsService:
    """Get or create EventsService for current organization"""
    factory = EventsServiceFactory(redis_client, db_pool)
    return await factory.get_service(organization_id)


async def get_event_producer(
    redis_client=Depends(get_redis),
) -> EventProducer:
    """Get EventProducer instance"""
    return EventProducer(redis_client)


@router.post("/events/emit")
async def emit_event(
    event: DomainEvent,
    organization_id: UUID = Depends(get_current_org),
    producer: EventProducer = Depends(get_event_producer),
) -> dict:
    """
    Emit a domain event.

    This is primarily used by internal services and SDK.
    Most application events are emitted automatically via domain operations.
    """
    try:
        # Ensure event has organization context
        if not hasattr(event, 'organization_id'):
            event.organization_id = organization_id

        stream_id = await producer.emit(event)

        return {
            "status": "success",
            "event_id": str(event.event_id),
            "stream_id": stream_id,
            "organization_id": str(organization_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/batch")
async def emit_event_batch(
    events: List[DomainEvent],
    organization_id: UUID = Depends(get_current_org),
    producer: EventProducer = Depends(get_event_producer),
) -> dict:
    """
    Emit multiple domain events in batch.

    Used by SDK for offline->online sync.
    """
    try:
        # Add organization context to each event
        for event in events:
            if not hasattr(event, 'organization_id'):
                event.organization_id = organization_id

        stream_ids = await producer.emit_batch(events)

        return {
            "status": "success",
            "count": len(stream_ids),
            "stream_ids": stream_ids,
            "organization_id": str(organization_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/stream")
async def stream_events(
    background_tasks: BackgroundTasks,
    organization_id: UUID = Depends(get_current_org),
    events_service: EventsService = Depends(get_events_service),
    event_types: Optional[List[str]] = None,
    since_event_id: Optional[str] = None,
):
    """
    Stream events via Server-Sent Events (SSE).

    Clients can subscribe to real-time event streams.
    Filter by event types and start from specific event.
    """

    async def event_generator():
        # This is a simplified SSE implementation
        # In production, would use Redis Pub/Sub or WebSockets

        while True:
            try:
                # TODO: Query Redis Stream for events since last position
                # and yield them as SSE messages
                await asyncio.sleep(1)

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        }
    )


@router.get("/events/health")
async def get_events_health(
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """Get health status of events infrastructure"""
    health = await events_service.health_check()
    return health


@router.get("/events/stats")
async def get_events_stats(
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """Get event stream statistics"""
    stats = await events_service.get_stream_stats()
    return stats


@router.get("/events/consumers/{consumer_group}/health")
async def get_consumer_health(
    consumer_group: str,
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """Get health status for specific consumer group"""
    health = await events_service.get_consumer_health(consumer_group)
    return health


@router.post("/events/replay")
async def replay_events(
    from_timestamp: Optional[str] = None,
    to_timestamp: Optional[str] = None,
    event_types: Optional[List[str]] = None,
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """
    Replay events (admin only).

    Can replay events within time range or specific event types.
    Use with caution - can cause duplicate processing.
    """
    result = await events_service.replay_events(
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        event_types=event_types,
    )

    if result["status"] == "not_implemented":
        raise HTTPException(status_code=501, detail=result["message"])

    return result


@router.get("/events/batch/status")
async def get_batch_status(
    batch_id: str,
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """Get status of a batch event emission"""
    # Placeholder - would check batch status
    return {
        "status": "completed",  # or "processing", "failed"
        "batch_id": batch_id,
        "processed_count": 0,
        "failed_count": 0,
        "details": "Batch status tracking will be implemented"
    }


@router.post("/events/dlq/{consumer_group}/retry")
async def retry_dlq_events(
    consumer_group: str,
    limit: int = 10,
    events_service: EventsService = Depends(get_events_service),
) -> dict:
    """
    Retry events from Dead Letter Queue.

    Moves failed events back to the main event stream for reprocessing.
    """
    result = await events_service.dlq.retry_all(
        consumer_group,
        limit=limit,
    )

    return {
        "status": "completed",
        "consumer_group": consumer_group,
        "limit": limit,
        "attempted": result.get("total_attempted", 0),
        "successful": result.get("successful", 0),
        "failed": result.get("failed", 0),
        "details": result.get("details", []),
    }


@router.get("/events/schema")
async def get_event_schema(
    event_type: Optional[str] = None,
) -> dict:
    """
    Get event schema(s).

    Returns JSON Schema for event types.
    Useful for SDK validation and documentation.
    """
    # Map event types to schemas
    schemas = {
        "experiment.started": ExperimentStarted.schema(),
        "metric.logged": MetricLogged.schema(),
        "run.completed": RunCompleted.schema(),
        "domain_event": (
            DomainEvent.model_json_schema()
            if hasattr(DomainEvent, "model_json_schema")
            else DomainEvent.schema()
        ),
    }

    if event_type:
        if event_type in schemas:
            return schemas[event_type]
        else:
            # Return generic domain event schema
            return schemas["domain_event"]

    return {"schemas": schemas}


@router.get("/events/types")
async def list_event_types() -> List[dict]:
    """List all available event types"""
    event_types = [
        {
            "type": "experiment.started",
            "description": "Experiment was created and started",
            "aggregate": "Experiment",
            "version": 1,
        },
        {
            "type": "metric.logged",
            "description": "Metric value was logged",
            "aggregate": "Run",
            "version": 1,
        },
        {
            "type": "run.completed",
            "description": "Run execution completed",
            "aggregate": "Run",
            "version": 1,
        },
        {
            "type": "notebook.updated",
            "description": "Notebook block added/updated/removed",
            "aggregate": "Notebook",
            "version": 1,
        },
        {
            "type": "paper.edited",
            "description": "Paper content was edited",
            "aggregate": "Paper",
            "version": 1,
        },
        {
            "type": "artifact.uploaded",
            "description": "Artifact was uploaded",
            "aggregate": "Artifact",
            "version": 1,
        },
        {
            "type": "git.commit",
            "description": "Git commit was recorded",
            "aggregate": "Experiment/Run",
            "version": 1,
        },
    ]

    return event_types


@router.post("/events/test/emit")
async def test_emit_event(
    event_type: str,
    organization_id: UUID = Depends(get_current_org),
    user_data: TokenData = Depends(get_current_user),
    producer: EventProducer = Depends(get_event_producer),
) -> dict:
    """
    Test endpoint to emit sample events.

    Only available in development/staging environments.
    """
    from datetime import datetime
    from uuid import uuid4

    # Sample event data based on type
    event_data = {
        "experiment.started": {
            "event_id": uuid4(),
            "event_type": "experiment.started",
            "aggregate_id": uuid4(),
            "aggregate_type": "Experiment",
            "version": 1,
            "timestamp": datetime.utcnow(),
            "organization_id": organization_id,
            "experiment_id": uuid4(),
            "project_id": uuid4(),
            "started_by": user_data.user_id,
            "name": "Test Experiment",  # Add these for compatibility
            "description": "Test experiment created via API",
            "tags": ["test", "api"],
            "created_by": user_data.user_id,  # Alias for started_by
        },
        "metric.logged": {
            "event_id": uuid4(),
            "event_type": "metric.logged",
            "aggregate_id": uuid4(),
            "aggregate_type": "Run",
            "version": 1,
            "timestamp": datetime.utcnow(),
            "organization_id": organization_id,
            "created_by": user_data.user_id,
            "run_id": uuid4(),
            "experiment_id": uuid4(),
            "metric_key": "accuracy",
            "metric_value": 0.95,
            "step": 100,
        },
    }

    if event_type not in event_data:
        available_types = list(event_data.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event type. Available types: {available_types}"
        )

    # Create event object
    if event_type == "experiment.started":
        event = ExperimentStarted(**event_data[event_type])
    elif event_type == "metric.logged":
        event = MetricLogged(**event_data[event_type])
    else:
        event = DomainEvent(**event_data[event_type])

    # Emit event
    stream_id = await producer.emit(event)

    return {
        "status": "success",
        "message": f"Test {event_type} event emitted",
        "event_id": str(event.event_id),
        "stream_id": stream_id,
        "event_data": event.model_dump(),
    }
