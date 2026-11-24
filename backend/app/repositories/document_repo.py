from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentCreate


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_by_hash(self, content_hash: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.content_hash == content_hash).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def count_all(self) -> int:
        return self.db.query(Document).count()

    def create(self, doc_in: DocumentCreate) -> Document:
        doc = Document(
            filename=doc_in.filename,
            file_path=doc_in.file_path,
            file_size=doc_in.file_size,
            mime_type=doc_in.mime_type,
            content_hash=doc_in.content_hash,
            metadata_json=doc_in.metadata_json,
            status=DocumentStatus.PENDING
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        error_message: Optional[str] = None,
        total_pages: Optional[int] = None,
        total_chunks: Optional[int] = None
    ) -> Optional[Document]:
        doc = self.get_by_id(document_id)
        if not doc:
            return None
        doc.status = status
        if error_message is not None:
            doc.error_message = error_message
        if total_pages is not None:
            doc.total_pages = total_pages
        if total_chunks is not None:
            doc.total_chunks = total_chunks
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete(self, document_id: str) -> bool:
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

