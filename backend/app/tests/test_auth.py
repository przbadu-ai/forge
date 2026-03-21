import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "changeme"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Check refresh cookie was set
    cookies = resp.headers.get_list("set-cookie")
    assert any("forge_refresh" in c for c in cookies)


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": "nobody", "password": "changeme"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient) -> None:
    # Login first to get refresh cookie
    login_resp = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "changeme"}
    )
    assert login_resp.status_code == 200

    # Extract refresh cookie from response
    cookies = login_resp.headers.get_list("set-cookie")
    refresh_cookie = None
    for c in cookies:
        if "forge_refresh" in c:
            # Parse cookie value
            refresh_cookie = c.split("forge_refresh=")[1].split(";")[0]
            break
    assert refresh_cookie is not None

    # Use refresh cookie
    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"forge_refresh": refresh_cookie},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    # Login first
    await client.post("/api/v1/auth/login", json={"username": "admin", "password": "changeme"})
    # Logout
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"
    # Check cookie is cleared (max-age=0)
    cookies = resp.headers.get_list("set-cookie")
    assert any("forge_refresh" in c and "Max-Age=0" in c for c in cookies)


@pytest.mark.asyncio
async def test_me_authenticated(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_authenticated(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
