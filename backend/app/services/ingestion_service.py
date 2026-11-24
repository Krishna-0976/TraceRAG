import re
import hashlib
from typing import List, Dict, Any, Tuple
import pymupdf  # PyMuPDF
from app.core.exceptions import InvalidFileException, DocumentProcessingException


class IngestionService:
    """
    Handles PDF validation, text extraction per page using PyMuPDF,
    text normalization/cleaning, and sliding-window chunking with overlap.
    """

    @staticmethod
    def calculate_file_hash(file_bytes: bytes) -> str:
        """Computes SHA-256 hash of file content for deduplication."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def extract_pdf_pages(file_path: str) -> List[Tuple[int, str]]:
        """
        Extracts raw text per page from a PDF file using PyMuPDF.
        Returns a list of (page_number, text) tuples (1-indexed).
        """
        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            raise InvalidFileException(f"Failed to open PDF document: {str(e)}")

        try:
            total_pages = doc.page_count
            if total_pages == 0:
                raise DocumentProcessingException("PDF file contains no pages.")

            pages_data: List[Tuple[int, str]] = []
            total_text_length = 0

            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                # Extract text using PyMuPDF
                text = page.get_text("text") or ""
                cleaned_page_text = IngestionService.clean_text(text)
                pages_data.append((page_num + 1, cleaned_page_text))
                total_text_length += len(cleaned_page_text.strip())

            if total_text_length == 0:
                raise DocumentProcessingException(
                    "The uploaded PDF has no extractable text (it may be scanned images or empty)."
                )

            return pages_data
        finally:
            doc.close()

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Normalizes extracted text:
        - Normalizes unicode characters
        - Fixes hyphenated line breaks (e.g., 'trans-\nfer' -> 'transfer')
        - Normalizes excessive whitespace and blank lines
        - Removes control characters
        """
        if not raw_text:
            return ""

        # Remove null bytes and control chars except newlines and tabs
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)

        # Fix hyphenated words broken across lines
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # Replace multiple horizontal spaces/tabs with a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Replace 3 or more consecutive newlines with 2 newlines (preserve paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def chunk_pages(
        pages_data: List[Tuple[int, str]],
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Chunks document text into overlapping chunks, tracking page numbers and boundaries.
        
        Args:
            pages_data: List of (page_number, text)
            chunk_size: Target character count per chunk
            chunk_overlap: Number of characters to overlap between successive chunks
        
        Returns:
            List of chunk dicts: {chunk_index, page_number, text, token_count, metadata_json}
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        step = chunk_size - chunk_overlap

        for page_num, page_text in pages_data:
            if not page_text:
                continue

            # If page text is smaller than chunk_size, treat as one chunk
            if len(page_text) <= chunk_size:
                token_count = max(1, len(page_text.split()))
                chunks.append({
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "text": page_text,
                    "token_count": token_count,
                    "metadata_json": {
                        "char_length": len(page_text),
                        "page": page_num,
                        "is_single_page": True
                    }
                })
                chunk_index += 1
                continue

            # Sliding window over the page text
            start = 0
            text_len = len(page_text)

            while start < text_len:
                end = min(start + chunk_size, text_len)

                # Attempt to break on sentence or word boundary if not at end of text
                if end < text_len:
                    # Look backwards for a sentence boundary (., !, ?, \n) within last 80 chars
                    search_start = max(start + chunk_size - 80, start)
                    sub = page_text[search_start:end]
                    punct_pos = max(
                        sub.rfind(". "),
                        sub.rfind(".\n"),
                        sub.rfind("! "),
                        sub.rfind("? "),
                        sub.rfind("\n\n")
                    )
                    if punct_pos != -1:
                        end = search_start + punct_pos + 1
                    else:
                        # Otherwise fall back to a word boundary (space)
                        space_pos = sub.rfind(" ")
                        if space_pos != -1:
                            end = search_start + space_pos

                chunk_content = page_text[start:end].strip()
                if chunk_content:
                    token_count = max(1, len(chunk_content.split()))
                    chunks.append({
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "text": chunk_content,
                        "token_count": token_count,
                        "metadata_json": {
                            "char_length": len(chunk_content),
                            "page": page_num,
                            "start_char": start,
                            "end_char": end
                        }
                    })
                    chunk_index += 1

                if end >= text_len:
                    break

                start += step

        return chunks

