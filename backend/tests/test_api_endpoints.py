import io
import pymupdf
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "TraceRAG" in data["service"]


def test_dashboard_stats(client: TestClient):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_documents" in data["data"]
    assert "total_chunks" in data["data"]


def test_document_upload_and_listing(client: TestClient):
    # Create in-memory PDF
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 70), "This is an integration test document for TraceRAG API testing.")
    pdf_bytes = doc.write()
    doc.close()

    files = {"file": ("integration_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_resp = client.post("/api/v1/documents/upload", files=files)
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["success"] is True
    doc_id = upload_data["data"]["id"]
    assert upload_data["data"]["total_chunks"] >= 1

    # List documents
    list_resp = client.get("/api/v1/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()["data"]
    assert any(d["id"] == doc_id for d in docs)

    # Search endpoint
    search_resp = client.post(
        "/api/v1/search",
        json={"query": "integration test document", "top_k": 2, "similarity_threshold": 0.20}
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()["data"]
    assert search_data["total_results"] > 0

    # RAG query endpoint
    rag_resp = client.post(
        "/api/v1/rag/query",
        json={"query": "What is this integration test document about?", "top_k": 2, "similarity_threshold": 0.20}
    )
    assert rag_resp.status_code == 200
    rag_data = rag_resp.json()["data"]
    assert len(rag_data["answer"]) > 0

    # Clean up / Delete document
    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"] is True


def test_evaluation_endpoints(client: TestClient):
    # Benchmark dataset retrieval
    ds_resp = client.get("/api/v1/evaluation/dataset")
    assert ds_resp.status_code == 200
    ds_data = ds_resp.json()["data"]
    assert len(ds_data["questions"]) >= 15

