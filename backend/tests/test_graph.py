"""Tests for graph search and traversal endpoints."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"


@pytest.mark.asyncio
async def test_graph_traverse_outgoing():
    """Traversing outgoing edges from 'transformer' should return related nodes."""
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

        # First get the transformer node ID
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={"q": "transformer", "organization_id": TEST_ORG_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert len(search_data["results"]) > 0
        transformer_id = search_data["results"][0]["id"]

        # Traverse outgoing edges
        traverse_resp = await client.get(
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": transformer_id,
                "organization_id": TEST_ORG_ID,
                "direction": "outgoing",
                "max_depth": 2,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert traverse_resp.status_code == 200, (
            f"Traverse failed: {traverse_resp.status_code} - {traverse_resp.text}"
        )

        data = traverse_resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected at least one traversal result"

        # 'transformer' connects to 'attention mechanism' via 'derives_from' or 'tests'
        titles = [r["target_title"] for r in data]
        assert "attention mechanism" in titles, (
            f"Expected 'attention mechanism' in traversal, got {titles}"
        )
        types = {r["edge_type"] for r in data}
        assert "derives_from" in types or "tests" in types, (
            f"Expected edges of type 'derives_from' or 'tests', got {types}"
        )

        # Verify structure
        item = data[0]
        assert "source_id" in item
        assert "target_id" in item
        assert "edge_id" in item
        assert "edge_type" in item
        assert "direction" in item
        assert "depth" in item
        assert item["direction"] == "outgoing"


@pytest.mark.asyncio
async def test_graph_traverse_incoming():
    """Traversing incoming edges should return nodes that point to the start node."""
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

        # Get 'attention mechanism' node ID
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={"q": "attention mechanism", "organization_id": TEST_ORG_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200
        data = search_resp.json()
        assert len(data["results"]) > 0
        node_id = data["results"][0]["id"]

        # Traverse incoming edges
        traverse_resp = await client.get(
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": node_id,
                "organization_id": TEST_ORG_ID,
                "direction": "incoming",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert traverse_resp.status_code == 200
        results = traverse_resp.json()
        assert len(results) > 0

        # 'attention mechanism' should be targetted by 'transformer'
        titles = [r["source_title"] for r in results]
        assert "transformer" in titles, (
            f"Expected 'transformer' in incoming sources, got {titles}"
        )
        for r in results:
            assert r["direction"] == "incoming"


@pytest.mark.asyncio
async def test_graph_traverse_edge_type_filter():
    """Filtering by edge type should only return edges of that type."""
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

        # Search for 'transformer'
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={"q": "transformer", "organization_id": TEST_ORG_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200
        transformer_id = search_resp.json()["results"][0]["id"]

        # Traverse with edge_type='tests'
        traverse_resp = await client.get(
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": transformer_id,
                "organization_id": TEST_ORG_ID,
                "edge_type": "tests",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert traverse_resp.status_code == 200
        results = traverse_resp.json()
        assert len(results) > 0

        # All results should have edge_type 'tests'
        for r in results:
            assert r["edge_type"] == "tests", (
                f"Expected 'tests' edge type, got '{r['edge_type']}'"
            )


@pytest.mark.asyncio
async def test_graph_traverse_both_directions():
    """Using direction='both' should return edges in both directions."""
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

        # Get 'transformer' node ID
        search_resp = await client.get(
            f"{BASE_URL}/v1/search/",
            params={"q": "transformer", "organization_id": TEST_ORG_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_resp.status_code == 200
        transformer_id = search_resp.json()["results"][0]["id"]

        # Traverse both directions
        traverse_resp = await client.get(
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": transformer_id,
                "organization_id": TEST_ORG_ID,
                "direction": "both",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert traverse_resp.status_code == 200
        results = traverse_resp.json()

        # Should have both outgoing (to attention mechanism) and incoming (from NLP)
        directions = {r["direction"] for r in results}
        assert "outgoing" in directions, "Expected outgoing edges"
        assert "incoming" in directions, "Expected incoming edges"


@pytest.mark.asyncio
async def test_graph_traverse_invalid_direction():
    """Invalid direction should return 422."""
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
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": "00000000-0000-0000-0000-000000000000",
                "organization_id": TEST_ORG_ID,
                "direction": "sideways",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for invalid direction, got {resp.status_code}"
        )


@pytest.mark.asyncio
async def test_graph_traverse_nonexistent_node():
    """Traversing from a non-existent node should return empty results."""
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

        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"{BASE_URL}/v1/graph/traverse",
            params={
                "node_id": fake_id,
                "organization_id": TEST_ORG_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        assert len(results) == 0, (
            f"Expected empty list for non-existent node, got {len(results)} results"
        )
