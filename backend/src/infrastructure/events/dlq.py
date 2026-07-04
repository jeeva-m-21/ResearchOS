"""
Dead Letter Queue (DLQ) for failed events.

Key features:
- Persistent storage for poison pills
- Retry capability for DLQ events
- Monitoring and alerting
- Configurable retention
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """
    Dead Letter Queue for events that fail processing after max retries.

    Stores failed events in Redis Streams for later inspection and possible retry.
    Each consumer group has its own DLQ stream.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        retention_days: int = 30,
        max_dlq_size: int = 10000,
    ):
        """
        Initialize Dead Letter Queue.

        Args:
            redis_client: Redis client
            retention_days: How long to keep DLQ entries (days)
            max_dlq_size: Maximum size of DLQ stream (circular buffer)
        """
        self.redis = redis_client
        self.retention_days = retention_days
        self.max_dlq_size = max_dlq_size

    def _get_dlq_key(self, consumer_group: str) -> str:
        """Get Redis key for DLQ stream"""
        return f"dlq:{consumer_group}"

    async def add(
        self,
        event_id: str,
        event_type: str,
        payload: str,
        error: str,
        consumer_group: str,
        original_message_id: Optional[str] = None,
        retry_count: int = 0,
        **additional_info: Any,
    ) -> str:
        """
        Add failed event to DLQ.

        Args:
            event_id: Original event ID
            event_type: Event type
            payload: Event payload (JSON string)
            error: Error that caused failure
            consumer_group: Consumer group that failed
            original_message_id: Original Redis Stream message ID
            retry_count: Number of retries attempted
            **additional_info: Additional metadata

        Returns:
            DLQ message ID
        """
        dlq_key = self._get_dlq_key(consumer_group)

        message = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "error": error,
            "consumer_group": consumer_group,
            "original_message_id": original_message_id or "",
            "retry_count": str(retry_count),
            "failed_at": datetime.utcnow().isoformat(),
            "additional_info": json.dumps(additional_info),
        }

        # Add to DLQ stream
        stream_id = await self.redis.xadd(
            dlq_key,
            message,
            maxlen=self.max_dlq_size
        )

        dlq_msg_id = stream_id.decode()

        logger.warning(
            f"Event {event_id} ({event_type}) moved to DLQ {dlq_key}: {error}"
        )

        # Set TTL for automatic cleanup (optional, Redis streams don't have TTL)
        # We'll clean via maxlen instead

        return dlq_msg_id

    async def get_entries(
        self,
        consumer_group: str,
        limit: int = 100,
        start_id: str = "-",
        end_id: str = "+",
    ) -> List[Dict[str, Any]]:
        """
        Get entries from DLQ.

        Args:
            consumer_group: Consumer group name
            limit: Maximum entries to return
            start_id: Start ID for range query ("-" for beginning)
            end_id: End ID for range query ("+" for end)

        Returns:
            List of DLQ entries
        """
        dlq_key = self._get_dlq_key(consumer_group)

        try:
            entries = await self.redis.xrange(
                dlq_key,
                min=start_id,
                max=end_id,
                count=limit
            )

            result = []
            for msg_id, fields in entries:
                entry = {
                    "dlq_message_id": msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                }

                # Parse fields
                for key, value in fields.items():
                    key_str = key.decode() if isinstance(key, bytes) else key
                    value_str = value.decode() if isinstance(value, bytes) else value

                    # Parse JSON fields
                    if key_str in ["additional_info"]:
                        try:
                            entry[key_str] = json.loads(value_str)
                        except json.JSONDecodeError:
                            entry[key_str] = value_str
                    else:
                        entry[key_str] = value_str

                result.append(entry)

            return result
        except Exception as e:
            logger.error(f"Error getting DLQ entries: {e}")
            return []

    async def get_stats(self, consumer_group: str) -> Dict[str, Any]:
        """Get DLQ statistics"""
        dlq_key = self._get_dlq_key(consumer_group)

        try:
            info = await self.redis.xinfo_stream(dlq_key)

            stats = {
                "exists": True,
                "length": info.get(b"length", 0),
                "consumer_group": consumer_group,
            }

            # Convert bytes to strings
            for key, value in info.items():
                if isinstance(value, bytes):
                    stats[key.decode()] = value.decode()
                else:
                    stats[key] = value

            return stats
        except redis.ResponseError as e:
            if "no such key" in str(e):
                return {
                    "exists": False,
                    "length": 0,
                    "consumer_group": consumer_group,
                }
            raise

    async def retry_entry(
        self,
        consumer_group: str,
        dlq_message_id: str,
        target_stream: Optional[str] = None,
    ) -> bool:
        """
        Retry a DLQ entry by moving it back to main stream.

        Args:
            consumer_group: Consumer group name
            dlq_message_id: DLQ message ID to retry
            target_stream: Target stream (defaults to original organization stream)

        Returns:
            Success flag
        """
        dlq_key = self._get_dlq_key(consumer_group)

        try:
            # Get the DLQ entry
            messages = await self.redis.xrange(
                dlq_key,
                min=dlq_message_id,
                max=dlq_message_id,
                count=1
            )

            if not messages:
                logger.error(f"DLQ entry {dlq_message_id} not found")
                return False

            _, fields = messages[0]

            # Parse fields
            event_id = fields.get(b"event_id", b"").decode()
            event_type = fields.get(b"event_type", b"").decode()
            payload = fields.get(b"payload", b"").decode()

            # Determine target stream
            if not target_stream:
                # Try to extract organization_id from payload
                try:
                    payload_data = json.loads(payload)
                    org_id = payload_data.get("organization_id")
                    if org_id:
                        target_stream = f"events:org_{org_id}"
                    else:
                        target_stream = "events:org_default"
                except (json.JSONDecodeError, KeyError):
                    target_stream = "events:org_default"

            # Prepare message for retry (add retry metadata)
            message = {
                "event_id": event_id,
                "event_type": event_type,
                "payload": payload,
                "dlq_retry": "true",
                "original_dlq_id": dlq_message_id,
                "retried_at": datetime.utcnow().isoformat(),
                "consumer_group": consumer_group,
            }

            # Add to target stream
            await self.redis.xadd(
                target_stream,
                message,
                maxlen=100000  # Same as main stream limit
            )

            # Remove from DLQ
            await self.redis.xdel(dlq_key, dlq_message_id)

            logger.info(
                f"DLQ entry {dlq_message_id} retried to {target_stream} "
                f"(event {event_id})"
            )

            return True

        except Exception as e:
            logger.error(f"Error retrying DLQ entry {dlq_message_id}: {e}")
            return False

    async def retry_all(
        self,
        consumer_group: str,
        limit: int = 100,
        target_stream: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retry all entries in DLQ up to limit.

        Returns:
            Statistics about retry operation
        """
        stats = {
            "total_attempted": 0,
            "successful": 0,
            "failed": 0,
            "details": [],
        }

        # Get entries
        entries = await self.get_entries(consumer_group, limit=limit)

        for entry in entries:
            stats["total_attempted"] += 1

            try:
                success = await self.retry_entry(
                    consumer_group,
                    entry["dlq_message_id"],
                    target_stream
                )

                if success:
                    stats["successful"] += 1
                    stats["details"].append({
                        "dlq_message_id": entry["dlq_message_id"],
                        "status": "retried",
                        "event_id": entry.get("event_id", "unknown"),
                    })
                else:
                    stats["failed"] += 1
                    stats["details"].append({
                        "dlq_message_id": entry["dlq_message_id"],
                        "status": "failed",
                        "event_id": entry.get("event_id", "unknown"),
                    })

            except Exception as e:
                stats["failed"] += 1
                stats["details"].append({
                    "dlq_message_id": entry["dlq_message_id"],
                    "status": "error",
                    "error": str(e),
                    "event_id": entry.get("event_id", "unknown"),
                })
                logger.error(f"Error retrying {entry['dlq_message_id']}: {e}")

        return stats

    async def clean_old_entries(
        self,
        consumer_group: str,
        max_age_days: Optional[int] = None,
    ) -> int:
        """
        Clean old DLQ entries.

        Args:
            consumer_group: Consumer group name
            max_age_days: Maximum age in days (defaults to retention_days)

        Returns:
            Number of entries cleaned
        """
        max_age_days = max_age_days or self.retention_days

        dlq_key = self._get_dlq_key(consumer_group)

        try:
            # Get all entries
            entries = await self.redis.xrange(dlq_key, min="-", max="+")

            cleaned_count = 0
            cutoff_time = datetime.utcnow().timestamp() - (max_age_days * 86400)

            for msg_id, fields in entries:
                failed_at_str = fields.get(b"failed_at", b"").decode()

                try:
                    failed_at = datetime.fromisoformat(failed_at_str.replace("Z", "+00:00"))
                    failed_at_timestamp = failed_at.timestamp()

                    if failed_at_timestamp < cutoff_time:
                        # Delete old entry
                        await self.redis.xdel(dlq_key, msg_id)
                        cleaned_count += 1
                        logger.debug(f"Cleaned old DLQ entry {msg_id.decode()}")
                except (ValueError, TypeError) as e:
                    # If we can't parse timestamp, skip
                    logger.warning(f"Could not parse timestamp for DLQ entry {msg_id}: {e}")
                    continue

            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} old entries from DLQ {dlq_key}")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning DLQ: {e}")
            return 0

    async def health_check(self, consumer_group: str) -> Dict[str, Any]:
        """Health check for DLQ"""
        try:
            stats = await self.get_stats(consumer_group)

            return {
                "status": "healthy" if stats["exists"] else "no_dlq",
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
