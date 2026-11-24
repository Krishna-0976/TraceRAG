import pytest
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService
from app.schemas.rag import RAGQueryRequest
from app.schemas.document import DocumentCreate
from app.schemas.chunk import DocumentChunkCreate
from app.models.document import DocumentStatus


def test_rag_grounded_answer_with_citations(db_session, deterministic_embedding_service):
    doc_repo = DocumentRepository(db_session)
    chunk_repo = ChunkRepository(db_session)

    doc = doc_repo.create(
        DocumentCreate(
            filename="policy.pdf",
            file_path="/tmp/policy.pdf",
            file_size=2048,
            mime_type="application/pdf"
        )
    )
    doc_repo.update_status(doc.id, DocumentStatus.COMPLETED)

    text_passage = "Customer-managed encryption keys (CMEK) must be rotated automatically every 90 days."
    emb = deterministic_embedding_service.embed_texts([text_passage])[0]

    chunk_repo.bulk_create([
        DocumentChunkCreate(
            document_id=doc.id,
            chunk_index=0,
            page_number=2,
            text=text_passage,
            token_count=12,
            embedding=emb
        )
    ])

    rag_svc = RAGService(db_session, embedding_service=deterministic_embedding_service)

    req = RAGQueryRequest(
        query="How often must customer-managed encryption keys be rotated?",
        top_k=2,
        similarity_threshold=0.30
    )
    res = rag_svc.query(req)

    assert not res.is_refusal
    assert res.grounded
    assert "90 days" in res.answer
    assert len(res.citations) > 0
    citation = res.citations[0]
    assert citation.page_number == 2
    assert "policy.pdf" in citation.source_document
    assert "rotated" in citation.excerpt.lower()


def test_rag_refusal_when_evidence_is_insufficient(db_session, deterministic_embedding_service):
    rag_svc = RAGService(db_session, embedding_service=deterministic_embedding_service)

    # Empty knowledge base or non-existent fact
    req = RAGQueryRequest(
        query="What is the secret recipe for dark chocolate lava cake?",
        top_k=2,
        similarity_threshold=0.70
    )
    res = rag_svc.query(req)

    assert res.is_refusal
    assert "cannot be established" in res.answer.lower() or "sufficient information" in res.answer.lower()
    assert len(res.citations) == 0

