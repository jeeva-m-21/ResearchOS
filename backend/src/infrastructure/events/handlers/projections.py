"""
Projection Handlers for CQRS read models.

These handlers update read models (projections) from events.
Projections are optimized for querying, denormalized views of domain state.
"""

import logging
from datetime import datetime
from typing import Any, Dict

import asyncpg

from domain.experiments.events import ExperimentStarted, MetricLogged
from domain.notebooks.events import NotebookUpdated
from domain.papers.events import PaperEdited
from domain.shared.events import DomainEvent

logger = logging.getLogger(__name__)


class ProjectionHandler:
    """
    Updates read model projections from events.

    Each projection is an optimized view of domain state for specific query patterns.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def handle_experiment_started(self, event: ExperimentStarted) -> None:
        """
        Update experiment summary projection.

        Creates/updates denormalized experiment view for fast querying.
        """
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO active_experiments (
                        id,
                        organization_id,
                        project_id,
                        name,
                        description,
                        status,
                        tags,
                        created_by,
                        created_at,
                        updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        tags = EXCLUDED.tags,
                        updated_at = EXCLUDED.updated_at
                    """,
                    event.experiment_id,
                    event.organization_id,
                    event.project_id,
                    event.name,
                    event.description,
                    "running",  # status after started
                    event.tags or [],
                    event.created_by,
                    event.timestamp,
                    event.timestamp
                )

            logger.debug(
                f"Updated experiment projection for {event.experiment_id}"
            )

        except Exception as e:
            logger.error(
                f"Error updating experiment projection for {event.experiment_id}: {e}"
            )
            raise

    async def handle_metric_logged(self, event: MetricLogged) -> None:
        """
        Update metric summary projection.

        Maintains aggregated metrics (min, max, avg, count) for fast querying.
        """
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO metric_summary (
                        run_id,
                        key,
                        min_value,
                        max_value,
                        avg_value,
                        count,
                        last_value,
                        last_updated
                    ) VALUES ($1, $2, $3, $3, $3, 1, $3, $4)
                    ON CONFLICT (run_id, key) DO UPDATE SET
                        min_value = LEAST(metric_summary.min_value, $3),
                        max_value = GREATEST(metric_summary.max_value, $3),
                        avg_value = (metric_summary.avg_value * metric_summary.count + $3)
                                   / (metric_summary.count + 1),
                        count = metric_summary.count + 1,
                        last_value = $3,
                        last_updated = $4
                    """,
                    event.run_id,
                    event.key,
                    event.value,
                    event.timestamp
                )

            logger.debug(
                f"Updated metric projection for run {event.run_id}, key {event.key}"
            )

        except Exception as e:
            logger.error(
                f"Error updating metric projection for run {event.run_id}: {e}"
            )
            raise

    async def handle_notebook_updated(self, event: NotebookUpdated) -> None:
        """
        Update notebook summary projection.

        Maintains notebook metadata and block counts for fast querying.
        """
        try:
            async with self.db.acquire() as conn:
                # Update notebook summary
                if event.operation == "add_block":
                    await conn.execute(
                        """
                        UPDATE notebook_summary
                        SET block_count = block_count + 1,
                            updated_at = $1
                        WHERE notebook_id = $2
                        """,
                        event.timestamp,
                        event.notebook_id
                    )
                elif event.operation == "remove_block":
                    await conn.execute(
                        """
                        UPDATE notebook_summary
                        SET block_count = GREATEST(0, block_count - 1),
                            updated_at = $1
                        WHERE notebook_id = $2
                        """,
                        event.timestamp,
                        event.notebook_id
                    )

            logger.debug(
                f"Updated notebook projection for {event.notebook_id}, "
                f"operation {event.operation}"
            )

        except Exception as e:
            logger.error(
                f"Error updating notebook projection for {event.notebook_id}: {e}"
            )
            raise

    async def handle_paper_edited(self, event: PaperEdited) -> None:
        """
        Update paper summary projection.

        Maintains paper metadata and version tracking.
        """
        try:
            async with self.db.acquire() as conn:
                # Update paper summary
                await conn.execute(
                    """
                    INSERT INTO paper_summary (
                        paper_id,
                        organization_id,
                        project_id,
                        title,
                        version,
                        status,
                        updated_by,
                        updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (paper_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        version = EXCLUDED.version,
                        status = EXCLUDED.status,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = EXCLUDED.updated_at
                    """,
                    event.paper_id,
                    event.organization_id,
                    event.project_id,
                    event.changes.get("title") if event.changes else None,
                    event.version,
                    event.changes.get("status") if event.changes else None,
                    event.created_by,
                    event.timestamp
                )

            logger.debug(
                f"Updated paper projection for {event.paper_id}, version {event.version}"
            )

        except Exception as e:
            logger.error(
                f"Error updating paper projection for {event.paper_id}: {e}"
            )
            raise

    async def handle_generic_event(self, event: DomainEvent) -> None:
        """
        Handle generic domain events.

        Updates event tracking projection for audit and monitoring.
        """
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO event_tracking (
                        event_id,
                        event_type,
                        aggregate_id,
                        aggregate_type,
                        organization_id,
                        processed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    event.aggregate_type,
                    getattr(event, 'organization_id', None),
                    datetime.utcnow()
                )

            logger.debug(
                f"Tracked event {event.event_id} ({event.event_type})"
            )

        except Exception as e:
            logger.error(
                f"Error tracking event {event.event_id}: {e}"
            )
            # Don't raise for tracking errors - they shouldn't block processing


class ProjectionManager:
    """
    Manages multiple projection handlers.

    Routes events to appropriate handlers and manages handler lifecycle.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self.handlers = ProjectionHandler(db_pool)

        # Event type to handler mapping
        self.handler_map: Dict[str, callable] = {
            "experiment.started": self.handlers.handle_experiment_started,
            "metric.logged": self.handlers.handle_metric_logged,
            "notebook.updated": self.handlers.handle_notebook_updated,
            "paper.edited": self.handlers.handle_paper_edited,
        }

    async def handle_event(self, event: DomainEvent) -> None:
        """
        Route event to appropriate handler.

        Args:
            event: Domain event to process
        """
        handler = self.handler_map.get(event.event_type)

        if handler:
            logger.info(
                f"Routing event {event.event_id} ({event.event_type}) "
                f"to projection handler"
            )
            await handler(event)
        else:
            # Handle generic events
            await self.handlers.handle_generic_event(event)

    async def health_check(self) -> Dict[str, Any]:
        """Health check for projection manager"""
        try:
            async with self.db.acquire() as conn:
                # Test database connection
                result = await conn.fetchval("SELECT 1")

                if result != 1:
                    raise RuntimeError("Database health check failed")

            return {
                "status": "healthy",
                "database": "connected",
                "handlers_registered": len(self.handler_map),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
