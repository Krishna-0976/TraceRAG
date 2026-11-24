import pytest
from app.services.evaluation_service import EvaluationService
from app.schemas.chunk import ChunkSearchHit


def test_hit_rate_at_k():
    hits = [
        ChunkSearchHit(
            id="1", document_id="d1", document_name="doc_a.pdf",
            chunk_index=0, page_number=1, text="Text", similarity_score=0.9, token_count=10
        ),
        ChunkSearchHit(
            id="2", document_id="d2", document_name="doc_b.pdf",
            chunk_index=0, page_number=2, text="Text", similarity_score=0.8, token_count=10
        )
    ]

    # Hit: doc_b.pdf is in retrieved hits
    hr_match = EvaluationService.calculate_hit_rate_at_k("doc_b.pdf", 2, hits)
    assert hr_match == 1.0

    # Miss: doc_c.pdf is not in retrieved hits
    hr_miss = EvaluationService.calculate_hit_rate_at_k("doc_c.pdf", 1, hits)
    assert hr_miss == 0.0

    # Page mismatch
    hr_page_miss = EvaluationService.calculate_hit_rate_at_k("doc_b.pdf", 5, hits)
    assert hr_page_miss == 0.0


def test_mrr_calculation():
    hits = [
        ChunkSearchHit(
            id="1", document_id="d1", document_name="wrong_doc.pdf",
            chunk_index=0, page_number=1, text="Text", similarity_score=0.9, token_count=10
        ),
        ChunkSearchHit(
            id="2", document_id="d2", document_name="target_doc.pdf",
            chunk_index=0, page_number=3, text="Target text", similarity_score=0.85, token_count=10
        ),
        ChunkSearchHit(
            id="3", document_id="d3", document_name="another_doc.pdf",
            chunk_index=0, page_number=1, text="Text", similarity_score=0.8, token_count=10
        )
    ]

    # First relevant chunk is at rank 2 -> MRR = 1/2 = 0.5
    mrr = EvaluationService.calculate_mrr("target_doc.pdf", 3, hits)
    assert mrr == 0.5

    # First chunk is relevant -> MRR = 1/1 = 1.0
    mrr_first = EvaluationService.calculate_mrr("wrong_doc.pdf", 1, hits)
    assert mrr_first == 1.0

    # Not found -> MRR = 0.0
    mrr_none = EvaluationService.calculate_mrr("absent.pdf", None, hits)
    assert mrr_none == 0.0


def test_recall_at_k():
    expected_context = "Zero trust architecture requires continuous authentication and authorization."
    hits = [
        ChunkSearchHit(
            id="1", document_id="d1", document_name="security.pdf",
            chunk_index=0, page_number=1,
            text="The company enforces zero trust architecture with strict authentication and continuous authorization.",
            similarity_score=0.92, token_count=15
        )
    ]

    recall = EvaluationService.calculate_recall_at_k(expected_context, hits)
    assert recall >= 0.80  # Most key tokens recovered


def test_deterministic_generation_evaluation(db_session, deterministic_embedding_service):
    eval_svc = EvaluationService(db_session, embedding_service=deterministic_embedding_service)

    chunks = [
        ChunkSearchHit(
            id="c1", document_id="d1", document_name="sec.pdf",
            chunk_index=0, page_number=1,
            text="AES-256 encryption is mandatory for all data at rest.",
            similarity_score=0.9, token_count=10
        )
    ]

    faith_s, _, corr_s, _, cit_s, _ = eval_svc.evaluate_generation(
        question="What encryption is mandatory for data at rest?",
        generated_answer="AES-256 encryption is mandatory for data at rest.",
        expected_answer="Data at rest must use AES-256 encryption.",
        retrieved_chunks=chunks,
        citations=[{"source_document": "sec.pdf", "page_number": 1, "excerpt": "AES-256 encryption is mandatory"}]
    )

    assert faith_s >= 0.75
    assert corr_s >= 0.75
    assert cit_s == 1.0
