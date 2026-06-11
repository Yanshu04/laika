from unittest.mock import MagicMock, patch
from app.services.embedding_service import EmbeddingService

@patch("app.services.embedding_service.SentenceTransformer")
@patch("app.services.embedding_service.chromadb.PersistentClient")
def test_embedding_service_workflow(mock_chroma_client_class, mock_transformer_class):
    # Reset internal static variables to ensure clean test state
    EmbeddingService._model = None
    EmbeddingService._chroma_client = None
    EmbeddingService._collection = None
    
    # 1. Setup Mock Model
    mock_model = MagicMock()
    # Mock encoding return: array of float arrays
    mock_model.encode.return_value = [[0.1, -0.2, 0.3]]
    mock_transformer_class.return_value = mock_model
    
    # 2. Setup Mock ChromaDB client and collection
    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_chroma_client_class.return_value = mock_client
    
    # 3. Test Lazy initialization
    model = EmbeddingService.get_model()
    assert model == mock_model
    mock_transformer_class.assert_called_once()
    
    client = EmbeddingService.get_chroma_client()
    assert client == mock_client
    mock_chroma_client_class.assert_called_once()
    
    collection = EmbeddingService.get_collection()
    assert collection == mock_collection
    mock_client.get_or_create_collection.assert_called_with(
        name=EmbeddingService.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 4. Test Embedding Generation
    embs = EmbeddingService.get_embeddings(["Hello world"])
    assert embs == [[0.1, -0.2, 0.3]]
    mock_model.encode.assert_called_once()
    
    # 5. Test Adding document chunks
    doc_id = "test-doc-id"
    filename = "test.pdf"
    chunks = [
        {"text": "Chunk text 1", "page_number": 1, "chunk_index": 0},
        {"text": "Chunk text 2", "page_number": None, "chunk_index": 1}
    ]
    
    # Mock encode for two chunks
    mock_model.encode.return_value = [[0.1, 0.2], [0.3, 0.4]]
    
    EmbeddingService.add_document_chunks(doc_id, filename, chunks)
    
    mock_collection.add.assert_called_once()
    call_args = mock_collection.add.call_args[1]
    
    assert call_args["ids"] == ["test-doc-id_0", "test-doc-id_1"]
    assert call_args["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]
    assert call_args["documents"] == ["Chunk text 1", "Chunk text 2"]
    assert call_args["metadatas"] == [
        {"document_id": doc_id, "filename": filename, "page_number": 1, "chunk_index": 0},
        {"document_id": doc_id, "filename": filename, "page_number": -1, "chunk_index": 1}
    ]
    
    # 6. Test Vector deletion
    EmbeddingService.delete_document_vectors(doc_id)
    mock_collection.delete.assert_called_once_with(where={"document_id": doc_id})
