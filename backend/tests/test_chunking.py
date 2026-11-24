import pytest
from app.services.ingestion_service import IngestionService


def test_chunking_small_text_single_chunk():
    pages_data = [(1, "Short sentence that easily fits in a single chunk.")]
    chunks = IngestionService.chunk_pages(pages_data, chunk_size=500, chunk_overlap=100)
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert "Short sentence" in chunks[0]["text"]
    assert chunks[0]["token_count"] > 0


def test_chunking_multi_page_and_overlap():
    long_text = "This is sentence one. " * 30  # Approx 660 chars
    pages_data = [(1, long_text), (2, "Second page text content.")]
    chunks = IngestionService.chunk_pages(pages_data, chunk_size=200, chunk_overlap=50)

    # Page 1 should split into multiple overlapping chunks
    assert len(chunks) > 2
    # Verify page tracking
    page_1_chunks = [c for c in chunks if c["page_number"] == 1]
    page_2_chunks = [c for c in chunks if c["page_number"] == 2]

    assert len(page_1_chunks) >= 3
    assert len(page_2_chunks) == 1
    assert "Second page" in page_2_chunks[0]["text"]


def test_chunking_invalid_parameters():
    pages_data = [(1, "Some text")]
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        IngestionService.chunk_pages(pages_data, chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_overlap must be strictly less than chunk_size"):
        IngestionService.chunk_pages(pages_data, chunk_size=100, chunk_overlap=100)

