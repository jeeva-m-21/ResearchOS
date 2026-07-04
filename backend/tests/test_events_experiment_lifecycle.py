"""Tests that experiment lifecycle emits events correctly"""
import os

import httpx
import pytest
from redis.asyncio import Redis

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_PROJECT_ID = "90c7cb47-cc1f-472f-99c5-2b17a9e088a8"

# Use the same REDIS_URL as the backend (set in docker-compose.yml env)
REDIS_URL = os.getenv("REDIS_URL", "redis://researchos-redis-1:6379/0")


@pytest.mark.asyncio
async def test_experiment_lifecycle_emits_events():
    """Creating experiment → run → metric should emit events to Redis Stream"""
    async with httpx.AsyncClient() as client:
        # ── 1. Login ──────────────────────────────────────────────────
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

        # ── 2. Create experiment ──────────────────────────────────────
        exp_resp = await client.post(
            f"{BASE_URL}/v1/experiments/",
            params={
                "name": "Test Event Lifecycle",
                "project_id": TEST_PROJECT_ID,
                "description": "Verifying event emission",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert exp_resp.status_code == 200, (
            f"Create experiment failed: {exp_resp.status_code} - {exp_resp.text}"
        )
        exp_data = exp_resp.json()
        experiment_id = exp_data["id"]

        # ── 3. Start a run ────────────────────────────────────────────
        run_resp = await client.post(
            f"{BASE_URL}/v1/experiments/{experiment_id}/runs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert run_resp.status_code == 200, (
            f"Start run failed: {run_resp.status_code} - {run_resp.text}"
        )
        run_data = run_resp.json()
        run_id = run_data["run_id"]

        # ── 4. Log a metric ───────────────────────────────────────────
        metric_resp = await client.post(
            f"{BASE_URL}/v1/experiments/{experiment_id}/runs/{run_id}/metrics",
            params={"key": "accuracy", "value": 0.95, "step": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert metric_resp.status_code == 200, (
            f"Log metric failed: {metric_resp.status_code} - {metric_resp.text}"
        )

        # ── 5. Read Redis Stream and verify events ────────────────────
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        stream_key = f"events:org_{TEST_ORG_ID}"

        try:
            # Read all events from the stream
            events = await redis_client.xrange(stream_key, "-", "+")

            # Collect event types
            event_types = []
            for _msg_id, fields in events:
                event_type = fields.get("event_type", "")
                event_types.append(event_type)

            # Assert required event types are present
            assert "experiment.started" in event_types, (
                f"Missing experiment.started event. Found: {event_types}"
            )
            assert "run.started" in event_types, (
                f"Missing run.started event. Found: {event_types}"
            )
            assert "metric.logged" in event_types, (
                f"Missing metric.logged event. Found: {event_types}"
            )

            # Verify event order (create → run → metric)
            exp_idx = event_types.index("experiment.started")
            run_idx = event_types.index("run.started")
            metric_idx = event_types.index("metric.logged")
            assert exp_idx < run_idx, (
                "experiment.started should come before run.started"
            )
            assert run_idx < metric_idx, (
                "run.started should come before metric.logged"
            )

        finally:
            await redis_client.aclose()


@pytest.mark.asyncio
async def test_experiment_starts_events():
    """Each experiment created should have its own experiment.started event"""
    async with httpx.AsyncClient() as client:
        # Login
        login_resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Create experiment
        exp_resp = await client.post(
            f"{BASE_URL}/v1/experiments/",
            params={
                "name": "Second Test Event",
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert exp_resp.status_code == 200
        exp_data = exp_resp.json()
        assert "id" in exp_data

        # Check Redis has experiment.started
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        stream_key = f"events:org_{TEST_ORG_ID}"

        try:
            events = await redis_client.xrange(stream_key, "-", "+")
            event_types = [
                fields.get("event_type", "")
                for _msg_id, fields in events
            ]
            assert "experiment.started" in event_types, (
                "Expected at least one experiment.started event"
            )

            # Verify at least one experiment.started event
            # references the newly created experiment
            found = False
            for _msg_id, fields in events:
                if fields.get("event_type") == "experiment.started":
                    payload = fields.get("payload", "")
                    if exp_data["id"] in payload:
                        found = True
                        break
            assert found, (
                "No experiment.started event found referencing "
                f"created experiment {exp_data['id']}"
            )

        finally:
            await redis_client.aclose()
