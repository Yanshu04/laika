import pytest
from datetime import datetime
from app.models.models import DocumentMetadata
from app.repositories.document_repository import DocumentRepository

def test_document_repository_crud():
    # 1. Create a dummy document metadata
    doc_id = "test-uuid-123"
    doc = DocumentMetadata(
        id=doc_id,
        filename="test_file.pdf",
        file_path="/path/to/test_file.pdf",
        status="UPLOADING",
        chunk_count=0,
        page_count=10,
        created_at=datetime.utcnow().isoformat()
    )
    
    # Verify database is empty initially or can fetch empty
    all_docs = DocumentRepository.get_all()
    # It might contain items if other tests run, but we will look for our specific item
    assert not any(d.id == doc_id for d in all_docs)
    
    # 2. Save document
    DocumentRepository.save(doc)
    
    # 3. Retrieve document by ID
    retrieved = DocumentRepository.get_by_id(doc_id)
    assert retrieved is not None
    assert retrieved.id == doc_id
    assert retrieved.filename == "test_file.pdf"
    assert retrieved.status == "UPLOADING"
    assert retrieved.page_count == 10
    
    # 4. Update status
    DocumentRepository.update_status(doc_id, "INDEXED", chunk_count=15)
    updated = DocumentRepository.get_by_id(doc_id)
    assert updated is not None
    assert updated.status == "INDEXED"
    assert updated.chunk_count == 15
    
    # 5. Get all
    all_docs = DocumentRepository.get_all()
    assert len(all_docs) >= 1
    assert any(d.id == doc_id for d in all_docs)
    
    # 6. Delete
    DocumentRepository.delete(doc_id)
    deleted = DocumentRepository.get_by_id(doc_id)
    assert deleted is None
