"""FastAPI application entry point"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.infrastructure.database import db
from src.infrastructure.events import EventConsumer, EventStore

from .middleware.auth import AuthMiddleware, OrganizationMiddleware
from .routes import (
    artifacts,
    auth,
    events,
    experiments,
    health,
    metrics,
    notebooks,
    projects,
    search,
)

logger = logging.getLogger(__name__)

# Track background consumer tasks for graceful shutdown
_consumer_tasks: List[asyncio.Task] = []


async def _start_event_store_consumers() -> None:
    """Start EventStore consumers for each organization found in the database.

    Each consumer listens on its org-scoped Redis Stream (``events:org_{id}``)
    and persists every event to the ``events`` table.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url, decode_responses=False)

    # Fetch all active organizations
    org_rows = await db.fetch_all(
        "SELECT id FROM organizations"
    )
    if not org_rows:
        logger.info("No organizations found — skipping EventStore consumer startup")
        return

    store = EventStore()

    for row in org_rows:
        org_id: UUID = row["id"]

        async def handle_event(event, _oid=org_id, _store=store):
            await _store.store_event(event)

        consumer = EventConsumer(
            redis_client=r,
            consumer_group="event-store",
            consumer_name=f"event-store-{org_id}",
            organization_id=org_id,
            batch_size=10,
            block_ms=1000,
        )

        consumer.on("experiment.started")(handle_event)
        consumer.on("metric.logged")(handle_event)
        consumer.on("run.started")(handle_event)
        consumer.on("run.completed")(handle_event)

        task = asyncio.create_task(consumer.start(), name=f"event-store-{org_id}")
        _consumer_tasks.append(task)
        logger.info("Started EventStore consumer for org %s", org_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    # Startup: Connect to database
    database_url = os.getenv("DATABASE_URL", "postgresql://researchos:researchos@postgres:5432/researchos")
    await db.connect(database_url)
    print(f"✅ Database connected: {database_url}")

    # Start background event store consumers
    try:
        await _start_event_store_consumers()
    except Exception as exc:
        logger.warning("EventStore consumer startup failed (non-fatal): %s", exc)

    yield

    # Shutdown: cancel consumer tasks and disconnect
    for task in _consumer_tasks:
        task.cancel()
    if _consumer_tasks:
        await asyncio.gather(*_consumer_tasks, return_exceptions=True)
        _consumer_tasks.clear()
    await db.disconnect()
    print("✅ Database disconnected")

app = FastAPI(
    title="ResearchOS API",
    description="Research Operating System API",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(OrganizationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(artifacts.router, prefix="/v1/artifacts", tags=["Artifacts"])
app.include_router(experiments.router, prefix="/v1/experiments", tags=["Experiments"])
app.include_router(notebooks.router, prefix="/v1/notebooks", tags=["Notebooks"])
app.include_router(search.router, prefix="/v1/search", tags=["Search"])
app.include_router(metrics.router, prefix="/v1", tags=["Metrics"])
app.include_router(projects.router, prefix="/v1/projects", tags=["Projects"])
app.include_router(events.router, prefix="/v1", tags=["Events"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
