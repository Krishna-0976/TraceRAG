from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.core.exceptions import TraceRAGException
from app.api.v1.router import api_v1_router
from app.services.evaluation_service import EvaluationService
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.evaluation_repo import EvaluationRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and default benchmark dataset
    init_db()
    db = SessionLocal()
    try:
        eval_service = EvaluationService(db)
        eval_service.ensure_default_benchmark_dataset()
    finally:
        db.close()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-Grounded AI Knowledge Engine with RAG Evaluation",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized exception handler
@app.exception_handler(TraceRAGException)
async def tracerag_exception_handler(request: Request, exc: TraceRAGException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error": exc.__class__.__name__,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"Internal server error: {str(exc)}",
            "error": "InternalServerError",
            "details": {}
        }
    )


# Health check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL
    }


# Dashboard Stats API
@app.get("/api/v1/stats", tags=["Dashboard"])
def get_dashboard_stats():
    db = SessionLocal()
    try:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)
        conv_repo = ConversationRepository(db)
        eval_repo = EvaluationRepository(db)

        total_docs = doc_repo.count_all()
        total_chunks = chunk_repo.count_all()
        total_messages = conv_repo.count_messages()
        total_convs = conv_repo.count_conversations()
        latest_run = eval_repo.get_latest_run()

        latest_eval_data = None
        if latest_run:
            latest_eval_data = {
                "id": latest_run.id,
                "name": latest_run.name,
                "completed_at": latest_run.completed_at,
                "mean_recall_at_k": latest_run.mean_recall_at_k,
                "mean_mrr": latest_run.mean_mrr,
                "mean_hit_rate_at_k": latest_run.mean_hit_rate_at_k,
                "mean_faithfulness": latest_run.mean_faithfulness,
                "mean_answer_correctness": latest_run.mean_answer_correctness,
                "mean_citation_correctness": latest_run.mean_citation_correctness
            }

        return {
            "success": True,
            "data": {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "total_questions_asked": total_messages,
                "total_conversations": total_convs,
                "latest_evaluation": latest_eval_data
            }
        }
    finally:
        db.close()


# Mount API V1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

