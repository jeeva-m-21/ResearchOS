"""
Example demonstrating the Event Infrastructure.

This script shows how to use the event infrastructure components.
Note: This is a conceptual example - actual implementation would need
proper Redis and PostgreSQL connections.
"""

import asyncio
import logging
from uuid import uuid4, UUID
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example event classes (simplified)
class DomainEvent:
    def __init__(self, event_type: str, aggregate_id: UUID, organization_id: UUID):
        self.event_id = uuid4()
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.aggregate_type = "Aggregate"
        self.version = 1
        self.timestamp = datetime.utcnow()
        self.organization_id = organization_id
        self.created_by = uuid4()  # Simulated user
    
    def model_dump_json(self):
        """Simplified serialization"""
        import json
        return json.dumps({
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": str(self.aggregate_id),
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "organization_id": str(self.organization_id),
            "created_by": str(self.created_by),
        })


async def example_event_flow():
    """
    Example demonstrating the complete event flow:
    1. Create events
    2. Emit to Redis Stream
    3. Process with consumer
    4. Handle exceptions and DLQ
    """
    logger.info("=== Event Infrastructure Example ===")
    
    # Note: Actual implementation would need Redis and DB connections
    # This is a conceptual demonstration
    
    from src.infrastructure.events.backoff import ExponentialBackoff
    
    # 1. Demonstrate backoff strategy
    logger.info("\n1. Exponential Backoff Example:")
    backoff = ExponentialBackoff(base_delay=1.0, max_delay=10.0, jitter=True)
    
    for attempt in range(5):
        delay = backoff.get_delay()
        logger.info(f"  Attempt {attempt + 1}: Delay = {delay:.2f}s")
    
    backoff.reset()
    logger.info(f"  After reset: Attempt = {backoff.get_attempt()}")
    
    # 2. Simulate event flow
    logger.info("\n2. Event Flow Simulation:")
    
    # Create example events
    org_id = uuid4()
    experiment_id = uuid4()
    
    experiment_started = DomainEvent(
        event_type="experiment.started",
        aggregate_id=experiment_id,
        organization_id=org_id
    )
    
    metric_logged = DomainEvent(
        event_type="metric.logged",
        aggregate_id=experiment_id,
        organization_id=org_id
    )
    
    logger.info(f"  Created events:")
    logger.info(f"    - {experiment_started.event_type} (ID: {experiment_started.event_id})")
    logger.info(f"    - {metric_logged.event_type} (ID: {metric_logged.event_id})")
    
    # 3. Show handler registration pattern
    logger.info("\n3. Event Handler Registration:")
    
    handlers = {
        "experiment.started": lambda e: logger.info(f"    Processing experiment started: {e.event_id}"),
        "metric.logged": lambda e: logger.info(f"    Processing metric logged: {e.event_id}"),
    }
    
    # Simulate event routing
    events = [experiment_started, metric_logged]
    for event in events:
        handler = handlers.get(event.event_type)
        if handler:
            handler(event)
        else:
            logger.info(f"    No handler for {event.event_type}")
    
    # 4. DLQ simulation
    logger.info("\n4. Dead Letter Queue Simulation:")
    
    # Simulated DLQ entry
    dlq_entry = {
        "event_id": str(uuid4()),
        "event_type": "experiment.failed",
        "error": "Max retries exceeded: Connection timeout",
        "retry_count": 3,
        "failed_at": datetime.utcnow().isoformat(),
    }
    
    logger.info(f"  DLQ Entry:")
    for key, value in dlq_entry.items():
        logger.info(f"    {key}: {value}")
    
    # 5. Idempotency check simulation
    logger.info("\n5. Idempotency Check:")
    
    processed_events = set()
    
    # First processing
    event_id = uuid4()
    if event_id not in processed_events:
        logger.info(f"  Processing event {event_id} (first time)")
        processed_events.add(event_id)
    else:
        logger.info(f"  Event {event_id} already processed, skipping")
    
    # Second attempt (should be skipped)
    if event_id not in processed_events:
        logger.info(f"  Processing event {event_id} (second time)")
        processed_events.add(event_id)
    else:
        logger.info(f"  Event {event_id} already processed, skipping")
    
    logger.info("\n=== Example Complete ===")
    
    return True


async def main():
    """Run the example"""
    try:
        await example_event_flow()
    except Exception as e:
        logger.error(f"Error in example: {e}")
        return False
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)