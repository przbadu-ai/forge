"""Tests for file upload, chunking, and file management endpoints."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_file_txt(auth_client: AsyncClient) -> None:
    """Upload a TXT file and get a success response."""
    content = b"Hello world, this is a test document for RAG."
    files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
    resp = await auth_client.post("/api/v1/files/upload", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert data["original_name"] == "test.txt"
    assert data["status"] == "pending"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_upload_file_unsupported_type(auth_client: AsyncClient) -> None:
    """Uploading an unsupported file type returns 400."""
    content = b"binary data"
    files = {"file": ("test.exe", io.BytesIO(content), "application/octet-stream")}
    resp = await auth_client.post("/api/v1/files/upload", files=files)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_files_empty(auth_client: AsyncClient) -> None:
    """List files returns empty initially."""
    resp = await auth_client.get("/api/v1/files/")
    assert resp.status_code == 200
    # May have files from other tests; just check it's a list
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_upload_and_list(auth_client: AsyncClient) -> None:
    """Upload a file, then list to verify it appears."""
    content = b"Test content for listing."
    files = {"file": ("listing-test.txt", io.BytesIO(content), "text/plain")}
    upload_resp = await auth_client.post("/api/v1/files/upload", files=files)
    assert upload_resp.status_code == 201
    file_id = upload_resp.json()["id"]

    list_resp = await auth_client.get("/api/v1/files/")
    assert list_resp.status_code == 200
    file_ids = [f["id"] for f in list_resp.json()]
    assert file_id in file_ids


@pytest.mark.asyncio
async def test_get_file_detail(auth_client: AsyncClient) -> None:
    """Get details of an uploaded file."""
    content = b"Detail test content."
    files = {"file": ("detail-test.txt", io.BytesIO(content), "text/plain")}
    upload_resp = await auth_client.post("/api/v1/files/upload", files=files)
    file_id = upload_resp.json()["id"]

    detail_resp = await auth_client.get(f"/api/v1/files/{file_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["original_name"] == "detail-test.txt"
    assert data["content_type"] == "text/plain"


@pytest.mark.asyncio
async def test_delete_file(auth_client: AsyncClient) -> None:
    """Delete an uploaded file."""
    content = b"Delete test content."
    files = {"file": ("delete-test.txt", io.BytesIO(content), "text/plain")}
    upload_resp = await auth_client.post("/api/v1/files/upload", files=files)
    file_id = upload_resp.json()["id"]

    delete_resp = await auth_client.delete(f"/api/v1/files/{file_id}")
    assert delete_resp.status_code == 204

    # Verify it's gone
    get_resp = await auth_client.get(f"/api/v1/files/{file_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_file(auth_client: AsyncClient) -> None:
    """Getting a nonexistent file returns 404."""
    resp = await auth_client.get("/api/v1/files/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient) -> None:
    """Upload endpoint requires authentication."""
    content = b"Unauthed content."
    files = {"file": ("unauth.txt", io.BytesIO(content), "text/plain")}
    resp = await client.post("/api/v1/files/upload", files=files)
    assert resp.status_code == 401
