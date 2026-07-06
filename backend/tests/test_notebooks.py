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


# ── Block Execution tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_python_block() -> None:
    """Create a notebook with a Python block, execute it, verify success & output."""
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
            params={"title": "Exec Test NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create a Python block ───────────────────────────────────
        block_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={
                "block_type": "python",
                "content": "print('hello world')",
                "language": "python",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert block_resp.status_code == 200, (
            f"Create block failed: {block_resp.status_code} - {block_resp.text}"
        )
        block_id = block_resp.json()["id"]

        # ── 4. Execute the block ───────────────────────────────────────
        exec_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/execute",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert exec_resp.status_code == 200, (
            f"Execute block failed: {exec_resp.status_code} - {exec_resp.text}"
        )

        exec_data = exec_resp.json()
        assert "execution_id" in exec_data
        assert exec_data["status"] == "success", (
            f"Expected success, got {exec_data['status']}: {exec_data}"
        )
        assert exec_data["output"] is not None
        assert "hello world" in exec_data["output"]
        assert "duration_ms" in exec_data

        # ── 5. List executions ────────────────────────────────────────
        list_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/executions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, (
            f"List executions failed: {list_resp.status_code} - {list_resp.text}"
        )

        exec_list = list_resp.json()
        assert isinstance(exec_list, list), f"Expected list, got {type(exec_list)}"
        assert len(exec_list) >= 1

        found = any(e["id"] == exec_data["execution_id"] for e in exec_list)
        assert found, (
            f"Execution {exec_data['execution_id']} not found in list: {exec_list}"
        )


@pytest.mark.asyncio
async def test_execute_block_bad_type() -> None:
    """Verify that non-executable block types return 400."""
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
            params={"title": "Exec BadType NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create a markdown block (non-executable) ────────────────
        block_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={"block_type": "markdown", "content": "Just text"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert block_resp.status_code == 200
        block_id = block_resp.json()["id"]

        # ── 4. Try to execute markdown ─────────────────────────────────
        exec_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/execute",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert exec_resp.status_code == 400, (
            f"Expected 400 for markdown, got {exec_resp.status_code}: "
            f"{exec_resp.text}"
        )


# ── Block Update/Delete tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_block() -> None:
    """Create a block, update its content, verify version increments."""
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
            params={"title": "Update Block NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create a python block ──────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={
                "block_type": "python",
                "content": "print('v1')",
                "language": "python",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        block_id = create_resp.json()["id"]
        assert create_resp.json()["current_version"] == 1

        # ── 4. Update the block content ───────────────────────────────
        update_resp = await client.put(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            json={
                "content": "print('v2')",
                "language": "python",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200, (
            f"Update block failed: {update_resp.status_code} - {update_resp.text}"
        )

        data = update_resp.json()
        assert data["content"] == "print('v2')"
        assert data["language"] == "python"
        assert data["current_version"] == 2, (
            f"Expected version 2, got {data['current_version']}"
        )
        assert data["content_version"] == 2

        # ── 5. Verify by GET-ing the block ────────────────────────────
        get_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["content"] == "print('v2')"
        assert get_resp.json()["content_version"] == 2


@pytest.mark.asyncio
async def test_delete_block() -> None:
    """Create a block, delete it, verify 404 on subsequent GET."""
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
            params={"title": "Delete Block NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create a block ─────────────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={
                "block_type": "markdown",
                "content": "To be deleted",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        block_id = create_resp.json()["id"]

        # ── 4. Delete the block ───────────────────────────────────────
        del_resp = await client.delete(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_resp.status_code == 200, (
            f"Delete block failed: {del_resp.status_code} - {del_resp.text}"
        )
        assert del_resp.json() == {"status": "deleted", "id": block_id}

        # ── 5. Verify GET returns 404 (soft delete) ───────────────────
        get_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404, (
            f"Expected 404 for deleted block, got {get_resp.status_code}: "
            f"{get_resp.text}"
        )


# ── Block History / Diff tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_block_history() -> None:
    """Create a block, update it, then verify history lists both versions."""
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
            params={"title": "History Test NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create block ───────────────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={"block_type": "markdown", "content": "Version 1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        block_id = create_resp.json()["id"]

        # ── 4. Update block to create version 2 ───────────────────────
        update_resp = await client.put(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            json={"content": "Version 2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["current_version"] == 2

        # ── 5. Get history ────────────────────────────────────────────
        hist_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert hist_resp.status_code == 200, (
            f"History failed: {hist_resp.status_code} - {hist_resp.text}"
        )

        entries = hist_resp.json()
        assert isinstance(entries, list)
        assert len(entries) >= 2, f"Expected >=2 history entries, got {len(entries)}"

        # Newest first (version 2, then version 1)
        assert entries[0]["version"] == 2, (
            f"Expected v2 first, got v{entries[0]['version']}"
        )
        assert entries[0]["content"] == "Version 2"
        assert entries[1]["version"] == 1
        assert entries[1]["content"] == "Version 1"

        # Check metadata present
        assert "created_at" in entries[0]
        assert "created_by" in entries[0]


@pytest.mark.asyncio
async def test_block_diff() -> None:
    """Create a block, update it, then diff v1 vs v2."""
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
            params={"title": "Diff Test NB", "project_id": TEST_PROJECT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert nb_resp.status_code == 200
        notebook_id = nb_resp.json()["id"]

        # ── 3. Create block ───────────────────────────────────────────
        create_resp = await client.post(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks",
            json={"block_type": "python", "content": "print('old')"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        block_id = create_resp.json()["id"]

        # ── 4. Update block ───────────────────────────────────────────
        await client.put(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}",
            json={"content": "print('new')"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # ── 5. Diff v1 vs v2 ──────────────────────────────────────────
        diff_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/diff",
            params={"v1": 1, "v2": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert diff_resp.status_code == 200, (
            f"Diff failed: {diff_resp.status_code} - {diff_resp.text}"
        )

        data = diff_resp.json()
        assert data["v1"] == 1
        assert data["v2"] == 2
        assert "diff" in data
        diff_lines = data["diff"]
        assert isinstance(diff_lines, list)

        # Should show removal of old and addition of new
        combined = "\n".join(diff_lines)
        assert "-print('old')" in combined, (
            f"Expected removal of old content in diff: {combined}"
        )
        assert "+print('new')" in combined, (
            f"Expected addition of new content in diff: {combined}"
        )

        # ── 6. Diff invalid version returns 404 ───────────────────────
        bad_resp = await client.get(
            f"{BASE_URL}/v1/notebooks/{notebook_id}/blocks/{block_id}/diff",
            params={"v1": 1, "v2": 999},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bad_resp.status_code == 404, (
            f"Expected 404 for bad version, got {bad_resp.status_code}"
        )
