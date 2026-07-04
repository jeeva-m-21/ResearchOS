# ResearchOS - Event Architecture

## Overview

ResearchOS uses an event-driven architecture for state changes, enabling:
- Audit trails
- Event replay
- CQRS projections
- Real-time notifications
- Integration with external systems

---

## Design Goals

1. **Kafka-Style Model**: Topics, partitions, consumer groups
2. **Redis Streams**: Lightweight, in-memory event streaming
3. **Retries**: Exponential backoff for transient failures
4. **Dead Letter Queues**: Isolate poison pills
5. **Idempotency**: Exactly-once processing
6. **Ordering**: Per-aggregate ordering guarantees
7. **Replay**: Time-travel and reprocessing

---

## Scalability Warning

⚠️ **Critical Configuration Limits:**

Redis Streams is designed for **low-to-medium throughput** (<1,000 events/sec):

**Limitations:**
- Memory-bound: All messages must fit in RAM
- No native disk persistence (AOF/RDB is for Redis state)
- Basic consumer group rebalancing compared to Kafka
- Stream trimming required to prevent unbounded growth

**Thresholds:**
| Throughput | Recommendation |
|------------|----------------|
| <100 events/sec | Redis Streams (default) ✅ |
| 100-1,000 events/sec | Redis Streams + aggressive monitoring ⚠️ |
| 1,000-10,000 events/sec | Kafka/Kinesis required ❌ |
| >10,000 events/sec | Kafka with partitioning required ❌ |

**Scaling Path:**
```
MVP (<1K users)     → Redis Streams
Growth (<10K users) → Kafka with Redis for consumer groups  
Enterprise          → Kafka with 12+ partitions per org
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVENT PRODUCERS                               │
│  - SDK (Python)                                                      │
│  - API (FastAPI)                                                    │
│  - Workers (Background jobs)                                        │
│  - Webhooks (External systems)                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ emit(event)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT BUS (Redis Streams)                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Streams                                                       │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  events:org_{org_id}                                       │ │ │
│  │  │  - Per-organization stream                                │ │ │
│  │  │  - Ordered by timestamp                                   │ │ │
│  │  │  - Consumer groups for parallel processing               │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Consumer Groups                                                │ │
│  │  - projectors: Update read models                             │ │
│  │  - notifiers: Send notifications                               │ │
│  │  - embedders: Generate embeddings                             │ │
│  │  - auditors: Write audit log                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ consume(event)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT CONSUMERS                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Projectors  │  │  Notifiers   │  │  Embedders   │              │
│  │  (CQRS)      │  │  (WebSocket) │  │  (Search)    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │  Auditors    │  │  DLQ Handler │                                │
│  │  (Audit Log) │  │  (Dead Letter)│                               │
│  └──────────────┘  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT STORE (PostgreSQL)                         │
│  - Append-only log                                                  │
│  - Event_id uniqueness (idempotency)                               │
│  - Metadata (timestamp, version, aggregate_id)                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Event Types

```python
# src/domain/shared/events.py

from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from enum import Enum

class EventType(str, Enum):
    # Experiment events
    EXPERIMENT_STARTED = "experiment.started"
    EXPERIMENT_COMPLETED = "experiment.completed"
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    METRIC_LOGGED = "metric.logged"
    PARAMETER_SET = "parameter.set"
    ARTIFACT_UPLOADED = "artifact.uploaded"
    
    # Notebook events
    NOTEBOOK_UPDATED = "notebook.updated"
    BLOCK_EXECUTED = "block.executed"
    
    # Paper events
    PAPER_EDITED = "paper.edited"
    CITATION_ADDED = "citation.added"
    
    # Research graph events
    NODE_CREATED = "node.created"
    NODE_UPDATED = "node.updated"
    EDGE_CREATED = "edge.created"
    
    # Git events
    GIT_COMMIT = "git.commit"

class DomainEvent(BaseModel):
    """Base event model"""
    
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Aggregate identification
    aggregate_id: UUID
    aggregate_type: str
    version: int = Field(ge=1)
    
    # Tenant
    organization_id: UUID
    
    # Actor
    created_by: UUID
    
    # Metadata
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

class ExperimentStarted(DomainEvent):
    event_type: Literal["experiment.started"] = "experiment.started"
    experiment_id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    tags: list[str]

class MetricLogged(DomainEvent):
    event_type: Literal["metric.logged"] = "metric.logged"
    run_id: UUID
    experiment_id: UUID
    key: str
    value: float
    step: int
    wall_time: float

class NotebookUpdated(DomainEvent):
    event_type: Literal["notebook.updated"] = "notebook.updated"
    notebook_id: UUID
    operation: str  # "add_block", "remove_block", "update_block"
    block_id: Optional[UUID]
    content: Optional[str]

class ArtifactUploaded(DomainEvent):
    event_type: Literal["artifact.uploaded"] = "artifact.uploaded"
    artifact_id: UUID
    name: str
    artifact_type: str
    mime_type: str
    size_bytes: int
    hash_sha256: str
    experiment_id: Optional[UUID]
    run_id: Optional[UUID]

class GitCommit(DomainEvent):
    event_type: Literal["git.commit"] = "git.commit"
    commit_sha: str
    branch: Optional[str]
    message: Optional[str]
    author: Optional[str]
    is_dirty: bool
    remote_url: Optional[str]

class PaperEdited(DomainEvent):
    event_type: Literal["paper.edited"] = "paper.edited"
    paper_id: UUID
    version: int
    changes: dict[str, Any]
```

---

## Event Bus (Redis Streams)

### Stream Structure

```
Redis Key: events:org_{org_id}

Message Format:
{
  "id": "1609459200000-0",  // Redis stream ID (timestamp-sequence)
  "event_id": "uuid",
  "event_type": "metric.logged",
  "aggregate_id": "uuid",
  "aggregate_type": "Run",
  "organization_id": "uuid",
  "version": 1,
  "timestamp": "2024-01-01T00:00:00Z",
  "payload": {...},
  "metadata": {...}
}

Consumer Groups:
- projectors: Update read models
- notifiers: Send WebSocket notifications
- embedders: Generate embeddings
- auditors: Write to audit log
```

### Producer

```python
# src/infrastructure/events/producer.py

import redis.asyncio as redis
import json
from uuid import UUID
from .events import DomainEvent

class EventProducer:
    """
    Event producer using Redis Streams.
    
    Features:
    - Append to organization stream
    - Automatic timestamp ordering
    - Consumer group support
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def emit(self, event: DomainEvent) -> str:
        """
        Emit event to stream.
        
        Returns:
            Stream ID (timestamp-sequence)
        """
        
        stream_key = f"events:org_{event.organization_id}"
        
        message = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "aggregate_type": event.aggregate_type,
            "organization_id": str(event.organization_id),
            "version": event.version,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.model_dump_json(),
            "metadata": json.dumps(event.metadata),
            "created_by": str(event.created_by)
        }
        
        # XADD to stream
        stream_id = await self.redis.xadd(
            stream_key,
            message,
            maxlen=10000000  # Limit stream length
        )
        
        return stream_id.decode()
    
    async def emit_batch(self, events: list[DomainEvent]) -> list[str]:
        """
        Emit multiple events.
        
        Returns:
            List of stream IDs
        """
        
        stream_ids = []
        
        # Group by organization
        for org_id, org_events in self._group_by_org(events):
            stream_key = f"events:org_{org_id}"
            
            messages = []
            for event in org_events:
                messages.append({
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "aggregate_id": str(event.aggregate_id),
                    "aggregate_type": event.aggregate_type,
                    "organization_id": str(event.organization_id),
                    "version": event.version,
                    "timestamp": event.timestamp.isoformat(),
                    "payload": event.model_dump_json(),
                    "metadata": json.dumps(event.metadata)
                })
            
            # Use pipeline for batch
            async with self.redis.pipeline() as pipe:
                for msg in messages:
                    pipe.xadd(stream_key, msg, maxlen=10000000)
                results = await pipe.execute()
                stream_ids.extend([r.decode() for r in results])
        
        return stream_ids
```

### Consumer

```python
# src/infrastructure/events/consumer.py

import asyncio
from typing import Callable, Awaitable
from redis.asyncio import Redis

class EventConsumer:
    """
    Event consumer using Redis Streams consumer groups.
    
    Features:
    - Consumer group for parallel processing
    - Automatic claim of pending messages
    - Retry handling
    - Dead letter queue
    """
    
    def __init__(
        self,
        redis: Redis,
        group_name: str,
        consumer_name: str,
        batch_size: int = 10,
        block_ms: int = 1000,
    ):
        self.redis = redis
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.batch_size = batch_size
        self.block_ms = block_ms
        
        self.handlers: dict[str, Callable] = {}
        self.running = False
    
    def on(self, event_type: str):
        """Register handler for event type"""
        def decorator(func: Callable):
            self.handlers[event_type] = func
            return func
        return decorator
    
    async def start(self, organization_id: UUID) -> None:
        """
        Start consuming events.
        
        Creates consumer group if not exists.
        """
        
        stream_key = f"events:org_{organization_id}"
        
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(
                stream_key,
                self.group_name,
                id="0",
                mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        
        self.running = True
        
        while self.running:
            try:
                # Read from stream
                messages = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={stream_key: ">"},
                    count=self.batch_size,
                    block=self.block_ms
                )
                
                if not messages:
                    continue
                
                # Process messages
                for stream, msg_list in messages:
                    for msg_id, fields in msg_list:
                        await self._process_message(msg_id, fields)
                
            except Exception as e:
                print(f"Consumer error: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, msg_id: bytes, fields: dict) -> None:
        """Process single message"""
        
        event_type = fields.get(b"event_type", b"").decode()
        event_id = fields.get(b"event_id", b"").decode()
        
        try:
            # Get handler
            handler = self.handlers.get(event_type)
            if not handler:
                # Acknowledge unknown event types
                await self.redis.xack(stream_key, self.group_name, msg_id)
                return
            
            # Execute handler
            event = self._parse_event(fields)
            await handler(event)
            
            # Acknowledge
            await self.redis.xack(stream_key, self.group_name, msg_id)
            
        except Exception as e:
            # Handle failure
            await self._handle_failure(msg_id, fields, e)
    
    async def _handle_failure(
        self,
        msg_id: bytes,
        fields: dict,
        error: Exception
    ) -> None:
        """Handle message processing failure"""
        
        # Get delivery count from Redis stream
        # Redis doesn't track delivery count, so we use our own mechanism
        event_id = fields.get(b"event_id").decode()
        retry_key = f"retry:{event_id}"
        
        retries = await self.redis.incr(retry_key)
        await self.redis.expire(retry_key, 86400)  # 24h
        
        if retries >= 3:
            # Move to DLQ
            await self._move_to_dlq(fields, error)
            await self.redis.xack(stream_key, self.group_name, msg_id)
            await self.redis.delete(retry_key)
        else:
            # Leave in pending list for retry
            # Will be claimed by another consumer after idle timeout
            pass
    
    async def _move_to_dlq(self, fields: dict, error: Exception) -> None:
        """Move message to dead letter queue"""
        
        dlq_key = f"dlq:{self.group_name}"
        
        await self.redis.xadd(
            dlq_key,
            {
                b"original_event": json.dumps(fields),
                b"error": str(error),
                b"failed_at": datetime.utcnow().isoformat()
            }
        )
    
    def _parse_event(self, fields: dict) -> DomainEvent:
        """Parse event from Redis fields"""
        payload = json.loads(fields[b"payload"])
        event_type = fields[b"event_type"].decode()
        
        event_classes = {
            "experiment.started": ExperimentStarted,
            "metric.logged": MetricLogged,
            "notebook.updated": NotebookUpdated,
            "artifact.uploaded": ArtifactUploaded,
            "git.commit": GitCommit,
            "paper.edited": PaperEdited,
        }
        
        event_class = event_classes.get(event_type, DomainEvent)
        return event_class(**payload)
```

---

## Event Store (PostgreSQL)

```python
# src/infrastructure/events/store.py

import asyncpg

class EventStore:
    """
    Append-only event store in PostgreSQL.
    
    Features:
    - Event_id uniqueness (idempotency)
    - Ordering by timestamp
    - Replay support
    """
    
    def __init__(self, db: asyncpg.Connection):
        self.db = db
    
    async def append(self, event: DomainEvent) -> None:
        """
        Append event to store.
        
        Raises:
            IntegrityError if event_id already exists (duplicate)
        """
        
        await self.db.execute(
            """
            INSERT INTO events (
                event_id,
                organization_id,
                event_type,
                aggregate_id,
                aggregate_type,
                version,
                payload,
                metadata,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (event_id) DO NOTHING
            """,
            event.event_id,
            event.organization_id,
            event.event_type,
            event.aggregate_id,
            event.aggregate_type,
            event.version,
            event.model_dump_json(),
            event.metadata,
            event.timestamp
        )
    
    async def get_events(
        self,
        organization_id: UUID,
        aggregate_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Get events for replay or querying"""
        
        conditions = ["organization_id = $1"]
        params = [organization_id]
        
        if aggregate_id:
            conditions.append(f"aggregate_id = ${len(params) + 1}")
            params.append(aggregate_id)
        
        if event_type:
            conditions.append(f"event_type = ${len(params) + 1}")
            params.append(event_type)
        
        if from_timestamp:
            conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(from_timestamp)
        
        if to_timestamp:
            conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(to_timestamp)
        
        params.append(limit)
        
        rows = await self.db.fetch(
            f"""
            SELECT * FROM events
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at ASC
            LIMIT ${len(params)}
            """,
            *params
        )
        
        return [self._parse_event(row) for row in rows]
    
    async def replay(
        self,
        organization_id: UUID,
        from_timestamp: Optional[datetime] = None,
        handlers: dict[str, Callable] = None,
    ) -> None:
        """
        Replay events for reprocessing.
        
        Used for:
        - Rebuilding projections
        - Fixing data inconsistencies
        - Migration
        """
        
        offset = 0
        batch_size = 100
        
        while True:
            events = await self.get_events(
                organization_id,
                from_timestamp=from_timestamp,
                limit=batch_size,
                offset=offset
            )
            
            if not events:
                break
            
            for event in events:
                handler = handlers.get(event.event_type)
                if handler:
                    await handler(event)
            
            offset += batch_size
```

---

## Idempotency

### Exactly-Once Processing

```python
# src/infrastructure/events/idempotency.py

class IdempotentHandler:
    """
    Ensures exactly-once processing using event_id.
    """
    
    def __init__(self, db, redis):
        self.db = db
        self.redis = redis
    
    async def process(self, event: DomainEvent, handler: Callable) -> None:
        """
        Process event idempotently.
        
        Checks if event was already processed before executing.
        """
        
        # Check cache first (fast path)
        cache_key = f"processed:{event.event_id}"
        if await self.redis.exists(cache_key):
            return  # Already processed
        
        # Check database (idempotency table)
        processed = await self.db.fetch_val(
            "SELECT 1 FROM processed_events WHERE event_id = $1",
            event.event_id
        )
        
        if processed:
            # Cache for next time
            await self.redis.setex(cache_key, 86400, "1")
            return
        
        # Process event
        await handler(event)
        
        # Mark as processed
        await self.db.execute(
            "INSERT INTO processed_events (event_id, processed_at) VALUES ($1, $2)",
            event.event_id,
            datetime.utcnow()
        )
        
        # Cache
        await self.redis.setex(cache_key, 86400, "1")
```

### Processed Events Table

```sql
CREATE TABLE processed_events (
    event_id UUID PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_processed_events_time ON processed_events(processed_at);
```

---

## Ordering

### Per-Aggregate Ordering

```python
class OrderedEventProcessor:
    """
    Ensures events for the same aggregate are processed in order.
    
    Uses partitioning by aggregate_id.
    """
    
    def __init__(self, num_partitions: int = 16):
        self.num_partitions = num_partitions
        self.partition_queues: dict[int, asyncio.Queue] = {
            i: asyncio.Queue() for i in range(num_partitions)
        }
        self.partition_workers: dict[int, asyncio.Task] = {}
    
    def get_partition(self, aggregate_id: UUID) -> int:
        """Get partition for aggregate"""
        return aggregate_id.int % self.num_partitions
    
    async def start(self) -> None:
        """Start partition workers"""
        for partition_id, queue in self.partition_queues.items():
            self.partition_workers[partition_id] = asyncio.create_task(
                self._process_partition(partition_id, queue)
            )
    
    async def process(self, event: DomainEvent) -> None:
        """Queue event for ordered processing"""
        partition = self.get_partition(event.aggregate_id)
        await self.partition_queues[partition].put(event)
    
    async def _process_partition(self, partition_id: int, queue: asyncio.Queue) -> None:
        """Process events from partition queue (maintains order)"""
        while True:
            event = await queue.get()
            try:
                await self._handle_event(event)
            except Exception as e:
                print(f"Error processing event {event.event_id}: {e}")
            finally:
                queue.task_done()
```

---

## Retries & Dead Letter Queue

### Retry Strategy

```python
# src/infrastructure/events/retry.py

import asyncio
from functools import wraps

class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True

def with_retry(config: RetryConfig = RetryConfig()):
    """Decorator for retry with exponential backoff"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(config.max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if attempt < config.max_retries - 1:
                        delay = min(
                            config.base_delay * (2 ** attempt),
                            config.max_delay
                        )
                        
                        if config.jitter:
                            delay = delay * (0.5 + random.random())
                        
                        print(f"Retry {attempt + 1}/{config.max_retries} after {delay}s: {e}")
                        await asyncio.sleep(delay)
            
            raise last_error
        
        return wrapper
    return decorator

class DeadLetterQueue:
    """
    Dead Letter Queue for failed events.
    
    Stores events that failed after max retries.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def add(
        self,
        event: DomainEvent,
        error: Exception,
        consumer_group: str,
    ) -> None:
        """Add failed event to DLQ"""
        
        dlq_key = f"dlq:{consumer_group}"
        
        await self.redis.xadd(
            dlq_key,
            {
                b"event_id": str(event.event_id),
                b"event_type": event.event_type,
                b"payload": event.model_dump_json(),
                b"error": str(error),
                b"failed_at": datetime.utcnow().isoformat()
            }
        )
    
    async def get_pending(
        self,
        consumer_group: str,
        limit: int = 100,
    ) -> list[dict]:
        """Get pending events from DLQ"""
        
        dlq_key = f"dlq:{consumer_group}"
        
        messages = await self.redis.xrange(dlq_key, count=limit)
        
        return [
            {
                "id": msg_id,
                **{k.decode(): v.decode() for k, v in fields.items()}
            }
            for msg_id, fields in messages
        ]
    
    async def retry(
        self,
        dlq_msg_id: str,
        consumer_group: str,
        event_processor,
    ) -> None:
        """Retry event from DLQ"""
        
        dlq_key = f"dlq:{consumer_group}"
        
        # Get message
        msg = await self.redis.xrange(dlq_key, dlq_msg_id, dlq_msg_id)
        if not msg:
            return
        
        _, fields = msg[0]
        
        # Parse event
        event = json.loads(fields[b"payload"])
        
        # Retry processing
        try:
            await event_processor.process(event)
            
            # Remove from DLQ on success
            await self.redis.xdel(dlq_key, dlq_msg_id)
        except Exception as e:
            # Update error
            await self.redis.xadd(
                dlq_key,
                {
                    b"event_id": fields[b"event_id"],
                    b"payload": fields[b"payload"],
                    b"error": str(e),
                    b"retried_at": datetime.utcnow().isoformat()
                }
            )
            await self.redis.xdel(dlq_key, dlq_msg_id)
```

---

## Event Handlers

### Projections (CQRS Read Models)

```python
# src/infrastructure/events/handlers/projections.py

class ProjectionHandler:
    """
    Updates read model projections from events.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def handle_experiment_started(self, event: ExperimentStarted) -> None:
        # Update experiment summary view
        await self.db.execute(
            """
            INSERT INTO active_experiments (id, name, status, project_id, organization_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status
            """,
            event.experiment_id,
            event.name,
            "running",
            event.project_id,
            event.organization_id
        )
    
    async def handle_metric_logged(self, event: MetricLogged) -> None:
        # Update metric summary aggregation
        await self.db.execute(
            """
            INSERT INTO metric_summary (run_id, key, min_value, max_value, avg_value, count, last_updated)
            VALUES ($1, $2, $3, $3, $3, 1, $4)
            ON CONFLICT (run_id, key) DO UPDATE SET
                min_value = LEAST(metric_summary.min_value, $3),
                max_value = GREATEST(metric_summary.max_value, $3),
                avg_value = (metric_summary.avg_value * metric_summary.count + $3) / (metric_summary.count + 1),
                count = metric_summary.count + 1,
                last_updated = $4
            """,
            event.run_id,
            event.key,
            event.value,
            event.timestamp
        )
```

### Notifications

```python
# src/infrastructure/events/handlers/notifications.py

class NotificationHandler:
    """
    Sends WebSocket notifications for events.
    """
    
    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
    
    async def handle_experiment_started(self, event: ExperimentStarted) -> None:
        # Notify organization members
        await self.ws_manager.broadcast_to_org(
            event.organization_id,
            {
                "type": "experiment.started",
                "experiment_id": str(event.experiment_id),
                "name": event.name,
                "timestamp": event.timestamp.isoformat()
            }
        )
    
    async def handle_metric_logged(self, event: MetricLogged) -> None:
        # Send real-time metric update
        await self.ws_manager.broadcast_to_org(
            event.organization_id,
            {
                "type": "metric.logged",
                "run_id": str(event.run_id),
                "key": event.key,
                "value": event.value,
                "step": event.step
            }
        )
```

### Embeddings

```python
# src/infrastructure/events/handlers/embeddings.py

class EmbeddingHandler:
    """
    Generates embeddings for search.
    """
    
    def __init__(self, embedding_adapter, db):
        self.embedding = embedding_adapter
        self.db = db
    
    async def handle_node_created(self, event: NodeCreated) -> None:
        # Generate embedding
        text = f"{event.title}\n{event.description or ''}"
        embedding = await self.embedding.embed([text])
        
        # Update node
        await self.db.execute(
            "UPDATE nodes SET embedding = $1 WHERE id = $2",
            embedding[0],
            event.node_id
        )
    
    async def handle_paper_edited(self, event: PaperEdited) -> None:
        # Re-embed paper
        paper = await self.db.fetch_one(
            "SELECT title, abstract FROM papers WHERE id = $1",
            event.paper_id
        )
        
        text = f"{paper['title']}\n{paper['abstract'] or ''}"
        embedding = await self.embedding.embed([text])
        
        node = await self.db.fetch_val(
            "SELECT node_id FROM papers WHERE id = $1",
            event.paper_id
        )
        
        await self.db.execute(
            "UPDATE nodes SET embedding = $1 WHERE id = $2",
            embedding[0],
            node
        )
```

---

## Consumer Group Setup

```python
# src/infrastructure/events/consumer_groups.py

async def setup_consumer_groups(redis: Redis) -> None:
    """Setup consumer groups for each stream"""
    
    # For each organization, create consumer groups
    # This is typically done when organization is created
    
    groups = [
        ("projectors", "Update read models"),
        ("notifiers", "Send notifications"),
        ("embedders", "Generate embeddings"),
        ("auditors", "Write audit log"),
    ]
    
    # Consumer groups are created lazily when consumer starts

async def start_consumers(organization_id: UUID) -> None:
    """Start all consumer groups for organization"""
    
    consumers = [
        EventConsumer(redis, "projectors", f"projector-{uuid4()}"),
        EventConsumer(redis, "notifiers", f"notifier-{uuid4()}"),
        EventConsumer(redis, "embedders", f"embedder-{uuid4()}"),
        EventConsumer(redis, "auditors", f"auditor-{uuid4()}"),
    ]
    
    # Register handlers
    consumers[0].on("experiment.started")(projection_handler.handle_experiment_started)
    consumers[0].on("metric.logged")(projection_handler.handle_metric_logged)
    
    consumers[1].on("experiment.started")(notification_handler.handle_experiment_started)
    consumers[1].on("metric.logged")(notification_handler.handle_metric_logged)
    
    consumers[2].on("node.created")(embedding_handler.handle_node_created)
    consumers[2].on("paper.edited")(embedding_handler.handle_paper_edited)
    
    # Start all consumers
    await asyncio.gather(*[c.start(organization_id) for c in consumers])
```

---

## Replay & Time-Travel

```python
# src/application/events/replay.py

class EventReplay:
    """
    Replay events for debugging, migration, or rebuilding projections.
    """
    
    async def replay_organization(
        self,
        organization_id: UUID,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        event_types: Optional[list[str]] = None,
        dry_run: bool = False,
    ) -> ReplayResult:
        """
        Replay events for an organization.
        
        Args:
            dry_run: If True, don't apply events, just return count
        """
        
        events = await self.event_store.get_events(
            organization_id,
            event_type=event_types[0] if event_types else None,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=1000000
        )
        
        if dry_run:
            return ReplayResult(
                count=len(events),
                event_types={e.event_type for e in events}
            )
        
        # Replay
        for event in events:
            handler = self.handlers.get(event.event_type)
            if handler:
                await handler(event)
        
        return ReplayResult(count=len(events))
    
    async def rebuild_projections(
        self,
        organization_id: UUID,
    ) -> None:
        """
        Rebuild all projections from events.
        
        Used for:
        - Fixing data inconsistencies
        - Schema migrations
        - New projection added
        """
        
        # Clear existing projections
        await self.db.execute(
            "DELETE FROM metric_summary WHERE organization_id = $1",
            organization_id
        )
        
        # Replay all events
        await self.replay_organization(organization_id)
```

---

## Monitoring

```python
# Track event processing
metrics.histogram("event.processing_time", duration_ms, tags={
    "event_type": event.event_type,
    "consumer_group": group_name
})

metrics.increment("event.processed", tags={
    "event_type": event.event_type,
    "status": "success"
})

# Track DLQ
metrics.gauge("dlq.size", await dlq.size("projectors"), tags={
    "consumer_group": "projectors"
})

# Track consumer lag
last_event_time = await redis.xinfo_stream(stream_key).last_event_time
lag = datetime.utcnow() - last_event_time
metrics.gauge("consumer.lag_seconds", lag.total_seconds())
```

---

## Summary

ResearchOS event architecture provides:

| Feature | Implementation |
|---------|---------------|
| **Message Broker** | Redis Streams |
| **Event Store** | PostgreSQL (append-only) |
| **Idempotency** | event_id uniqueness |
| **Ordering** | Per-aggregate partitioning |
| **Retries** | Exponential backoff (3 retries) |
| **DLQ** | Redis stream per consumer group |
| **Replay** | Time-range query from event store |
| **Consumer Groups** | Parallel processing |

---

## Next Steps

- Implementation → Backend `/v1/events/batch` endpoint
- SDK integration → SDK WAL → Backend sync
- Monitoring → Event processing metrics
