from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkBase(BaseModel):
    chunk_index: int
    page_number: int
    text: str
    token_count: int
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunkCreate(DocumentChunkBase):
    document_id: str
    embedding: Optional[List[float]] = None


class DocumentChunkRead(DocumentChunkBase):
    id: str
    document_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChunkSearchHit(BaseModel):
    id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: int
    text: str
    similarity_score: float
    token_count: int
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
