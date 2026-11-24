from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.core.database import Base, VectorType
from app.core.config import settings
from app.models.base import TimestampMixin, generate_uuid


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(VectorType(settings.EMBEDDING_DIM), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_doc_chunk_idx", "document_id", "chunk_index"),
    )

