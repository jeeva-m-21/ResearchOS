"""Tests that the EventStore consumer persists events from Redis Stream to PostgreSQL.

The consumer runs as a background task inside the FastAPI lifespan. When the API
emits an event (e.g. ``experiment.started``), the consumer reads it from the
Redis Stream and writes a row to the ``events`` table.

This test:
1. Logs in
2. Creates an experiment (emits ``experiment.started``)
3. Starts a run (emits ``run.started``)
4. Waits for the consumer to catch up
5. Asserts the row appears in PostgreSQL
"""
import asyncio
import os

import asyncpg
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_PROJECT_ID = "90c7cb47-cc1f-472f-99c5-2b17a9e088a8"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://researchos:researchos@researchos-postgres-1:5432/researchos",
)


async def _count_events(conn, event_type: str, after_id: str = "") -> int:
    """Count events of a given type whose payload contains *after_id*."""
    count = await conn.fetchval(
        """
        SELECT count(*) FROM events
        WHERE event_type = $1
          AND payload::text LIKE $2
        """,
        event_type,
        f"%{after_id}%",
    )
    return count or 0


@pytest.mark.asyncio
async def test_event_store_persists_experiment_started():
    """Creating an experiment should result in an events row after consumer
    processes the stream."""
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

        # ── 2. Create experiment (emits experiment.started) ────────────
        exp_resp = await client.post(
            f"{BASE_URL}/v1/experiments/",
            params={
                "name": "EventStore Consumer Test",
                "project_id": TEST_PROJECT_ID,
                "description": "Verify consumer stores events",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert exp_resp.status_code == 200, (
            f"Create experiment failed: {exp_resp.status_code} - {exp_resp.text}"
        )
        exp_data = exp_resp.json()
        experiment_id = exp_data["id"]

        # ── 3. Start a run (emits run.started) ─────────────────────────
        run_resp = await client.post(
            f"{BASE_URL}/v1/experiments/{experiment_id}/runs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert run_resp.status_code == 200, (
            f"Start run failed: {run_resp.status_code} - {run_resp.text}"
        )
        run_data = run_resp.json()
        run_id = run_data["run_id"]

        # ── 4. Wait for consumer to process the stream ────────────────
        # The consumer runs with block_ms=1000 and batch_size=10, so a
        # short sleep is enough for it to pick up the new events.
        await asyncio.sleep(3)

        # ── 5. Query PostgreSQL and assert rows exist ─────────────────
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Check experiment.started
            exp_count = await _count_events(
                conn, "experiment.started", experiment_id
            )
            assert exp_count >= 1, (
                f"No experiment.started event found for experiment {experiment_id}"
            )

            # Check run.started
            run_count = await _count_events(
                conn, "run.started", run_id
            )
            assert run_count >= 1, (
                f"No run.started event found for run {run_id}"
            )

            # Verify payload contains meaningful data
            row = await conn.fetchrow(
                """
                SELECT event_type, organization_id, aggregate_type, version
                FROM events
                WHERE event_type = 'experiment.started'
                AND payload::text LIKE $1
                LIMIT 1
                """,
                f"%{experiment_id}%",
            )
            assert row is not None
            assert row["organization_id"] is not None
            assert row["aggregate_type"] == "Experiment"
            assert row["version"] == 1

        finally:
            await conn.close()
