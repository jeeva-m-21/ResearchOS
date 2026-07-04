"""Tests for auth API key endpoints"""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"


@pytest.mark.asyncio
async def test_auth_api_keys_post_creates_key():
    """Test that POST /auth/api-keys creates a valid API key"""
    async with httpx.AsyncClient() as client:
        # 1. Login to get JWT token
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

        # 2. Create a new API key
        api_key_resp = await client.post(
            f"{BASE_URL}/auth/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Key - Pytest"},
        )
        assert api_key_resp.status_code == 200, (
            f"POST /auth/api-keys failed:"
            f" {api_key_resp.status_code} - {api_key_resp.text}"
        )
        data = api_key_resp.json()

        # 3. Validate response shape
        assert "key" in data, "Response missing 'key'"
        assert "id" in data, "Response missing 'id'"
        assert "name" in data, "Response missing 'name'"
        assert "organization_id" in data, "Response missing 'organization_id'"

        # 4. Key should start with expected prefix
        assert data["key"].startswith("rok_"), (
            f"API key does not start with 'rok_': {data['key'][:20]}..."
        )

        # 5. Name matches request
        assert data["name"] == "Test Key - Pytest"


@pytest.mark.asyncio
async def test_auth_api_keys_requires_auth():
    """Test that POST /auth/api-keys rejects requests without valid auth"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/auth/api-keys",
            json={"name": "Unauthenticated Key"},
        )
        # Returns 401 or 403 depending on middleware handling
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 for unauthenticated request, got {resp.status_code}"
        )
