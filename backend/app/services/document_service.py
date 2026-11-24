import os
import shutil
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import InvalidFileException, DocumentNotFoundException, DocumentProcessingException
from app.models.document import Document, DocumentStatus
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.schemas.document import DocumentCreate, DocumentRead, DocumentDetail, IngestionConfig
from app.schemas.chunk import DocumentChunkCreate, DocumentChunkRead
from app.services.ingestion_service import IngestionService
from app.services.embedding_service import EmbeddingService


class DocumentService:
    def __init__(self, db: Session, embedding_service: Optional[EmbeddingService] = None):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.ingestion_service = IngestionService()
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Ensure upload dir exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def upload_and_process_pdf(
        self,
        file: UploadFile,
        config: Optional[IngestionConfig] = None
    ) -> DocumentRead:
        """
        Full PDF Ingestion Pipeline:
        1. Validates file is PDF
        2. Saves to disk and computes SHA-256 hash
        3. Checks for duplicates
        4. Creates Document database entry
        5. Extracts text & page numbers using PyMuPDF
        6. Chunks text into sliding windows with overlap
        7. Generates vector embeddings
        8. Stores chunks in database
        9. Updates Document status to COMPLETED
        """
        if not file.filename.lower().endswith(".pdf"):
            raise InvalidFileException(f"Unsupported file format: '{file.filename}'. Only PDF files are supported.")

        cfg = config or IngestionConfig(
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP
        )

        # Read file contents
        try:
            content_bytes = file.file.read()
            if len(content_bytes) == 0:
                raise InvalidFileException("Uploaded file is empty (0 bytes).")
            file_size = len(content_bytes)
        except Exception as e:
            raise InvalidFileException(f"Failed to read file: {str(e)}")

        content_hash = self.ingestion_service.calculate_file_hash(content_bytes)

        # Check duplicate
        existing = self.doc_repo.get_by_hash(content_hash)
        if existing and existing.status == DocumentStatus.COMPLETED:
            return DocumentRead.model_validate(existing)

        # Save file to disk
        safe_filename = f"{content_hash[:12]}_{os.path.basename(file.filename)}"
        saved_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        with open(saved_path, "wb") as f:
            f.write(content_bytes)

        # Create Document record
        doc_in = DocumentCreate(
            filename=file.filename,
            file_path=saved_path,
            file_size=file_size,
            mime_type="application/pdf",
            content_hash=content_hash,
            metadata_json={"original_filename": file.filename, "file_size": file_size}
        )
        doc = self.doc_repo.create(doc_in)

        # Update status to PROCESSING
        self.doc_repo.update_status(doc.id, DocumentStatus.PROCESSING)

        try:
            # 1. PyMuPDF extraction
            pages_data = self.ingestion_service.extract_pdf_pages(saved_path)
            total_pages = len(pages_data)

            # 2. Chunking
            chunks_raw = self.ingestion_service.chunk_pages(
                pages_data=pages_data,
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap
            )

            if not chunks_raw:
                raise DocumentProcessingException("No chunks could be extracted from document text.")

            # 3. Embedding generation
            chunk_texts = [c["text"] for c in chunks_raw]
            embeddings = self.embedding_service.embed_texts(chunk_texts)

            # 4. Create chunk records
            chunk_creates: List[DocumentChunkCreate] = []
            for raw, emb in zip(chunks_raw, embeddings):
                chunk_creates.append(
                    DocumentChunkCreate(
                        document_id=doc.id,
                        chunk_index=raw["chunk_index"],
                        page_number=raw["page_number"],
                        text=raw["text"],
                        token_count=raw["token_count"],
                        embedding=emb,
                        metadata_json={
                            **raw.get("metadata_json", {}),
                            "document_name": doc.filename
                        }
                    )
                )

            self.chunk_repo.bulk_create(chunk_creates)

            # 5. Mark as COMPLETED
            updated_doc = self.doc_repo.update_status(
                document_id=doc.id,
                status=DocumentStatus.COMPLETED,
                total_pages=total_pages,
                total_chunks=len(chunk_creates)
            )
            return DocumentRead.model_validate(updated_doc)

        except Exception as e:
            # Mark document as FAILED
            self.doc_repo.update_status(
                document_id=doc.id,
                status=DocumentStatus.FAILED,
                error_message=str(e)
            )
            raise DocumentProcessingException(str(e))

    def list_documents(self, skip: int = 0, limit: int = 100) -> List[DocumentRead]:
        docs = self.doc_repo.get_all(skip=skip, limit=limit)
        return [DocumentRead.model_validate(d) for d in docs]

    def get_document_detail(self, document_id: str) -> DocumentDetail:
        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)

        chunks = self.chunk_repo.get_by_document(document_id)
        chunk_reads = [DocumentChunkRead.model_validate(c) for c in chunks]

        doc_read = DocumentRead.model_validate(doc)
        return DocumentDetail(
            **doc_read.model_dump(),
            chunks=chunk_reads
        )

    def delete_document(self, document_id: str) -> bool:
        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)

        # Delete physical file if exists
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception:
                pass

        # Cascade deletes chunks from DB
        return self.doc_repo.delete(document_id)

