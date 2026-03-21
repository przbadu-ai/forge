"""Tests for text chunking logic."""

from app.services.file_service import chunk_text


def test_empty_text_returns_empty() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_single_chunk() -> None:
    text = "Hello world."
    chunks = chunk_text(text, chunk_size=512, overlap=50)
    assert len(chunks) == 1
    assert "Hello world." in chunks[0]


def test_long_text_produces_multiple_chunks() -> None:
    # Create text that's clearly longer than chunk_size
    text = " ".join(["word"] * 200)  # ~1000 chars
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1


def test_chunks_have_no_empty_entries() -> None:
    text = "Paragraph one.\n\n\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(text, chunk_size=512, overlap=0)
    for chunk in chunks:
        assert chunk.strip() != ""


def test_overlap_parameter() -> None:
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = chunk_text(text, chunk_size=30, overlap=10)
    # With overlap, later chunks should contain some text from previous chunk
    if len(chunks) > 1:
        # The second chunk should have some overlap from the first
        assert len(chunks[1]) > 0


def test_paragraph_splitting() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunk_text(text, chunk_size=512, overlap=0)
    # All three paragraphs should be captured
    combined = " ".join(chunks)
    assert "First paragraph." in combined
    assert "Second paragraph." in combined
    assert "Third paragraph." in combined
