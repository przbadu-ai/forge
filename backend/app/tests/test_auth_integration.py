"""
Integration tests for auth token lifecycle:
- Full login -> protected call -> refresh -> protected call cycle
- Cookie handling across requests
- Logout session invalidation
- Route protection without credentials
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_full_token_lifecycle(client: AsyncClient) -> None:
    """Login, use access token, refresh, use new token."""
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Verify refresh cookie was set
    cookies = login_resp.headers.get_list("set-cookie")
    assert any("forge_refresh" in c for c in cookies)

    # Extract refresh cookie for explicit use
    refresh_cookie = None
    for c in cookies:
        if "forge_refresh" in c:
            refresh_cookie = c.split("forge_refresh=")[1].split(";")[0]
            break
    assert refresh_cookie is not None

    # 2. Access protected endpoint with access token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin"

    # 3. Refresh token — issues a new access token from the refresh cookie
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"forge_refresh": refresh_cookie},
    )
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    assert new_access_token  # a valid token is returned

    # 4. Use refreshed access token on protected endpoint
    me_resp2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_resp2.status_code == 200
    assert me_resp2.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_logout_invalidates_session(client: AsyncClient) -> None:
    """After logout, refresh cookie is deleted (Max-Age=0) so browser discards it."""
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_resp.status_code == 200

    # Logout
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Verify cookie deletion header is set (Max-Age=0 tells browser to discard)
    set_cookies = logout_resp.headers.get_list("set-cookie")
    assert any(
        "forge_refresh" in c and "Max-Age=0" in c for c in set_cookies
    ), "Logout must clear forge_refresh cookie via Max-Age=0"

    # Without a cookie, refresh returns 401 (simulates browser after cookie cleared)
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient) -> None:
    """All protected routes return 401 when no Bearer token provided."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_malformed_token(client: AsyncClient) -> None:
    """Malformed Bearer token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_cookie(client: AsyncClient) -> None:
    """Refresh endpoint returns 401 when no cookie is present."""
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_correct_user_data(auth_client: AsyncClient) -> None:
    """GET /auth/me returns expected fields and excludes sensitive data."""
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # sensitive field must not be exposed
