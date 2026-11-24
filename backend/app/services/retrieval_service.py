import time
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_service import EmbeddingService
from app.schemas.search import SearchRequest, SearchResponse
from app.schemas.chunk import ChunkSearchHit
from app.core.exceptions import RetrievalException


class RetrievalService:
    def __init__(self, db: Session, embedding_service: Optional[EmbeddingService] = None):
        self.db = db
        self.chunk_repo = ChunkRepository(db)
        self.embedding_service = embedding_service or EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.40,
        document_ids: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        Executes semantic vector search for a query:
        1. Encodes query string into embedding vector
        2. Queries vector database using cosine distance
        3. Filters by similarity threshold and document_ids
        4. Returns ranked ChunkSearchHit results
        """
        start_time = time.perf_counter()

        try:
            # 1. Embed query
            query_vector = self.embedding_service.embed_query(query)
            
            # 2. Vector search in database
            hits = self.chunk_repo.search_vector(
                query_vector=query_vector,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                document_ids=document_ids
            )

            execution_time = (time.perf_counter() - start_time) * 1000.0

            return SearchResponse(
                query=query,
                total_results=len(hits),
                results=hits,
                execution_time_ms=round(execution_time, 2)
            )
        except Exception as e:
            raise RetrievalException(f"Failed to execute semantic search: {str(e)}")

    def retrieve_chunks_for_rag(
        self,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.40,
        document_ids: Optional[List[str]] = None
    ) -> List[ChunkSearchHit]:
        """Convenience method returning raw hits for RAG pipeline."""
        search_res = self.search(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            document_ids=document_ids
        )
        return search_res.results

