"""Shared event producer dependency for API routes"""
import os
from typing import Optional

from redis.asyncio import Redis

from src.infrastructure.events.producer import EventProducer

_producer: Optional[EventProducer] = None
_redis: Optional[Redis] = None


async def get_event_producer() -> EventProducer:
    """Get or create cached EventProducer singleton"""
    global _producer, _redis

    if _producer is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis = Redis.from_url(redis_url, decode_responses=False)
        _producer = EventProducer(_redis)

    return _producer
