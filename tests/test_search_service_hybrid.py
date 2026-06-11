import pytest
from app.repositories.database import get_db_connection
from app.repositories.document_repository import DocumentRepository
from app.services.search_service import SearchService

def test_sqlite_fts5_indexing_and_search():
    # 1. Insert mock chunks
    doc_id = "test-hybrid-doc"
    filename = "test_hybrid.txt"
    chunks = [
        {"chunk_index": 0, "page_number": None, "text": "The quick brown fox jumps over the lazy dog."},
        {"chunk_index": 1, "page_number": 1, "text": "FastAPI is a modern web framework for Python."}
    ]
    
    # Save to SQLite FTS index
    DocumentRepository.save_chunks(doc_id, filename, chunks)
    
    # 2. Test keyword search for "FastAPI"
    results = SearchService.search("FastAPI", search_mode="keyword", top_k=5)
    assert len(results) >= 1
    assert any("framework" in r["text"] for r in results)
    assert any(r["filename"] == filename for r in results)
    
    # Test keyword search for "fox"
    results_fox = SearchService.search("fox", search_mode="keyword", top_k=5)
    assert len(results_fox) >= 1
    assert any("lazy dog" in r["text"] for r in results_fox)
    
    # 3. Clean up
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (doc_id,))
