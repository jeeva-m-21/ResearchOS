"""Tests for notebook CRUD endpoints."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_PROJECT_ID = "90c7cb47-cc1f-472f-99c5-2b17a9e088a8"


@pytest.mark.asyncio
async def test_create_notebook() -> None:
    """Create a notebook and verify the response shape."""
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

        # ── 2. Create notebook ────────────────────────────────────────
        resp = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={
                "title": "My Test Notebook",
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"Create notebook failed: {resp.status_code} - {resp.text}"
        )

        data = resp.json()
        assert "id" in data, f"Missing 'id' key: {data}"
        assert data["title"] == "My Test Notebook"
        assert data["project_id"] == TEST_PROJECT_ID


@pytest.mark.asyncio
async def test_get_notebook() -> None:
    """Create a notebook, then GET it by id, verify all fields."""
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

        # ── 2. Create notebook ────────────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={
                "title": "Notebook for Get Test",
                "project_id": TEST_PROJECT_ID,
                "description": "Test description",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        notebook_id = create_resp.json()["id"]

        # ── 3. Get notebook by id ─────────────────────────────────────
        get_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200, (
            f"Get notebook failed: {get_resp.status_code} - {get_resp.text}"
        )

        data = get_resp.json()
        assert data["id"] == notebook_id
        assert data["title"] == "Notebook for Get Test"
        assert data["description"] == "Test description"
        assert data["project_id"] == TEST_PROJECT_ID
        assert "branch" in data
        assert "created_at" in data
        assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_notebooks() -> None:
    """Create 2 notebooks, then GET /v1/notebooks/ and verify both appear."""
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

        # ── 2. Create two notebooks ───────────────────────────────────
        title_a = "List Test Notebook Alpha"
        title_b = "List Test Notebook Beta"

        resp_a = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={
                "title": title_a,
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_a.status_code == 200

        resp_b = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={
                "title": title_b,
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_b.status_code == 200

        # ── 3. List notebooks ─────────────────────────────────────────
        list_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/",
            params={
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, (
            f"List notebooks failed: {list_resp.status_code} - {list_resp.text}"
        )

        data = list_resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"

        titles = [nb["title"] for nb in data]
        assert title_a in titles, (
            f"Expected '{title_a}' in list, got {titles}"
        )
        assert title_b in titles, (
            f"Expected '{title_b}' in list, got {titles}"
        )


# ── Block CRUD tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_block() -> None:
    """Create a notebook, then add a block and verify the response."""
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

        # ── 2. Create notebook ────────────────────────────────────────
        nb_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={"title": "Block Test NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create a markdown block ─────────────────────────────────
        resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={
                "block_type": "markdown",
                "content": "## Hello\nThis is a test block.",
                "language": None,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"Create block failed: {resp.status_code} - {resp.text}"
        )

        data = resp.json()
        assert data["block_type"] == "markdown"
        assert data["content"] == "## Hello\nThis is a test block."
        assert data["position"] == 0
        assert data["current_version"] == 1
        assert data["notebook_id"] == notebook_id


@pytest.mark.asyncio
async def test_list_blocks() -> None:
    """Create a notebook with 2 blocks, then list them."""
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

        # ── 2. Create notebook ────────────────────────────────────────
        nb_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={"title": "Block List NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create block A ─────────────────────────────────────────
        resp_a = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={"block_type": "markdown", "content": "Block A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_a.status_code == 200

        # ── 4. Create block B ─────────────────────────────────────────
        resp_b = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={
                "block_type": "python",
                "content": "print('hello')",
                "language": "python",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_b.status_code == 200

        # ── 5. List blocks ────────────────────────────────────────────
        list_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, (
            f"List blocks failed: {list_resp.status_code} - {list_resp.text}"
        )

        data = list_resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) >= 2

        # Blocks ordered by position
        types = [b["block_type"] for b in data[:2]]
        assert "markdown" in types
        assert "python" in types


@pytest.mark.asyncio
async def test_get_block() -> None:
    """Create a block, then GET it by id and verify fields."""
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

        # ── 2. Create notebook ────────────────────────────────────────
        nb_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/",
            params={"title": "Block Get NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create block ───────────────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={"block_type": "latex", "content": r"E = mc^2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        block_id = create_resp.json()["id"]

        # ── 4. Get block by id ────────────────────────────────────────
        get_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200, (
            f"Get block failed: {get_resp.status_code} - {get_resp.text}"
        )

        data = get_resp.json()
        assert data["id"] == block_id
        assert data["block_type"] == "latex"
        assert data["content"] == r"E = mc^2"
        assert data["position"] == 0
        assert "created_at" in data
