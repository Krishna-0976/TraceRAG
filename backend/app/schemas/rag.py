from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.chunk import ChunkSearchHit


class Citation(BaseModel):
    source_document: str
    document_id: str
    page_number: int
    excerpt: str
    chunk_id: str
    similarity_score: float


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question about documents")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID if continuing thread")
    document_ids: Optional[List[str]] = Field(default=None, description="Restrict retrieval to specific document IDs")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of context passages to retrieve")
    similarity_threshold: float = Field(default=0.40, ge=0.0, le=1.0, description="Minimum similarity threshold")


class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    retrieved_chunks: List[ChunkSearchHit] = Field(default_factory=list)
    conversation_id: str
    message_id: str
    grounded: bool
    is_refusal: bool = False
    execution_time_ms: float

