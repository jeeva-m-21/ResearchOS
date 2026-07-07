"""Tests for the Papers feature — CRUD, compile endpoint, and latex_content."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_PROJECT_ID = "90c7cb47-cc1f-472f-99c5-2b17a9e088a8"


@pytest.fixture(scope="module")
def token():
    """Get auth token for the test researcher."""
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_paper_with_latex(token):
    """A paper can be created with latex_content."""
    async with httpx.AsyncClient() as client:
        latex = (
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\title{Test Paper}\n"
            "\\maketitle\n"
            "Hello world.\n"
            "\\end{document}"
        )
        resp = await client.post(
            f"{BASE_URL}/v1/papers/",
            params={
                "title": "LaTeX Test Paper",
                "project_id": TEST_PROJECT_ID,
                "latex_content": latex,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["title"] == "LaTeX Test Paper"
        assert data["status"] == "draft"
        return data["id"]


@pytest.mark.asyncio
async def test_get_paper_returns_latex(token):
    """Get paper should include latex_content."""
    async with httpx.AsyncClient() as client:
        # First create one
        create_resp = await client.post(
            f"{BASE_URL}/v1/papers/",
            params={
                "title": "Get LaTeX Test",
                "project_id": TEST_PROJECT_ID,
                "latex_content": "\\section{Test}",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        paper_id = create_resp.json()["id"]

        # Now fetch it
        resp = await client.get(
            f"{BASE_URL}/v1/papers/{paper_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "latex_content" in data
        assert data["latex_content"] == "\\section{Test}"


@pytest.mark.asyncio
async def test_update_paper_latex(token):
    """Updating a paper should store new latex_content."""
    async with httpx.AsyncClient() as client:
        create_resp = await client.post(
            f"{BASE_URL}/v1/papers/",
            params={
                "title": "Update LaTeX Test",
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        paper_id = create_resp.json()["id"]

        # Update with latex
        update_resp = await client.patch(
            f"{BASE_URL}/v1/papers/{paper_id}",
            params={
                "latex_content": "\\section{Updated}",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["latex_content"] == "\\section{Updated}"


@pytest.mark.asyncio
async def test_compile_empty_latex_returns_error(token):
    """Compile endpoint should return an error when paper has no LaTeX content."""
    async with httpx.AsyncClient() as client:
        create_resp = await client.post(
            f"{BASE_URL}/v1/papers/",
            params={
                "title": "Empty LaTeX Paper",
                "project_id": TEST_PROJECT_ID,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        paper_id = create_resp.json()["id"]

        resp = await client.post(
            f"{BASE_URL}/v1/papers/{paper_id}/compile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "no latex content" in data["message"].lower()


@pytest.mark.asyncio
async def test_compile_with_latex_content(token):
    """Compile endpoint should return unavailable or success with latex_content."""
    async with httpx.AsyncClient() as client:
        create_resp = await client.post(
            f"{BASE_URL}/v1/papers/",
            params={
                "title": "Compilable Paper",
                "project_id": TEST_PROJECT_ID,
                "latex_content": (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "Hello\n"
                    "\\end{document}"
                ),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        paper_id = create_resp.json()["id"]

        resp = await client.post(
            f"{BASE_URL}/v1/papers/{paper_id}/compile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Either unavailable (pdflatex not installed) or success
        assert data["status"] in ("unavailable", "success")
        if data["status"] == "success":
            assert "pdf_base64" in data
