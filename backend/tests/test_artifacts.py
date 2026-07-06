"""Tests for artifact CRUD endpoints."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_PROJECT_ID = "90c7cb47-cc1f-472f-99c5-2b17a9e088a8"


@pytest.mark.asyncio
async def test_upload_artifact() -> None:
    """Upload a text artifact and verify the response."""
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

        # ── 2. Upload a text file ─────────────────────────────────────
        file_content = b"Hello, world! This is a test artifact."
        files = {"file": ("test_artifact.txt", file_content, "text/plain")}
        upload_resp = await client.post(
            f"{BASE_URL}/v1/artifacts/upload",
            params={"artifact_type": "text"},
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert upload_resp.status_code == 200, (
            f"Upload failed: {upload_resp.status_code} - {upload_resp.text}"
        )

        data = upload_resp.json()
        assert "id" in data, f"Missing 'id' key: {data}"
        assert data["name"] == "test_artifact.txt"
        assert data["artifact_type"] == "text"
        assert data["mime_type"] == "text/plain"
        assert data["size_bytes"] == len(file_content)
        assert data["hash_sha256"] is not None
        assert data["version"] == 1

        # ── 3. List artifacts ─────────────────────────────────────────
        list_resp = await client.get(
            f"{BASE_URL}/v1/artifacts/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, (
            f"List artifacts failed: {list_resp.status_code} - {list_resp.text}"
        )

        artifact_list = list_resp.json()
        assert isinstance(artifact_list, list)
        uploaded_ids = [a["id"] for a in artifact_list]
        assert data["id"] in uploaded_ids, (
            f"Uploaded artifact {data['id']} not found in list"
        )

        # ── 4. Get artifact by ID ─────────────────────────────────────
        get_resp = await client.get(
            f"{BASE_URL}/v1/artifacts/{data['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200, (
            f"Get artifact failed: {get_resp.status_code} - {get_resp.text}"
        )

        artifact = get_resp.json()
        assert artifact["id"] == data["id"]
        assert artifact["name"] == "test_artifact.txt"
        assert artifact["artifact_type"] == "text"
        assert artifact["mime_type"] == "text/plain"
        assert artifact["size_bytes"] == len(file_content)
        assert artifact["hash_sha256"] == data["hash_sha256"]


@pytest.mark.asyncio
async def test_upload_artifact_bad_type() -> None:
    """Verify that invalid artifact types return 422."""
    async with httpx.AsyncClient() as client:
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

        files = {"file": ("test.txt", b"content", "text/plain")}
        upload_resp = await client.post(
            f"{BASE_URL}/v1/artifacts/upload",
            params={"artifact_type": "invalid_type"},
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert upload_resp.status_code == 422, (
            f"Expected 422 for bad type, got {upload_resp.status_code}: "
            f"{upload_resp.text}"
        )


@pytest.mark.asyncio
async def test_get_artifact_not_found() -> None:
    """Verify that requesting a non-existent artifact returns 404."""
    async with httpx.AsyncClient() as client:
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

        fake_id = "00000000-0000-0000-0000-000000000000"
        get_resp = await client.get(
            f"{BASE_URL}/v1/artifacts/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404, (
            f"Expected 404 for missing artifact, got {get_resp.status_code}"
        )
