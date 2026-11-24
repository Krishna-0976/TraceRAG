from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.chunk import ChunkSearchHit


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document ID filters")
    top_k: int = Field(default=4, ge=1, le=50, description="Maximum chunks to retrieve")
    similarity_threshold: float = Field(default=0.40, ge=0.0, le=1.0, description="Minimum cosine similarity")


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[ChunkSearchHit]
    execution_time_ms: float

