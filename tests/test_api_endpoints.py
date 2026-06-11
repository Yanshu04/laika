from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

from app.main import app
from app.models.models import DocumentMetadata, QueryResponse, SourceCitation

client = TestClient(app)

def test_read_root_health():
    with patch("app.main.LlmService.test_connection", return_value=True):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "Local AI Knowledge Assistant (LAIKA)"
        assert data["services"]["ollama_connected"] is True

def test_upload_invalid_extension():
    response = client.post(
        "/api/documents/upload",
        files=[("files", ("test.txt", b"plain text content", "text/plain"))]
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

@patch("app.api.document_routes.DocumentService")
def test_upload_valid_document(mock_document_service):
    # Setup mock document metadata return
    mock_doc = DocumentMetadata(
        id="mock-uuid-999",
        filename="employee_handbook.pdf",
        file_path="/data/uploads/mock-uuid-999.pdf",
        status="UPLOADING",
        chunk_count=0,
        page_count=None,
        created_at="2026-06-11T09:30:00Z"
    )
    mock_document_service.save_and_initialize.return_value = mock_doc
    
    # Perform file upload
    response = client.post(
        "/api/documents/upload",
        files=[("files", ("employee_handbook.pdf", b"pdf data bytes", "application/pdf"))]
    )
    
    # Assert response
    assert response.status_code == 202
    res_data = response.json()
    assert len(res_data) == 1
    assert res_data[0]["id"] == "mock-uuid-999"
    assert res_data[0]["status"] == "UPLOADING"
    
    # Verify service calls
    mock_document_service.save_and_initialize.assert_called_once()
    mock_document_service.process_document.assert_called_once_with("mock-uuid-999")

@patch("app.api.document_routes.DocumentService")
def test_list_documents(mock_document_service):
    mock_document_service.get_all_documents.return_value = [
        DocumentMetadata(
            id="uuid1", filename="doc1.pdf", file_path="path1", status="INDEXED",
            chunk_count=10, page_count=2, created_at="2026-06-11"
        )
    ]
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "doc1.pdf"

@patch("app.api.document_routes.DocumentService")
def test_delete_document_success(mock_document_service):
    # Setup document exists
    mock_doc = DocumentMetadata(
        id="uuid-delete", filename="delete_me.pdf", file_path="path", status="INDEXED",
        chunk_count=5, page_count=1, created_at="2026-06-11"
    )
    mock_document_service.get_document_by_id.return_value = mock_doc
    
    response = client.delete("/api/documents/uuid-delete")
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully deleted document 'delete_me.pdf'"
    mock_document_service.delete_document.assert_called_once_with("uuid-delete")

@patch("app.api.document_routes.DocumentService")
def test_delete_document_not_found(mock_document_service):
    mock_document_service.get_document_by_id.return_value = None
    response = client.delete("/api/documents/non-existent")
    assert response.status_code == 404

@patch("app.api.chat_routes.RagPipeline")
def test_chat_query_endpoint(mock_rag_pipeline):
    # Setup mock response
    mock_rag_pipeline.answer_question.return_value = QueryResponse(
        answer="The company core values are integrity and innovation.",
        sources=[
            SourceCitation(filename="values.pdf", page_number=2, text_snippet="core values: integrity, innovation")
        ]
    )
    
    response = client.post(
        "/api/chat/query",
        json={"question": "What are the core values?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "integrity and innovation" in data["answer"]
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "values.pdf"
    assert data["sources"][0]["page_number"] == 2
