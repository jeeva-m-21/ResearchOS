"""
Events Service - Main entry point for event infrastructure.

This service coordinates all event infrastructure components:
- Producer management
- Consumer groups
- Handler registration
- Health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import redis.asyncio as redis
import asyncpg

from .producer import EventProducer
from .consumer import EventConsumer
from .dlq import DeadLetterQueue
from .idempotency import IdempotencyChecker

# Import handlers
from .handlers.projections import ProjectionManager
from .handlers.notifications import NotificationManager

logger = logging.getLogger(__name__)


class EventsService:
    """
    Main coordination service for event infrastructure.
    
    Manages:
    - Multiple consumer groups (projectors, notifiers, embedders, auditors)
    - Handler registration and routing
    - Health monitoring
    - Graceful startup/shutdown
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        db_pool: asyncpg.Pool,
        organization_id: UUID,
    ):
        self.redis = redis_client
        self.db = db_pool
        self.organization_id = organization_id
        
        # Core infrastructure
        self.producer = EventProducer(redis_client)
        self.dlq = DeadLetterQueue(redis_client)
        self.idempotency_checker = IdempotencyChecker(redis_client, db_pool)
        
        # Event handlers
        self.projection_manager = ProjectionManager(db_pool)
        self.notification_manager = NotificationManager()  # TODO: Add WebSocket manager
        
        # Consumer groups
        self.consumers: Dict[str, EventConsumer] = {}
        
        # Metrics
        self.metrics = {
            "events_emitted": 0,
            "events_processed": 0,
            "consumer_errors": 0,
            "active_consumers": 0,
        }
        
    async def start_consumers(self) -> None:
        """Start all consumer groups for this organization"""
        consumer_groups = [
            ("projectors", "Update read models"),
            ("notifiers", "Send notifications"),
            ("embedders", "Generate embeddings"),
            ("auditors", "Write audit log"),
        ]
        
        for group_name, description in consumer_groups:
            consumer_name = f"{group_name}-{self.organization_id}"
            
            consumer = EventConsumer(
                redis_client=self.redis,
                consumer_group=group_name,
                consumer_name=consumer_name,
                organization_id=self.organization_id,
                dead_letter_queue=self.dlq,
                backoff_config={
                    "base_delay": 1.0,
                    "max_delay": 60.0,
                    "jitter": True,
                }
            )
            
            # Register handlers based on consumer group
            if group_name == "projectors":
                consumer.on("experiment.started")(self.projection_manager.handle_event)
                consumer.on("metric.logged")(self.projection_manager.handle_event)
                consumer.on("notebook.updated")(self.projection_manager.handle_event)
                consumer.on("paper.edited")(self.projection_manager.handle_event)
                
            elif group_name == "notifiers":
                consumer.on("experiment.started")(self.notification_manager.handle_event)
                consumer.on("metric.logged")(self.notification_manager.handle_event)
                consumer.on("notebook.updated")(self.notification_manager.handle_event)
            
            # Start consumer in background
            asyncio.create_task(consumer.start())
            
            self.consumers[group_name] = consumer
            self.metrics["active_consumers"] += 1
            
            logger.info(
                f"Started consumer {consumer_name} in group {group_name} "
                f"for organization {self.organization_id}"
            )
    
    async def stop_consumers(self, timeout: float = 30.0) -> None:
        """Stop all consumers gracefully"""
        logger.info(f"Stopping all consumers for organization {self.organization_id}")
        
        stop_tasks = []
        for group_name, consumer in self.consumers.items():
            stop_tasks.append(consumer.stop(timeout))
        
        # Wait for all consumers to stop
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.consumers.clear()
        self.metrics["active_consumers"] = 0
        
        logger.info(f"All consumers stopped for organization {self.organization_id}")
    
    async def emit_event(self, event) -> str:
        """Emit event and track metrics"""
        stream_id = await self.producer.emit(event)
        self.metrics["events_emitted"] += 1
        return stream_id
    
    async def emit_batch(self, events: List) -> List[str]:
        """Emit batch of events"""
        stream_ids = await self.producer.emit_batch(events)
        self.metrics["events_emitted"] += len(stream_ids)
        return stream_ids
    
    async def get_consumer_health(self, consumer_group: str) -> Dict[str, Any]:
        """Get health status for specific consumer group"""
        consumer = self.consumers.get(consumer_group)
        
        if not consumer:
            return {
                "status": "not_found",
                "consumer_group": consumer_group,
                "organization_id": str(self.organization_id),
            }
        
        return await consumer.health_check()
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for events service"""
        health_results = {
            "status": "healthy",
            "components": {},
            "organization_id": str(self.organization_id),
        }
        
        try:
            # Check Redis connection
            await self.redis.ping()
            health_results["components"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health_results["status"] = "unhealthy"
            health_results["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
        
        try:
            # Check database connection
            async with self.db.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_results["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_results["status"] = "unhealthy"
            health_results["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
        
        # Check producer
        producer_health = await self.producer.health_check()
        health_results["components"]["producer"] = producer_health
        
        # Check consumers
        for group_name, consumer in self.consumers.items():
            consumer_health = await consumer.health_check()
            health_results["components"][f"consumer_{group_name}"] = consumer_health
            
            if consumer_health.get("status") != "healthy":
                health_results["status"] = "degraded"
        
        # Check DLQ
        dlq_health = await self.dlq.health_check("projectors")  # Check first group
        health_results["components"]["dlq"] = dlq_health
        
        # Add metrics
        health_results["metrics"] = self.metrics.copy()
        
        return health_results
    
    async def get_stream_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        try:
            stream_info = await self.producer.get_stream_info(self.organization_id)
            
            # Get consumer group info
            consumer_groups = {}
            for group_name, consumer in self.consumers.items():
                try:
                    pending = await consumer.get_pending_messages()
                    lag = await consumer.get_consumer_lag()
                    
                    consumer_groups[group_name] = {
                        "pending_messages": len(pending),
                        "consumer_lag_seconds": lag,
                        "consumer_name": consumer.consumer_name,
                    }
                except Exception as e:
                    consumer_groups[group_name] = {
                        "error": str(e),
                    }
            
            return {
                "organization_id": str(self.organization_id),
                "stream_info": stream_info,
                "consumer_groups": consumer_groups,
                "metrics": self.metrics,
            }
            
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            return {
                "organization_id": str(self.organization_id),
                "error": str(e),
            }
    
    async def replay_events(
        self,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        event_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Replay events for this organization.
        
        Note: This is a simplified implementation. In production, 
        replay would read from event store (PostgreSQL) and re-emit.
        """
        # TODO: Implement proper replay from event store
        logger.warning(
            f"Replay requested for organization {self.organization_id} "
            f"from {from_timestamp} to {to_timestamp}"
        )
        
        return {
            "status": "not_implemented",
            "organization_id": str(self.organization_id),
            "message": "Event replay will be implemented with event store",
            "requested_range": {
                "from": from_timestamp,
                "to": to_timestamp,
                "event_types": event_types,
            },
        }


class EventsServiceFactory:
    """Factory for creating EventsService instances per organization"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        db_pool: asyncpg.Pool,
    ):
        self.redis = redis_client
        self.db = db_pool
        self.services: Dict[UUID, EventsService] = {}
    
    async def get_service(self, organization_id: UUID) -> EventsService:
        """Get or create EventsService for organization"""
        if organization_id not in self.services:
            service = EventsService(
                redis_client=self.redis,
                db_pool=self.db,
                organization_id=organization_id,
            )
            self.services[organization_id] = service
            
            # Start consumers for new service
            await service.start_consumers()
            
            logger.info(f"Created EventsService for organization {organization_id}")
        
        return self.services[organization_id]
    
    async def stop_all(self) -> None:
        """Stop all services"""
        logger.info(f"Stopping all event services ({len(self.services)} organizations)")
        
        stop_tasks = []
        for service in self.services.values():
            stop_tasks.append(service.stop_consumers())
        
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.services.clear()
        
        logger.info("All event services stopped")