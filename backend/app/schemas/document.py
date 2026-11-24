from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.document import DocumentStatus
from app.schemas.chunk import DocumentChunkRead


class DocumentBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str = "application/pdf"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    file_path: str
    content_hash: Optional[str] = None


class DocumentRead(DocumentBase):
    id: str
    status: DocumentStatus
    error_message: Optional[str] = None
    total_pages: int
    total_chunks: int
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentRead):
    chunks: List[DocumentChunkRead] = Field(default_factory=list)


class IngestionConfig(BaseModel):
    chunk_size: int = Field(default=500, ge=50, le=4000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=100, ge=0, le=1000, description="Overlap in characters")
