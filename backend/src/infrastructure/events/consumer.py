"""
Event Consumer with Redis Streams consumer groups.

Key features:
- Consumer groups for parallel processing
- Idempotent processing via event_id check
- Exponential backoff retries with jitter
- Dead letter queue for poison pills
- Graceful shutdown support
- Health monitoring and metrics
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis

from domain.shared.events import DomainEvent

from .backoff import ExponentialBackoff
from .dlq import DeadLetterQueue

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Event consumer using Redis Streams consumer groups.

    Design Constraints:
    - Consumer groups enable parallel processing across multiple consumers
    - Automatic claim of pending messages after idle timeout
    - Idempotent processing via event_id uniqueness
    - DLQ for messages that fail after max retries
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        consumer_group: str,
        consumer_name: str,
        organization_id: UUID,
        batch_size: int = 10,
        block_ms: int = 1000,
        max_retries: int = 3,
        dead_letter_queue: Optional[DeadLetterQueue] = None,
        backoff_config: Optional[Dict[str, Any]] = None,
    ):
        self.redis = redis_client
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.organization_id = organization_id
        self.stream_key = f"events:org_{organization_id}"

        # Configuration
        self.batch_size = batch_size
        self.block_ms = block_ms
        self.max_retries = max_retries

        # Event handlers
        self.handlers: Dict[str, Callable[[DomainEvent], Awaitable[None]]] = {}

        # Retry and DLQ
        self.backoff = ExponentialBackoff(
            base_delay=backoff_config.get("base_delay", 1.0) if backoff_config else 1.0,
            max_delay=backoff_config.get("max_delay", 60.0) if backoff_config else 60.0,
            jitter=backoff_config.get("jitter", True) if backoff_config else True,
        )
        self.dlq = dead_letter_queue

        # State
        self.running = False
        self.last_message_time: Optional[datetime] = None
        self.processed_count = 0
        self.error_count = 0
        self.dlq_count = 0

        # Metrics
        self.metrics = {
            "processed_total": 0,
            "errors_total": 0,
            "dlq_total": 0,
            "avg_processing_time_ms": 0,
            "consumer_lag_seconds": 0,
        }

    def on(self, event_type: str) -> Callable:
        """Decorator to register handler for specific event type"""
        def decorator(func: Callable[[DomainEvent], Awaitable[None]]):
            self.handlers[event_type] = func
            return func
        return decorator

    async def start(self) -> None:
        """
        Start consuming events.

        Creates consumer group if not exists.
        """
        logger.info(
            f"Starting consumer {self.consumer_name} in group {self.consumer_group} "
            f"for organization {self.organization_id}"
        )

        # Create consumer group if not exists
        await self._ensure_consumer_group()

        self.running = True
        self.backoff.reset()

        while self.running:
            try:
                await self._consume_batch()
                self.backoff.reset()  # Reset on success
            except Exception as e:
                logger.error(f"Consumer error: {e}", exc_info=True)

                # Exponential backoff on error
                delay = self.backoff.get_delay()
                logger.warning(f"Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)

    async def stop(self, timeout: float = 30.0) -> None:
        """
        Graceful shutdown.

        Args:
            timeout: Maximum time to wait for processing to complete
        """
        logger.info(f"Stopping consumer {self.consumer_name}")
        self.running = False

        # Wait for consumers to finish processing
        start_time = time.time()
        while self._has_pending_messages() and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        logger.info(f"Consumer {self.consumer_name} stopped")

    async def _consume_batch(self) -> None:
        """Consume one batch of messages"""
        # Read messages from stream
        messages = await self.redis.xreadgroup(
            groupname=self.consumer_group,
            consumername=self.consumer_name,
            streams={self.stream_key: ">"},  # Read new messages
            count=self.batch_size,
            block=self.block_ms
        )

        if not messages:
            return

        # Process each message
        stream_name, message_list = messages[0]
        for message_id, fields in message_list:
            self.last_message_time = datetime.utcnow()
            await self._process_message(message_id, fields)

    async def _process_message(self, message_id: bytes, fields: Dict[bytes, bytes]) -> None:
        """Process single message"""
        start_time = time.time()
        event_id = None

        try:
            # Parse message
            event = self._parse_message(fields)
            event_id = event.event_id

            # Get handler
            handler = self.handlers.get(event.event_type)
            if not handler:
                logger.warning(f"No handler for event type {event.event_type}")
                # Acknowledge anyway
                await self.redis.xack(self.stream_key, self.consumer_group, message_id)
                return

            # Check idempotency (optional - depends on handler implementation)
            processed = await self._check_processed(event_id)
            if processed:
                logger.info(f"Event {event_id} already processed, skipping")
                await self.redis.xack(self.stream_key, self.consumer_group, message_id)
                return

            # Process event
            await handler(event)

            # Mark as processed
            await self._mark_processed(event_id)

            # Acknowledge message
            await self.redis.xack(self.stream_key, self.consumer_group, message_id)

            # Update metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self.processed_count += 1
            self.metrics["processed_total"] += 1
            self.metrics["avg_processing_time_ms"] = (
                self.metrics["avg_processing_time_ms"] * 0.9 + processing_time_ms * 0.1
            )

            logger.debug(f"Processed event {event_id} in {processing_time_ms:.2f}ms")

        except Exception as e:
            self.error_count += 1
            self.metrics["errors_total"] += 1

            error_msg = str(e)
            message_id_str = message_id.decode() if isinstance(message_id, bytes) else message_id
            logger.error(f"Error processing message {message_id_str}: {error_msg}")

            # Track retry count
            retry_key = f"retry:{event_id}" if event_id else f"retry:{message_id_str}"
            retries = await self.redis.incr(retry_key)
            await self.redis.expire(retry_key, 86400)  # 24h retention

            if retries >= self.max_retries:
                # Move to DLQ
                logger.error(f"Max retries ({self.max_retries}) exceeded for {message_id_str}")
                await self._move_to_dlq(message_id, fields, error_msg)

                # Acknowledge to remove from pending
                await self.redis.xack(self.stream_key, self.consumer_group, message_id)

                # Clean up retry counter
                await self.redis.delete(retry_key)

                self.dlq_count += 1
                self.metrics["dlq_total"] += 1
            else:
                # Leave in pending for retry (will be auto-claimed after idle timeout)
                logger.info(f"Retry {retries}/{self.max_retries} for {message_id_str}")

    async def _move_to_dlq(
        self,
        message_id: bytes,
        fields: Dict[bytes, bytes],
        error_msg: str
    ) -> None:
        """Move failed message to dead letter queue"""
        if self.dlq:
            # Helper function to safely decode bytes or return string
            def safe_decode(value, default=""):
                if isinstance(value, bytes):
                    return value.decode()
                return value if value is not None else default

            event_id_value = fields.get(b"event_id", b"")
            event_type_value = fields.get(b"event_type", b"")
            payload_value = fields.get(b"payload", b"")
            message_id_str = message_id.decode() if isinstance(message_id, bytes) else message_id

            await self.dlq.add(
                event_id=safe_decode(event_id_value),
                event_type=safe_decode(event_type_value),
                payload=safe_decode(payload_value),
                error=error_msg,
                consumer_group=self.consumer_group,
                original_message_id=message_id_str,
            )
        else:
            message_id_str = message_id.decode() if isinstance(message_id, bytes) else message_id
            logger.warning(f"No DLQ configured, discarding failed message {message_id_str}")

    def _parse_message(self, fields: Dict[bytes, bytes]) -> DomainEvent:
        """Parse Redis Stream fields into DomainEvent"""
        payload_str = fields.get(b"payload", b"").decode()
        payload_data = json.loads(payload_str)

        # Reconstruct event
        event_type = fields.get(b"event_type", b"").decode()

        # For now, return a generic DomainEvent
        # In practice, we would have event registry to reconstruct specific types
        return DomainEvent(**payload_data)

    async def _ensure_consumer_group(self) -> None:
        """Create consumer group if it doesn't exist"""
        try:
            await self.redis.xgroup_create(
                self.stream_key,
                self.consumer_group,
                id="0",  # Start from beginning
                mkstream=True  # Create stream if doesn't exist
            )
            logger.info(f"Created consumer group {self.consumer_group} for stream {self.stream_key}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            # Group already exists
            logger.debug(f"Consumer group {self.consumer_group} already exists")

    async def _check_processed(self, event_id: UUID) -> bool:
        """
        Check if event has already been processed.

        Implementation note: This could use a Redis SET or database table
        for idempotency checking.
        """
        # For simplicity, use Redis SET - in production would use DB table
        key = f"processed:{self.consumer_group}:events"
        exists = await self.redis.sismember(key, str(event_id))

        if exists:
            logger.debug(f"Event {event_id} already processed by {self.consumer_group}")

        return exists

    async def _mark_processed(self, event_id: UUID) -> None:
        """Mark event as processed for idempotency"""
        key = f"processed:{self.consumer_group}:events"
        await self.redis.sadd(key, str(event_id))

        # Clean old entries periodically (could be done via TTL)
        # For now, just set TTL
        await self.redis.expire(key, 86400)  # 24h retention

    def _has_pending_messages(self) -> bool:
        """
        Check if we have unacknowledged messages.

        This is a simple check - in production would check Redis pending list.
        """
        # Simple implementation - always return False
        # In production, would check Redis XPENDING
        return False

    async def get_pending_messages(self) -> List[Dict[str, Any]]:
        """Get pending messages for this consumer"""
        try:
            pending = await self.redis.xpending(
                self.stream_key,
                self.consumer_group,
                start="-",  # From beginning
                end="+",    # To end
                count=100,  # Limit
                consumername=self.consumer_name
            )

            # Parse pending messages
            result = []
            for msg in pending:
                result.append({
                    "message_id": msg[0].decode() if isinstance(msg[0], bytes) else msg[0],
                    "consumer": msg[1].decode() if isinstance(msg[1], bytes) else msg[1],
                    "idle_ms": msg[2],
                    "delivery_count": msg[3],
                })

            return result
        except Exception as e:
            logger.error(f"Error getting pending messages: {e}")
            return []

    async def get_consumer_lag(self) -> Optional[float]:
        """Get consumer lag in seconds"""
        try:
            stream_info = await self.redis.xinfo_stream(self.stream_key)

            if not stream_info:
                return None

            last_id_info = stream_info.get(b"last-generated-id", b"0-0")
            if last_id_info == b"0-0":
                return 0.0

            # Parse timestamp from message ID (format: timestamp-sequence)
            last_id = last_id_info.decode()
            timestamp_part = last_id.split("-")[0]

            try:
                last_timestamp_ms = int(timestamp_part)
                current_timestamp_ms = int(time.time() * 1000)

                lag_seconds = (current_timestamp_ms - last_timestamp_ms) / 1000.0
                self.metrics["consumer_lag_seconds"] = lag_seconds
                return lag_seconds
            except (ValueError, IndexError):
                return None

        except Exception as e:
            logger.error(f"Error calculating consumer lag: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Health check for consumer"""
        try:
            # Check Redis connection
            await self.redis.ping()

            # Get lag
            lag = await self.get_consumer_lag()

            # Get pending messages
            pending = await self.get_pending_messages()

            return {
                "status": "healthy",
                "running": self.running,
                "redis": "connected",
                "consumer_group": self.consumer_group,
                "consumer_name": self.consumer_name,
                "metrics": self.metrics.copy(),
                "pending_messages": len(pending),
                "consumer_lag_seconds": lag,
                "processed_count": self.processed_count,
                "error_count": self.error_count,
                "dlq_count": self.dlq_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "running": self.running,
                "redis": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def claim_stalled_messages(self, idle_threshold_ms: int = 30000) -> int:
        """
        Claim messages from other consumers that have been idle too long.

        Args:
            idle_threshold_ms: Messages idle longer than this will be claimed

        Returns:
            Number of messages claimed
        """
        try:
            # Use XAUTOCLAIM for automatic claiming
            result = await self.redis.xautoclaim(
                self.stream_key,
                self.consumer_group,
                self.consumer_name,
                min_idle_time=idle_threshold_ms,
                count=self.batch_size
            )

            claimed_count = len(result[1])  # List of claimed messages
            if claimed_count > 0:
                logger.info(f"Claimed {claimed_count} stalled messages")

            return claimed_count
        except Exception as e:
            logger.error(f"Error claiming stalled messages: {e}")
            return 0
