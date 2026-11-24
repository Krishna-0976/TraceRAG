from fastapi import APIRouter
from app.api.v1.documents import router as documents_router
from app.api.v1.search import router as search_router
from app.api.v1.rag import router as rag_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.evaluation import router as evaluation_router

api_v1_router = APIRouter()

api_v1_router.include_router(documents_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(evaluation_router)

