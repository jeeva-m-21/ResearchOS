"""
Idempotent Event Processing.

Key features:
- Exactly-once processing guarantee via event_id uniqueness
- Database-backed idempotency checking
- Redis caching for performance
- Support for distributed processing
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import asyncpg
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class IdempotencyChecker:
    """
    Ensures exactly-once processing using event_id uniqueness.

    Strategy:
    1. Check Redis cache (fast path)
    2. Check database (authoritative source)
    3. Mark as processed in both cache and DB

    This prevents duplicate processing in distributed systems.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        db_pool: asyncpg.Pool,
        cache_ttl: int = 86400,  # 24 hours
    ):
        self.redis = redis_client
        self.db = db_pool
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, event_id: UUID, consumer_group: str) -> str:
        """Get Redis cache key for idempotency check"""
        return f"idempotent:{consumer_group}:{event_id}"

    async def is_processed(
        self,
        event_id: UUID,
        consumer_group: str,
    ) -> bool:
        """
        Check if event has already been processed.

        Returns:
            True if event already processed, False otherwise
        """
        # 1. Check Redis cache (fast path)
        cache_key = self._get_cache_key(event_id, consumer_group)
        cached = await self.redis.exists(cache_key)

        if cached:
            logger.debug(f"Event {event_id} found in cache (already processed)")
            return True

        # 2. Check database
        try:
            async with self.db.acquire() as conn:
                processed = await conn.fetchval(
                    """
                    SELECT 1 FROM processed_events
                    WHERE event_id = $1 AND consumer_group = $2
                    """,
                    event_id,
                    consumer_group
                )

                if processed:
                    # Cache the result
                    await self.redis.setex(cache_key, self.cache_ttl, "1")
                    logger.debug(f"Event {event_id} found in DB (already processed)")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error checking idempotency in DB for event {event_id}: {e}")
            # If DB fails, be conservative and assume not processed
            # This might cause duplicate processing but is safer than dropping events
            return False

    async def mark_processed(
        self,
        event_id: UUID,
        consumer_group: str,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """
        Mark event as processed.

        This should be called after successful processing.
        """
        cache_key = self._get_cache_key(event_id, consumer_group)

        try:
            # 1. Write to database (authoritative source)
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO processed_events (
                        event_id,
                        consumer_group,
                        event_type,
                        aggregate_id,
                        processing_time_ms,
                        processed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (event_id, consumer_group) DO NOTHING
                    """,
                    event_id,
                    consumer_group,
                    event_type,
                    aggregate_id,
                    processing_time_ms,
                    datetime.utcnow()
                )

            # 2. Update cache
            await self.redis.setex(cache_key, self.cache_ttl, "1")

            logger.debug(f"Marked event {event_id} as processed by {consumer_group}")

        except Exception as e:
            logger.error(f"Error marking event {event_id} as processed: {e}")
            raise

    async def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        """
        Clean up old idempotency entries.

        Args:
            max_age_days: Maximum age of entries to keep

        Returns:
            Number of entries cleaned
        """
        try:
            async with self.db.acquire() as conn:
                # Clean database entries
                result = await conn.execute(
                    """
                    DELETE FROM processed_events
                    WHERE processed_at < NOW() - INTERVAL '$1 days'
                    """,
                    max_age_days
                )

                rows_deleted = int(result.split()[1])  # "DELETE n"

                # Note: Redis cache entries will expire automatically via TTL

                logger.info(f"Cleaned {rows_deleted} old idempotency entries")
                return rows_deleted

        except Exception as e:
            logger.error(f"Error cleaning idempotency entries: {e}")
            return 0

    async def get_stats(
        self,
        consumer_group: Optional[str] = None,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get idempotency statistics"""
        try:
            async with self.db.acquire() as conn:
                query = """
                    SELECT
                        COUNT(*) as total_processed,
                        AVG(processing_time_ms) as avg_processing_time_ms,
                        COUNT(DISTINCT event_type) as distinct_event_types
                    FROM processed_events
                    WHERE processed_at > NOW() - INTERVAL '$1 hours'
                """

                params = [time_range_hours]

                if consumer_group:
                    query += " AND consumer_group = $2"
                    params.append(consumer_group)

                stats = await conn.fetchrow(query, *params)

                result = {
                    "total_processed": stats["total_processed"] or 0,
                    "avg_processing_time_ms": float(stats["avg_processing_time_ms"] or 0),
                    "distinct_event_types": stats["distinct_event_types"] or 0,
                    "time_range_hours": time_range_hours,
                    "consumer_group": consumer_group,
                }

                return result

        except Exception as e:
            logger.error(f"Error getting idempotency stats: {e}")
            return {
                "total_processed": 0,
                "avg_processing_time_ms": 0.0,
                "distinct_event_types": 0,
                "error": str(e),
            }


class IdempotentProcessor:
    """
    Higher-level idempotent processor that wraps event processing.

    Usage:
        processor = IdempotentProcessor(idempotency_checker, consumer_group)
        success = await processor.process(event_id, process_func)
    """

    def __init__(
        self,
        idempotency_checker: IdempotencyChecker,
        consumer_group: str,
    ):
        self.checker = idempotency_checker
        self.consumer_group = consumer_group

    async def process(
        self,
        event_id: UUID,
        process_func,
        *args,
        event_type: Optional[str] = None,
        aggregate_id: Optional[UUID] = None,
        **kwargs,
    ) -> bool:
        """
        Process event idempotently.

        Args:
            event_id: Event ID
            process_func: Async function to process the event
            *args: Arguments to pass to process_func
            event_type: Event type (for tracking)
            aggregate_id: Aggregate ID (for tracking)
            **kwargs: Keyword arguments to pass to process_func

        Returns:
            True if processing succeeded (or was already done), False on error
        """
        # Check if already processed
        processed = await self.checker.is_processed(event_id, self.consumer_group)

        if processed:
            logger.info(f"Event {event_id} already processed, skipping")
            return True

        # Process the event
        start_time = datetime.utcnow()
        try:
            result = await process_func(*args, **kwargs)

            # Calculate processing time
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Mark as processed
            await self.checker.mark_processed(
                event_id=event_id,
                consumer_group=self.consumer_group,
                event_type=event_type,
                aggregate_id=aggregate_id,
                processing_time_ms=processing_time_ms,
            )

            return True

        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}")
            return False


def with_idempotency(
    idempotency_checker: IdempotencyChecker,
    consumer_group: str,
):
    """
    Decorator for idempotent processing.

    Example:
        @with_idempotency(checker, "projectors")
        async def handle_experiment_started(event: ExperimentStarted):
            # ...
    """
    def decorator(func):
        async def wrapper(event, *args, **kwargs):
            processor = IdempotentProcessor(idempotency_checker, consumer_group)

            event_id = getattr(event, 'event_id', None)
            event_type = getattr(event, 'event_type', None)
            aggregate_id = getattr(event, 'aggregate_id', None)

            if not event_id:
                raise ValueError("Event must have event_id attribute")

            success = await processor.process(
                event_id=event_id,
                process_func=func,
                event=event,
                *args,
                event_type=event_type,
                aggregate_id=aggregate_id,
                **kwargs,
            )

            if not success:
                raise RuntimeError(f"Failed to process event {event_id} idempotently")

            return success

        return wrapper

    return decorator
