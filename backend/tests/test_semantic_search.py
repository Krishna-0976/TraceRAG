import pytest
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.schemas.document import DocumentCreate
from app.schemas.chunk import DocumentChunkCreate
from app.models.document import DocumentStatus


def test_semantic_search_retrieval(db_session, deterministic_embedding_service):
    doc_repo = DocumentRepository(db_session)
    chunk_repo = ChunkRepository(db_session)

    # Insert test document
    doc = doc_repo.create(
        DocumentCreate(
            filename="cloud_security.pdf",
            file_path="/tmp/cloud_security.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
    )
    doc_repo.update_status(doc.id, DocumentStatus.COMPLETED)

    # Insert chunks with embeddings
    chunks_text = [
        "Multi-Factor Authentication (MFA) and FIDO2 keys are strictly required for cloud infrastructure.",
        "Database backups must be retained for 365 days in an immutable WORM storage vault.",
        "Coffee machine maintenance instructions and breakroom etiquette."
    ]
    embeddings = deterministic_embedding_service.embed_texts(chunks_text)

    chunk_creates = [
        DocumentChunkCreate(
            document_id=doc.id,
            chunk_index=i,
            page_number=i + 1,
            text=chunks_text[i],
            token_count=15,
            embedding=embeddings[i]
        )
        for i in range(3)
    ]
    chunk_repo.bulk_create(chunk_creates)

    # Test retrieval service
    retrieval_svc = RetrievalService(db_session, deterministic_embedding_service)
    
    # Query matching chunk 0
    res = retrieval_svc.search(
        query="What authentication is required for infrastructure?",
        top_k=2,
        similarity_threshold=0.30
    )

    assert res.total_results > 0
    top_hit = res.results[0]
    assert "Multi-Factor Authentication" in top_hit.text
    assert top_hit.page_number == 1
    assert top_hit.similarity_score > 0.30


def test_semantic_search_no_match(db_session, deterministic_embedding_service):
    retrieval_svc = RetrievalService(db_session, deterministic_embedding_service)
    # Query with impossible similarity threshold
    res = retrieval_svc.search(
        query="Some obscure query",
        top_k=4,
        similarity_threshold=0.999
    )
    assert res.total_results == 0

