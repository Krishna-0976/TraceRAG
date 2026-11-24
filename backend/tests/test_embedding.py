import math
import pytest
from app.services.embedding_service import EmbeddingService
from app.repositories.chunk_repo import ChunkRepository


def test_embedding_dimensions_and_normalization():
    svc = EmbeddingService(dimension=1536)
    vec = svc.embed_query("Quantum computing and quantum error correction.")
    assert len(vec) == 1536
    # Verify unit norm
    norm = math.sqrt(sum(v * v for v in vec))
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_embedding_semantic_properties():
    svc = EmbeddingService(dimension=1536)
    vec_a = svc.embed_query("Retrieval Augmented Generation with vector databases")
    vec_b = svc.embed_query("Retrieval Augmented Generation with vector databases")
    vec_c = svc.embed_query("Retrieval Augmented Generation with dense embeddings")
    vec_d = svc.embed_query("Recipe for chocolate chip cookies and banana bread")

    # Identical texts must have similarity 1.0
    sim_identical = ChunkRepository._calculate_cosine_similarity(vec_a, vec_b)
    assert pytest.approx(sim_identical, rel=1e-3) == 1.0

    # Highly relevant text should have higher similarity than disparate text
    sim_relevant = ChunkRepository._calculate_cosine_similarity(vec_a, vec_c)
    sim_irrelevant = ChunkRepository._calculate_cosine_similarity(vec_a, vec_d)

    assert sim_relevant > sim_irrelevant
    assert sim_relevant > 0.40


def test_batch_embedding():
    svc = EmbeddingService(dimension=1536)
    texts = ["First chunk of text", "Second chunk of text", "Third chunk of text"]
    embeddings = svc.embed_texts(texts)
    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb) == 1536

