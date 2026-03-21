"""File upload and management API endpoints."""

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import AsyncSessionFactory, get_session
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.file_service import delete_file, process_file, upload_file

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class FileRead(BaseModel):
    id: int
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    status: str
    chunk_count: int
    user_id: int
    created_at: datetime


class FileUploadResponse(BaseModel):
    id: int
    original_name: str
    status: str
    message: str


# ---------- Helpers ----------


def _file_to_read(f: UploadedFile) -> FileRead:
    return FileRead(
        id=f.id,
        filename=f.filename,
        original_name=f.original_name,
        content_type=f.content_type,
        size_bytes=f.size_bytes,
        status=f.status,
        chunk_count=f.chunk_count,
        user_id=f.user_id,
        created_at=f.created_at,
    )


async def _process_file_background(file_id: int) -> None:
    """Process file in background task with its own session."""
    async with AsyncSessionFactory() as session:
        await process_file(file_id, session)


# ---------- Endpoints ----------


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FileUploadResponse:
    """Upload a file for RAG processing."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    try:
        uploaded = await upload_file(
            file_data=file.file,
            original_name=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=current_user.id,  # type: ignore[arg-type]
            session=session,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    # Trigger async processing in background
    asyncio.create_task(_process_file_background(uploaded.id))  # type: ignore[arg-type]

    return FileUploadResponse(
        id=uploaded.id,
        original_name=uploaded.original_name,
        status=uploaded.status,
        message="File uploaded. Processing started.",
    )


@router.get("/", response_model=list[FileRead])
async def list_files(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FileRead]:
    """List all files for the current user."""
    result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.user_id == current_user.id)  # type: ignore[arg-type]
        .order_by(UploadedFile.created_at.desc())  # type: ignore[attr-defined]
    )
    files = result.scalars().all()
    return [_file_to_read(f) for f in files]


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FileRead:
    """Get details of a specific file."""
    result = await session.execute(
        select(UploadedFile).where(
            UploadedFile.id == file_id,  # type: ignore[arg-type]
            UploadedFile.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    uploaded = result.scalars().first()
    if uploaded is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return _file_to_read(uploaded)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    file_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a file and its associated ChromaDB documents."""
    # Verify ownership
    result = await session.execute(
        select(UploadedFile).where(
            UploadedFile.id == file_id,  # type: ignore[arg-type]
            UploadedFile.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    uploaded = result.scalars().first()
    if uploaded is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    deleted = await delete_file(file_id, session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )
