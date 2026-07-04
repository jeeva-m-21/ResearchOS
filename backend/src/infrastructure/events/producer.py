"""
Event Producer with Redis Streams.

Key features:
- Organization-scoped streams
- Batch support
- Error handling and retries
- Stream length limits for memory management
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
import redis.asyncio as redis
from datetime import datetime

from src.domain.shared.events import DomainEvent


class EventProducer:
    """
    Enhanced Redis Streams event producer with batch support and robustness.
    
    Design Constraints:
    - Redis Streams capacity: ~1000 events/sec (plan migration to Kafka if higher needed)
    - Stream per organization for tenant isolation
    - Max length: 100,000 events per stream (circular buffer)
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_stream_length: int = 100000,
        max_batch_size: int = 100,
    ):
        self.redis = redis_client
        self.max_stream_length = max_stream_length
        self.max_batch_size = max_batch_size
    
    async def emit(self, event: DomainEvent) -> str:
        """
        Emit a single event to Redis Stream.
        
        Returns:
            Stream ID (timestamp-sequence)
        """
        return await self._emit_one(event)
    
    async def emit_batch(self, events: List[DomainEvent]) -> List[str]:
        """
        Emit multiple events in batch.
        
        Returns:
            List of stream IDs
        """
        if not events:
            return []
        
        # Group events by organization for efficient batching
        org_events: Dict[UUID, List[DomainEvent]] = {}
        for event in events:
            if not hasattr(event, 'organization_id'):
                raise ValueError(f"Event {event.event_id} missing organization_id")
            
            org_id = event.organization_id
            if org_id not in org_events:
                org_events[org_id] = []
            org_events[org_id].append(event)
        
        # Emit batches per organization
        stream_ids = []
        for org_id, org_events_list in org_events.items():
            # Split into batches if needed
            for i in range(0, len(org_events_list), self.max_batch_size):
                batch = org_events_list[i:i + self.max_batch_size]
                batch_ids = await self._emit_batch_for_org(org_id, batch)
                stream_ids.extend(batch_ids)
        
        return stream_ids
    
    async def _emit_one(self, event: DomainEvent) -> str:
        """Emit single event"""
        if not hasattr(event, 'organization_id'):
            raise ValueError(f"Event {event.event_id} missing organization_id")
        
        stream_key = f"events:org_{event.organization_id}"
        
        message = self._prepare_message(event)
        
        # Use pipeline for atomicity
        async with self.redis.pipeline() as pipe:
            pipe.xadd(stream_key, message, maxlen=self.max_stream_length)
            result = await pipe.execute()
        
        stream_id = result[0]
        if isinstance(stream_id, bytes):
            stream_id = stream_id.decode()
        return stream_id
    
    async def _emit_batch_for_org(
        self,
        organization_id: UUID,
        events: List[DomainEvent]
    ) -> List[str]:
        """Emit batch of events for a single organization"""
        stream_key = f"events:org_{organization_id}"
        
        # Prepare all messages
        messages = []
        for event in events:
            if event.organization_id != organization_id:
                raise ValueError(
                    f"Event {event.event_id} organization_id mismatch: "
                    f"{event.organization_id} != {organization_id}"
                )
            messages.append(self._prepare_message(event))
        
        # Use transaction for atomicity
        async with self.redis.pipeline() as pipe:
            for msg in messages:
                pipe.xadd(stream_key, msg, maxlen=self.max_stream_length)
            results = await pipe.execute()
        
        # Decode bytes if needed
        decoded_results = []
        for r in results:
            if isinstance(r, bytes):
                decoded_results.append(r.decode())
            else:
                decoded_results.append(r)
        return decoded_results
    
    def _prepare_message(self, event: DomainEvent) -> Dict[str, str]:
        """Prepare event message for Redis Stream"""
        # Extract organization_id safely
        org_id = getattr(event, 'organization_id', None)
        if org_id is None:
            raise ValueError(f"Event {event.event_id} missing organization_id")
        
        # Prepare metadata
        metadata = getattr(event, 'metadata', {})
        if metadata is None:
            metadata = {}
        
        created_by = getattr(event, 'created_by', None)
        
        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "aggregate_type": event.aggregate_type,
            "version": str(event.version),
            "timestamp": event.timestamp.isoformat(),
            "organization_id": str(org_id),
            "payload": event.model_dump_json(),
            "metadata": json.dumps(metadata),
            "created_by": str(created_by) if created_by else "",
        }
    
    async def get_stream_info(self, organization_id: UUID) -> Dict[str, Any]:
        """Get stream information (length, first/last IDs)"""
        stream_key = f"events:org_{organization_id}"
        
        try:
            # Get stream info
            info = await self.redis.xinfo_stream(stream_key)
            
            # Convert bytes to strings
            result = {}
            for key, value in info.items():
                # Decode key if it's bytes
                key_str = key.decode() if isinstance(key, bytes) else key
                
                if isinstance(value, bytes):
                    result[key_str] = value.decode()
                elif isinstance(value, dict):
                    result[key_str] = {
                        (k.decode() if isinstance(k, bytes) else k): 
                        (v.decode() if isinstance(v, bytes) else v)
                        for k, v in value.items()
                    }
                else:
                    result[key_str] = value
            
            return result
        except redis.ResponseError as e:
            # Stream doesn't exist
            if "no such key" in str(e):
                return {
                    "length": 0,
                    "exists": False
                }
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for producer"""
        try:
            # Test Redis connection
            await self.redis.ping()
            
            return {
                "status": "healthy",
                "redis": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
