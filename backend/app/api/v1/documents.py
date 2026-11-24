from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.document import DocumentRead, DocumentDetail, IngestionConfig
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=APIResponse[DocumentRead], status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(..., description="PDF document to ingest"),
    chunk_size: Optional[int] = Form(default=500, description="Target chunk character size"),
    chunk_overlap: Optional[int] = Form(default=100, description="Chunk overlap character count"),
    db: Session = Depends(get_db)
):
    """Uploads and ingests a PDF document into the vector knowledge base."""
    config = IngestionConfig(
        chunk_size=chunk_size or 500,
        chunk_overlap=chunk_overlap or 100
    )
    service = DocumentService(db)
    doc_read = service.upload_and_process_pdf(file, config)
    return APIResponse(
        success=True,
        message=f"Document '{doc_read.filename}' processed successfully ({doc_read.total_chunks} chunks indexed).",
        data=doc_read
    )


@router.get("", response_model=APIResponse[List[DocumentRead]])
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists all uploaded documents."""
    service = DocumentService(db)
    docs = service.list_documents(skip=skip, limit=limit)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(docs)} documents.",
        data=docs
    )


@router.get("/{document_id}", response_model=APIResponse[DocumentDetail])
def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves document metadata along with extracted chunks."""
    service = DocumentService(db)
    detail = service.get_document_detail(document_id)
    return APIResponse(
        success=True,
        message="Document details retrieved.",
        data=detail
    )


@router.delete("/{document_id}", response_model=APIResponse[bool])
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a document, its disk file, and associated vector chunks."""
    service = DocumentService(db)
    deleted = service.delete_document(document_id)
    return APIResponse(
        success=deleted,
        message="Document and vector chunks deleted successfully.",
        data=deleted
    )

