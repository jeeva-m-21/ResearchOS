"""Tests for hybrid search endpoint (vector + BM25)."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"


@pytest.mark.asyncio
async def test_search_returns_results():
    """Search with 'transformer' should return the transformer node."""
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

        # ── 2. Search for 'transformer' ───────────────────────────────
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "transformer",
                "organization_id": TEST_ORG_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200, (
            f"Search failed: {search_resp.status_code} - {search_resp.text}"
        )

        data = search_resp.json()
        assert "results" in data, f"Missing 'results' key: {data}"
        assert len(data["results"]) > 0, "Expected at least one search result"
        assert "total" in data
        assert "query" in data
        assert data["query"] == "transformer"
        assert "took_ms" in data

        # The most relevant result for "transformer" should be the
        # node titled "transformer"
        first = data["results"][0]
        assert first["title"] == "transformer", (
            f"Expected 'transformer' as first result, got '{first['title']}'"
        )
        assert first["node_type"] == "idea"
        assert "id" in first


@pytest.mark.asyncio
async def test_search_with_type_filter():
    """Search with type filter should only return matching node types."""
    async with httpx.AsyncClient() as client:
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

        # Search for "learning" but only in "hypothesis" type
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "learning",
                "organization_id": TEST_ORG_ID,
                "types": ["hypothesis"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200, (
            f"Search failed: {search_resp.status_code} - {search_resp.text}"
        )

        data = search_resp.json()
        # All results should be of type "hypothesis"
        for result in data["results"]:
            assert result["node_type"] == "hypothesis", (
                f"Expected 'hypothesis' type, got '{result['node_type']}'"
            )


@pytest.mark.asyncio
async def test_search_pagination():
    """Search pagination (limit + offset) should work correctly."""
    async with httpx.AsyncClient() as client:
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

        # Full results
        full_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "learning",
                "organization_id": TEST_ORG_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert full_resp.status_code == 200
        full_data = full_resp.json()
        full_total = full_data["total"]

        # First page with limit=3
        page1_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "learning",
                "organization_id": TEST_ORG_ID,
                "limit": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert page1_resp.status_code == 200
        page1_data = page1_resp.json()
        assert len(page1_data["results"]) <= 3
        assert page1_data["total"] == full_total

        # Page 2 with offset=3
        page2_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "learning",
                "organization_id": TEST_ORG_ID,
                "limit": 3,
                "offset": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert page2_resp.status_code == 200
        page2_data = page2_resp.json()

        # Verify pages don't overlap
        page1_ids = {r["id"] for r in page1_data["results"]}
        page2_ids = {r["id"] for r in page2_data["results"]}
        assert page1_ids.isdisjoint(page2_ids), (
            "Page 1 and Page 2 should not overlap"
        )


@pytest.mark.asyncio
async def test_search_empty_query_rejected():
    """Empty query should return 422."""
    async with httpx.AsyncClient() as client:
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

        resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={
                "q": "",
                "organization_id": TEST_ORG_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for empty query, got {resp.status_code}: {resp.text}"
        )


@pytest.mark.asyncio
async def test_suggestions():
    """Suggestions should return matching titles based on trigram similarity."""
    async with httpx.AsyncClient() as client:
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

        resp = await client.get(
            f"{BASE_URL}/v1/search/suggestions",
            params={
                "q": "trans",
                "organization_id": TEST_ORG_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"Suggestions failed: {resp.status_code} - {resp.text}"
        )

        titles = resp.json()
        assert isinstance(titles, list), f"Expected list, got {type(titles)}"
        assert len(titles) > 0, "Expected at least one suggestion"
        # Should include "transformer"
        assert "transformer" in titles, (
            f"Expected 'transformer' in suggestions, got {titles}"
        )
