"""Tests for DLQ retry and consumer health endpoints"""
import json
import os
from uuid import uuid4

import httpx
import pytest
from redis.asyncio import Redis

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"

REDIS_URL = os.getenv("REDIS_URL", "redis://researchos-redis-1:6379/0")


@pytest.mark.asyncio
async def test_dlq_retry_moves_events_back_to_stream() -> None:
    """DLQ retry endpoint should move failed events back to main stream"""
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

        # 2. Add test entry to DLQ stream
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        dlq_key = "dlq:projectors"
        test_event_id = str(uuid4())
        dlq_msg_id = None

        try:
            dlq_msg_id = await redis_client.xadd(dlq_key, {
                "event_id": test_event_id,
                "event_type": "experiment.started",
                "payload": json.dumps({
                    "event_id": test_event_id,
                    "event_type": "experiment.started",
                    "organization_id": TEST_ORG_ID,
                }),
                "error": "Test error for DLQ retry",
                "consumer_group": "projectors",
                "failed_at": "2026-07-04T00:00:00",
                "retry_count": "3",
                "original_message_id": "0-0",
                "additional_info": "{}",
            }, maxlen=10000)

            # 3. Call retry endpoint
            retry_resp = await client.post(
                f"{BASE_URL}/v1/events/dlq/projectors/retry?limit=10",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert retry_resp.status_code == 200, (
                f"Retry failed: {retry_resp.status_code} - {retry_resp.text}"
            )
            data = retry_resp.json()

            # 4. Verify response shows successful retry
            assert data["status"] == "completed"
            assert data["consumer_group"] == "projectors"
            assert data["attempted"] >= 1, (
                f"Expected at least 1 attempt, got {data['attempted']}"
            )
            assert data["successful"] >= 1, (
                f"Expected at least 1 success, got {data['successful']}"
            )

        finally:
            # 5. Clean up: remove DLQ entry and retried event from main stream
            if dlq_msg_id:
                await redis_client.xdel(dlq_key, dlq_msg_id)
            main_stream = f"events:org_{TEST_ORG_ID}"
            main_events = await redis_client.xrange(main_stream, "-", "+")
            for msg_id, fields in main_events:
                if fields.get("event_id") == test_event_id:
                    await redis_client.xdel(main_stream, msg_id)
                    break
            await redis_client.aclose()


@pytest.mark.asyncio
async def test_consumer_health_endpoint() -> None:
    """Consumer health endpoint should return proper health data"""
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

        # 2. Call consumer health endpoint
        health_resp = await client.get(
            f"{BASE_URL}/v1/events/consumers/projectors/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert health_resp.status_code == 200, (
            f"Health check failed: {health_resp.status_code} - {health_resp.text}"
        )
        data = health_resp.json()

        # 3. Verify expected keys (always present regardless of health status)
        assert "status" in data, f"Missing 'status' key: {data}"
        assert "consumer_group" in data, f"Missing 'consumer_group' key: {data}"
        assert data["consumer_group"] == "projectors"

        # Structural keys present when healthy
        if data["status"] == "healthy":
            assert "running" in data
            assert "redis" in data
            assert data["redis"] == "connected"
            assert "metrics" in data
            assert isinstance(data["metrics"], dict)
            has_lag = (
                "consumer_lag_seconds" in data.get("metrics", {})
                or "consumer_lag_seconds" in data
            )
            assert has_lag, "Expected consumer lag metric"
        else:
            # Even when not found, status should be a known value
            assert data["status"] in ("healthy", "not_found", "unhealthy", "degraded")
