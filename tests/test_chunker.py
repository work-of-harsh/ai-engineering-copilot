
import pytest

from app.ingestion.chunker import chunk_document


def test_chunk_document_preserves_source_path():
    chunks = chunk_document(
        path="app/payment.py",
        content="line one\nline two\nline three",
        chunk_size=100,
        overlap=10,
    )

    assert len(chunks) == 1
    assert chunks[0]["path"] == "app/payment.py"
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 3


def test_chunk_document_returns_empty_for_empty_content():
    assert chunk_document("empty.txt", "") == []


def test_chunk_document_rejects_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_document("file.py", "hello", chunk_size=0)


def test_chunk_document_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_document("file.py", "hello", chunk_size=10, overlap=10)
