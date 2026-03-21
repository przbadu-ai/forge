"""File service — upload, parse, chunk, embed, and store documents."""

import logging
import os
import uuid
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chroma_client import add_documents, delete_file_documents
from app.models.settings import AppSettings
from app.models.uploaded_file import UploadedFile
from app.services.embedding_service import embed_texts

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def upload_file(
    file_data: BinaryIO,
    original_name: str,
    content_type: str,
    user_id: int,
    session: AsyncSession,
) -> UploadedFile:
    """Save uploaded file to disk and create a DB record."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Validate extension
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Generate unique filename
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / stored_name

    # Write file to disk
    contents = file_data.read()
    size_bytes = len(contents)

    if size_bytes > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size_bytes} bytes. Max: {MAX_FILE_SIZE}")

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create DB record
    uploaded = UploadedFile(
        filename=stored_name,
        original_name=original_name,
        content_type=content_type,
        size_bytes=size_bytes,
        status="pending",
        user_id=user_id,
    )
    session.add(uploaded)
    await session.commit()
    await session.refresh(uploaded)
    return uploaded


def parse_file(file_path: Path, content_type: str) -> str:
    """Extract text content from a file based on its type."""
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".docx":
        return _parse_docx(file_path)
    elif ext in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(file_path: Path) -> str:
    """Extract text from PDF using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(str(file_path))
    texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n\n".join(texts)


def _parse_docx(file_path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(str(file_path))
    texts: list[str] = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            texts.append(paragraph.text)
    return "\n\n".join(texts)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks using recursive character splitting."""
    if not text.strip():
        return []

    chunks: list[str] = []
    separators = ["\n\n", "\n", ". ", " "]

    def _split(text: str, sep_idx: int = 0) -> list[str]:
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        if sep_idx >= len(separators):
            # No more separators — hard split
            result = []
            for i in range(0, len(text), chunk_size - overlap):
                piece = text[i : i + chunk_size].strip()
                if piece:
                    result.append(piece)
            return result

        sep = separators[sep_idx]
        parts = text.split(sep)
        result = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    result.append(current.strip())
                if len(part) > chunk_size:
                    result.extend(_split(part, sep_idx + 1))
                    current = ""
                else:
                    current = part

        if current.strip():
            result.append(current.strip())

        return result

    raw_chunks = _split(text)

    # Add overlap between chunks
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and overlap > 0:
            prev_tail = raw_chunks[i - 1][-overlap:]
            chunk = prev_tail + " " + chunk
        chunks.append(chunk)

    return chunks


async def process_file(file_id: int, session: AsyncSession) -> None:
    """Full pipeline: parse -> chunk -> embed -> store in ChromaDB."""
    result = await session.execute(
        select(UploadedFile).where(UploadedFile.id == file_id)  # type: ignore[arg-type]
    )
    uploaded = result.scalars().first()
    if uploaded is None:
        logger.error("UploadedFile %d not found", file_id)
        return

    try:
        uploaded.status = "processing"
        session.add(uploaded)
        await session.commit()

        # Parse
        file_path = UPLOAD_DIR / uploaded.filename
        text = parse_file(file_path, uploaded.content_type)

        if not text.strip():
            uploaded.status = "failed"
            session.add(uploaded)
            await session.commit()
            logger.warning("No text extracted from file %d", file_id)
            return

        # Chunk
        chunks = chunk_text(text)
        if not chunks:
            uploaded.status = "failed"
            session.add(uploaded)
            await session.commit()
            return

        # Get embedding settings
        settings_result = await session.execute(select(AppSettings))
        app_settings = settings_result.scalars().first()

        embedding_base_url = app_settings.embedding_base_url if app_settings else None
        embedding_model = app_settings.embedding_model if app_settings else None

        # Embed
        embeddings = await embed_texts(
            chunks,
            base_url=embedding_base_url,
            model=embedding_model,
        )

        # Store in ChromaDB
        add_documents(file_id, chunks, embeddings)

        # Update status
        uploaded.chunk_count = len(chunks)
        uploaded.status = "ready"
        session.add(uploaded)
        await session.commit()

        logger.info(
            "File %d processed: %d chunks embedded",
            file_id,
            len(chunks),
        )

    except Exception:
        logger.exception("Failed to process file %d", file_id)
        uploaded.status = "failed"
        session.add(uploaded)
        await session.commit()


async def delete_file(file_id: int, session: AsyncSession) -> bool:
    """Delete a file: remove from ChromaDB, disk, and DB."""
    result = await session.execute(
        select(UploadedFile).where(UploadedFile.id == file_id)  # type: ignore[arg-type]
    )
    uploaded = result.scalars().first()
    if uploaded is None:
        return False

    # Remove from ChromaDB
    try:
        delete_file_documents(file_id)
    except Exception:
        logger.warning("Failed to delete ChromaDB documents for file %d", file_id)

    # Remove from disk
    file_path = UPLOAD_DIR / uploaded.filename
    try:
        if file_path.exists():
            os.remove(file_path)
    except OSError:
        logger.warning("Failed to delete file from disk: %s", file_path)

    # Remove from DB
    await session.delete(uploaded)
    await session.commit()
    return True
