"""
Event Store — persists events to PostgreSQL for durability and replay.

The EventStore is the consumer-side counterpart of EventProducer. While the
producer writes events to Redis Streams for fast distribution, the EventStore
persists them to the `events` table so they survive restarts and can be
replayed later.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.shared.events import DomainEvent
from infrastructure.database import db

logger = logging.getLogger(__name__)


class EventStore:
    """
    Append-only event store backed by PostgreSQL.

    Usage::

        store = EventStore()
        await store.store_event(event)

    This is deliberately a thin wrapper around the ``events`` table. No
    idempotency checking or retry logic lives here — those are handled by the
    EventConsumer before the event reaches this store.
    """

    async def store_event(
        self,
        event: DomainEvent,
        processed_at: Optional[datetime] = None,
    ) -> None:
        """Insert a single event into the events table.

        Args:
            event: The domain event to persist.
            processed_at: When the event was consumed (defaults to now).
        """
        await db.execute(
            """
            INSERT INTO events (
                id,
                event_id,
                organization_id,
                event_type,
                aggregate_id,
                aggregate_type,
                version,
                payload,
                metadata,
                created_at,
                processed_at
            ) VALUES (
                gen_random_uuid(),
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            )
            ON CONFLICT (event_id) DO NOTHING
            """,
            event.event_id,
            event.organization_id,
            event.event_type,
            event.aggregate_id,
            event.aggregate_type,
            event.version,
            event.model_dump_json(),
            json.dumps(getattr(event, "metadata", {})),
            event.timestamp,
            processed_at or datetime.utcnow(),
        )
        logger.debug("Stored event %s (%s)", event.event_id, event.event_type)

    async def store_batch(
        self,
        events: List[DomainEvent],
    ) -> None:
        """Insert multiple events in a single round-trip.

        Args:
            events: The domain events to persist.
        """
        processed_at = datetime.utcnow()
        for event in events:
            await self.store_event(event, processed_at)

    async def get_events(
        self,
        organization_id: UUID,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch stored events, newest first.

        Args:
            organization_id: Scoped to an organization.
            event_type: Optional filter by event type.
            aggregate_id: Optional filter by aggregate.
            limit: Max rows to return.
            offset: Pagination offset.

        Returns:
            List of raw row dicts from the events table.
        """
        params: List[Any] = [organization_id]
        conditions = ["organization_id = $1"]

        if event_type:
            conditions.append(f"event_type = ${len(params) + 1}")
            params.append(event_type)
        if aggregate_id:
            conditions.append(f"aggregate_id = ${len(params) + 1}")
            params.append(aggregate_id)

        params.append(limit)
        params.append(offset)

        rows = await db.fetch_all(
            f"""
            SELECT *
            FROM events
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${len(params) - 1} OFFSET ${len(params)}
            """,
            *params,
        )
        return [dict(r) for r in rows]

    async def count_events(
        self,
        organization_id: UUID,
        event_type: Optional[str] = None,
    ) -> int:
        """Count stored events, optionally filtered by type."""
        params: List[Any] = [organization_id]
        conditions = ["organization_id = $1"]

        if event_type:
            conditions.append(f"event_type = ${len(params) + 1}")
            params.append(event_type)

        val = await db.fetch_val(
            f"SELECT count(*) FROM events WHERE {' AND '.join(conditions)}",
            *params,
        )
        return val or 0
