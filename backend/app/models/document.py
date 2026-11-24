import enum
from sqlalchemy import Column, String, Integer, Text, Enum, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False, default="application/pdf")
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)
    total_pages = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=0)
    content_hash = Column(String(64), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

