"""Tests for POST /auth/logout endpoint"""
from typing import Any

import httpx
import pytest

BASE_URL = "http://backend:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
LOGOUT_URL = f"{BASE_URL}/auth/logout"


@pytest.fixture(scope="module")
def auth_token() -> dict[str, Any]:
    """Obtain a valid JWT token pair for testing"""
    with httpx.Client() as client:
        resp = client.post(
            LOGIN_URL,
            json={
                "email": "researcher@test.com",
                "password": "password123",
                "organization_id": "02b5991b-d971-41fc-b257-4ded07d94aac",
            },
        )
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        return dict(resp.json())


def test_logout_with_refresh_token(auth_token: dict[str, Any]) -> None:
    """Logout with valid refresh_token in body should return 200"""
    refresh_token = auth_token["refresh_token"]
    with httpx.Client() as client:
        resp = client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        data = resp.json()
        assert "message" in data
        assert data["message"] == "Logged out successfully"


def test_logout_missing_body() -> None:
    """Logout without body should return 422 validation error"""
    with httpx.Client() as client:
        resp = client.post(LOGOUT_URL)  # no body
        assert resp.status_code == 422, (
            f"Expected 422, got {resp.status_code}: {resp.text}"
        )


def test_logout_missing_refresh_token(auth_token: dict[str, Any]) -> None:
    """Logout without refresh_token field should return 422"""
    with httpx.Client() as client:
        resp = client.post(LOGOUT_URL, json={})  # empty body
        assert resp.status_code == 422, (
            f"Expected 422, got {resp.status_code}: {resp.text}"
        )
