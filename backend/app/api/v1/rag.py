from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.rag import RAGQueryRequest, RAGResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG QA Engine"])


@router.post("/query", response_model=APIResponse[RAGResponse])
def rag_query(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieval-Augmented Generation (RAG) Question Answering:
    1. Embeds query and retrieves semantically relevant document chunks.
    2. Enforces strict context grounding.
    3. Formats answer with verifiable document and page citations.
    4. Refuses hallucination if evidence is absent.
    """
    rag_service = RAGService(db)
    response = rag_service.query(request)
    return APIResponse(
        success=True,
        message="Answer generated with source citations." if not response.is_refusal else "Insufficient evidence to answer from sources.",
        data=response
    )

