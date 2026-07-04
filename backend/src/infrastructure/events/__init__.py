"""
Event Infrastructure for ResearchOS.

This module provides the event-driven architecture using Redis Streams.
Key components:

1. EventProducer: Emit events to Redis Streams
2. EventConsumer: Consume events with consumer groups
3. DeadLetterQueue: Handle poison pills
4. Backoff strategies: Retry with exponential backoff
5. Idempotency: Exactly-once processing guarantee
6. Event handlers: Projections, notifications, etc.

Design Constraints:
- Redis Streams capacity: ~1000 events/sec (plan Kafka migration if higher needed)
- Organization-scoped streams for tenant isolation
- Consumer groups for parallel processing
- Event ordering preserved per aggregate
"""

from .producer import EventProducer
from .consumer import EventConsumer
from .dlq import DeadLetterQueue
from .backoff import ExponentialBackoff, RetryLimiter
from .idempotency import IdempotencyChecker, IdempotentProcessor
from .service import EventsService, EventsServiceFactory

# Event handlers
from .handlers.projections import ProjectionHandler, ProjectionManager
from .handlers.notifications import NotificationHandler, NotificationManager

__all__ = [
    # Core infrastructure
    "EventProducer",
    "EventConsumer",
    "DeadLetterQueue",
    "ExponentialBackoff",
    "RetryLimiter",
    "IdempotencyChecker",
    "IdempotentProcessor",
    
    # Service layer
    "EventsService",
    "EventsServiceFactory",
    
    # Event handlers
    "ProjectionHandler",
    "ProjectionManager",
    "NotificationHandler",
    "NotificationManager",
]
