import os
import pytest
import pymupdf
from app.services.ingestion_service import IngestionService
from app.core.exceptions import InvalidFileException, DocumentProcessingException


def test_clean_text_normalization():
    raw = "This is a test-\nline with   excessive \t spaces \n\n\n\nand multiple breaks."
    cleaned = IngestionService.clean_text(raw)
    assert "testline" in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned


def test_pdf_extraction_valid(tmp_path):
    pdf_path = tmp_path / "valid.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 70), "Page 1 content about machine learning.")
    page2 = doc.new_page()
    page2.insert_text((50, 70), "Page 2 content about neural networks.")
    doc.save(str(pdf_path))
    doc.close()

    pages = IngestionService.extract_pdf_pages(str(pdf_path))
    assert len(pages) == 2
    assert pages[0][0] == 1
    assert "machine learning" in pages[0][1]
    assert pages[1][0] == 2
    assert "neural networks" in pages[1][1]


def test_pdf_extraction_empty_content(tmp_path):
    pdf_path = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()  # Page with no text
    doc.save(str(pdf_path))
    doc.close()

    with pytest.raises(DocumentProcessingException, match="no extractable text"):
        IngestionService.extract_pdf_pages(str(pdf_path))


def test_pdf_extraction_invalid_file(tmp_path):
    fake_path = tmp_path / "corrupt.pdf"
    with open(fake_path, "wb") as f:
        f.write(b"not a valid pdf binary content")

    with pytest.raises(InvalidFileException):
        IngestionService.extract_pdf_pages(str(fake_path))

