#!/usr/bin/env python3
"""
Test EventProducer decode issue fix.

Tests that EventProducer correctly handles both bytes and string keys
regardless of decode_responses setting.
"""

import asyncio
import json
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any
import redis.asyncio as redis

from src.domain.shared.events import DomainEvent
from src.infrastructure.events.producer import EventProducer


class TestEvent(DomainEvent):
    """Test event for testing"""
    event_type: str = "test.event"
    aggregate_id: UUID
    aggregate_type: str = "Test"
    organization_id: UUID
    version: int = 1
    metadata: Dict[str, Any] = {}
    created_by: UUID


async def test_decode_with_decode_responses_false():
    """Test with decode_responses=False (default)"""
    print("Testing with decode_responses=False...")
    
    # Create Redis client with decode_responses=False
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=False  # Default setting
    )
    
    producer = EventProducer(redis_client)
    
    # Create test event
    org_id = uuid4()
    event = TestEvent(
        aggregate_id=uuid4(),
        organization_id=org_id,
        created_by=uuid4()
    )
    
    try:
        # Test emit
        stream_id = await producer.emit(event)
        print(f"  ✓ Event emitted successfully: {stream_id}")
        
        # Test get_stream_info
        info = await producer.get_stream_info(org_id)
        print(f"  ✓ Stream info retrieved: {info}")
        
        # Verify info contains string keys
        assert isinstance(info, dict), "Info should be a dict"
        assert all(isinstance(k, str) for k in info.keys()), "All keys should be strings"
        
        print("  ✓ All keys are strings (not bytes)")
        
        # Clean up
        await redis_client.delete(f"events:org_{org_id}")
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        raise
    finally:
        await redis_client.close()


async def test_decode_with_decode_responses_true():
    """Test with decode_responses=True"""
    print("Testing with decode_responses=True...")
    
    # Create Redis client with decode_responses=True
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True  # Strings instead of bytes
    )
    
    producer = EventProducer(redis_client)
    
    # Create test event
    org_id = uuid4()
    event = TestEvent(
        aggregate_id=uuid4(),
        organization_id=org_id,
        created_by=uuid4()
    )
    
    try:
        # Test emit
        stream_id = await producer.emit(event)
        print(f"  ✓ Event emitted successfully: {stream_id}")
        
        # Test get_stream_info
        info = await producer.get_stream_info(org_id)
        print(f"  ✓ Stream info retrieved: {info}")
        
        # Verify info contains string keys
        assert isinstance(info, dict), "Info should be a dict"
        assert all(isinstance(k, str) for k in info.keys()), "All keys should be strings"
        
        print("  ✓ All keys are strings")
        
        # Clean up
        await redis_client.delete(f"events:org_{org_id}")
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        raise
    finally:
        await redis_client.close()


async def test_batch_emit():
    """Test batch emit with decode handling"""
    print("Testing batch emit...")
    
    # Create Redis client
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=False  # Test with bytes
    )
    
    producer = EventProducer(redis_client)
    
    # Create test events
    org_id = uuid4()
    events = [
        TestEvent(
            aggregate_id=uuid4(),
            organization_id=org_id,
            created_by=uuid4()
        )
        for _ in range(3)
    ]
    
    try:
        # Test batch emit
        stream_ids = await producer.emit_batch(events)
        print(f"  ✓ Batch emitted successfully: {len(stream_ids)} events")
        
        # Verify all stream IDs are strings
        assert all(isinstance(sid, str) for sid in stream_ids), "All stream IDs should be strings"
        print("  ✓ All stream IDs are strings")
        
        # Test get_stream_info
        info = await producer.get_stream_info(org_id)
        print(f"  ✓ Stream info retrieved: length={info.get('length', 0)}")
        
        # Clean up
        await redis_client.delete(f"events:org_{org_id}")
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        raise
    finally:
        await redis_client.close()


async def test_health_check():
    """Test health check method"""
    print("Testing health check...")
    
    # Create Redis client
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=False
    )
    
    producer = EventProducer(redis_client)
    
    try:
        # Test health check
        health = await producer.health_check()
        print(f"  ✓ Health check: {health}")
        
        assert health["status"] in ["healthy", "unhealthy"], "Status should be healthy or unhealthy"
        print("  ✓ Health check status valid")
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        raise
    finally:
        await redis_client.close()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing EventProducer decode issue fix")
    print("=" * 60)
    
    tests = [
        test_decode_with_decode_responses_false,
        test_decode_with_decode_responses_true,
        test_batch_emit,
        test_health_check,
    ]
    
    for test_func in tests:
        try:
            await test_func()
            print()
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} failed: {e}")
            return 1
    
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    # Note: This test requires Redis to be running
    # You can run it with: python -m pytest test_event_producer_decode.py -v
    # Or directly: python test_event_producer_decode.py
    
    print("Note: This test requires Redis to be running on localhost:6379")
    print("Run with: make docker-up (to start Redis)")
    print()
    
    exit_code = asyncio.run(main())
    exit(exit_code)