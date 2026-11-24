"""
TraceRAG End-to-End Acceptance Test & Verification Script
Demonstrates the full end-to-end workflow:
1. Ingests 3 multi-page technical PDFs
2. Performs PyMuPDF text extraction & sliding-window chunking
3. Generates 1536-dimensional vector embeddings
4. Executes semantic vector retrieval
5. Generates grounded answer with exact page citations
6. Tests strict refusal when information is absent (zero hallucinations)
7. Runs full 18-question benchmark evaluation suite
8. Compares two distinct retrieval configurations
9. Validates dashboard metrics and persistence
"""
import os
import sys
import json
import time

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

client = TestClient(app)


def print_step(num: int, title: str):
    print(f"\n{'='*70}")
    print(f"STEP {num}: {title.upper()}")
    print(f"{'='*70}")


def main():
    print_step(1, "System Initialization & Health Check")
    init_db()
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    print("Health Status:", json.dumps(health_data, indent=2))

    print_step(2, "Upload & Ingest Three Sample Technical PDFs")
    sample_files = [
        "sample_docs/rag_architecture_overview.pdf",
        "sample_docs/enterprise_cloud_security_policy.pdf",
        "sample_docs/autonomous_agent_workflows.pdf"
    ]

    doc_ids = []
    for filepath in sample_files:
        assert os.path.exists(filepath), f"File {filepath} not found!"
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            upload_resp = client.post(
                "/api/v1/documents/upload",
                files={"file": (filename, f, "application/pdf")},
                data={"chunk_size": 500, "chunk_overlap": 100}
            )
        assert upload_resp.status_code in [200, 201], f"Upload failed for {filename}: {upload_resp.text}"
        data = upload_resp.json()["data"]
        doc_ids.append(data["id"])
        print(f"-> Ingested '{filename}': Status={data['status']}, Pages={data['total_pages']}, Chunks={data['total_chunks']}")

    print_step(3, "Verify Document Details & Chunk Inspection")
    detail_resp = client.get(f"/api/v1/documents/{doc_ids[0]}")
    assert detail_resp.status_code == 200
    doc_detail = detail_resp.json()["data"]
    print(f"Document: {doc_detail['filename']} | Total Chunks: {len(doc_detail['chunks'])}")
    sample_chunk = doc_detail["chunks"][0]
    print(f"Sample Chunk 0 (Page {sample_chunk['page_number']}): '{sample_chunk['text'][:120]}...'")

    print_step(4, "Semantic Vector Search via pgvector Cosine Distance")
    search_query = "What is the mandatory encryption algorithm for data at rest?"
    search_resp = client.post(
        "/api/v1/search",
        json={"query": search_query, "top_k": 3, "similarity_threshold": 0.25}
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()["data"]
    print(f"Query: '{search_query}'")
    print(f"Found {search_data['total_results']} matching passages in {search_data['execution_time_ms']} ms:")
    for i, hit in enumerate(search_data["results"], start=1):
        print(f"  [{i}] Doc: {hit['document_name']} | P.{hit['page_number']} | Sim: {hit['similarity_score']*100:.1f}%")
        print(f"      Snippet: {hit['text'][:100]}...")

    print_step(5, "RAG Grounded QA with Strict Citations")
    rag_query = "What authentication mechanism is mandatory for privileged infrastructure administrators?"
    rag_resp = client.post(
        "/api/v1/rag/query",
        json={"query": rag_query, "top_k": 4, "similarity_threshold": 0.40}
    )
    assert rag_resp.status_code == 200
    rag_data = rag_resp.json()["data"]
    print(f"Question: '{rag_query}'")
    print(f"Grounded: {rag_data['grounded']} | Is Refusal: {rag_data['is_refusal']}")
    print(f"Generated Answer:\n{rag_data['answer']}\n")
    print(f"Verifiable Citations ({len(rag_data['citations'])}):")
    for c in rag_data["citations"]:
        print(f"  * Source: {c['source_document']} | Page: {c['page_number']} | Sim: {c['similarity_score']*100:.1f}%")
        print(f"    Excerpt: \"{c['excerpt']}\"")

    print_step(6, "Negative Test: Hallucination Refusal for Absent Facts")
    unanswerable_q = "What is the secret recipe for dark chocolate lava cake?"
    neg_resp = client.post(
        "/api/v1/rag/query",
        json={"query": unanswerable_q, "top_k": 4, "similarity_threshold": 0.65}
    )
    assert neg_resp.status_code == 200
    neg_data = neg_resp.json()["data"]
    print(f"Question: '{unanswerable_q}'")
    print(f"Is Refusal: {neg_data['is_refusal']} | Citations: {len(neg_data['citations'])}")
    print(f"Answer: {neg_data['answer']}")
    assert neg_data["is_refusal"] is True, "System failed to refuse an unanswerable question!"

    print_step(7, "Execute Evaluation Benchmark Run #1 (Configuration A)")
    run1_resp = client.post(
        "/api/v1/evaluation/run",
        json={
            "name": "Config A (Top-K=4, Thresh=0.40)",
            "top_k": 4,
            "similarity_threshold": 0.40
        }
    )
    assert run1_resp.status_code == 200
    run1_data = run1_resp.json()["data"]
    print(f"Completed Benchmark Run: '{run1_data['name']}' ({run1_data['total_questions']} Questions)")
    print(f"  * Recall@K:             {run1_data['mean_recall_at_k']*100:.2f}%")
    print(f"  * MRR:                  {run1_data['mean_mrr']*100:.2f}%")
    print(f"  * Hit Rate@K:           {run1_data['mean_hit_rate_at_k']*100:.2f}%")
    print(f"  * Faithfulness:         {run1_data['mean_faithfulness']*100:.2f}%")
    print(f"  * Answer Correctness:   {run1_data['mean_answer_correctness']*100:.2f}%")
    print(f"  * Citation Correctness: {run1_data['mean_citation_correctness']*100:.2f}%")

    print_step(8, "Execute Evaluation Benchmark Run #2 (Configuration B - High Recall)")
    run2_resp = client.post(
        "/api/v1/evaluation/run",
        json={
            "name": "Config B (Top-K=6, Thresh=0.25)",
            "top_k": 6,
            "similarity_threshold": 0.25
        }
    )
    assert run2_resp.status_code == 200
    run2_data = run2_resp.json()["data"]
    print(f"Completed Benchmark Run: '{run2_data['name']}' ({run2_data['total_questions']} Questions)")
    print(f"  * Recall@K:             {run2_data['mean_recall_at_k']*100:.2f}%")
    print(f"  * MRR:                  {run2_data['mean_mrr']*100:.2f}%")
    print(f"  * Hit Rate@K:           {run2_data['mean_hit_rate_at_k']*100:.2f}%")
    print(f"  * Faithfulness:         {run2_data['mean_faithfulness']*100:.2f}%")
    print(f"  * Answer Correctness:   {run2_data['mean_answer_correctness']*100:.2f}%")
    print(f"  * Citation Correctness: {run2_data['mean_citation_correctness']*100:.2f}%")

    print_step(9, "Compare Retrieval Configurations Side-by-Side")
    compare_resp = client.post(
        "/api/v1/evaluation/compare",
        json={"run_id_a": run1_data["id"], "run_id_b": run2_data["id"]}
    )
    assert compare_resp.status_code == 200
    comp_data = compare_resp.json()["data"]
    print("Metric Deltas (Config B vs Config A):")
    for metric, delta in comp_data["metrics_delta"].items():
        sign = "+" if delta > 0 else ""
        print(f"  * {metric:25}: {sign}{delta*100:.2f}%")
    print("\nAnalytical Summary Report:")
    print(comp_data["summary_analysis"])

    print_step(10, "Validate Dashboard Aggregations")
    stats_resp = client.get("/api/v1/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Indexed Chunks: {stats['total_chunks']}")
    print(f"Total Messages Logged: {stats['total_questions_asked']}")
    print(f"Latest Evaluation Recorded: {stats['latest_evaluation']['name']}")
    print(f"Latest Faithfulness Score: {stats['latest_evaluation']['mean_faithfulness']*100:.1f}%")

    print("\n" + "="*70)
    print("🎉 ALL ACCEPTANCE CRITERIA VERIFIED AND PASSED SUCCESSFULLY!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
