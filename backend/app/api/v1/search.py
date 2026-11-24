from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post("", response_model=APIResponse[SearchResponse])
def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Executes true vector semantic search using pgvector cosine similarity.
    Retrieves the top-K relevant chunks above the similarity threshold.
    """
    retrieval_service = RetrievalService(db)
    result = retrieval_service.search(
        query=request.query,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        document_ids=request.document_ids
    )
    return APIResponse(
        success=True,
        message=f"Found {result.total_results} matching passages in {result.execution_time_ms} ms.",
        data=result
    )

