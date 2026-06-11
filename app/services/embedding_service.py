import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    _model: Optional[SentenceTransformer] = None
    _chroma_client: Optional[chromadb.PersistentClient] = None
    _collection: Optional[Any] = None
    COLLECTION_NAME = "laika_knowledge_base"

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Lazily initialize and return the SentenceTransformer model."""
        if cls._model is None:
            logger.info(f"Initializing Embedding Model: {settings.EMBEDDING_MODEL}")
            logger.info("NOTE: On first launch, this will download the model from HuggingFace. Subsequent runs will use the local cache.")
            try:
                cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Embedding model loading failed: {e}") from e
        return cls._model

    @classmethod
    def get_chroma_client(cls) -> chromadb.PersistentClient:
        """Lazily initialize and return the ChromaDB client."""
        if cls._chroma_client is None:
            logger.info(f"Initializing persistent ChromaDB client at: {settings.CHROMA_DIR}")
            try:
                cls._chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise RuntimeError(f"ChromaDB initialization failed: {e}") from e
        return cls._chroma_client

    @classmethod
    def get_collection(cls) -> Any:
        """Get or create the ChromaDB collection."""
        if cls._collection is None:
            client = cls.get_chroma_client()
            try:
                cls._collection = client.get_or_create_collection(
                    name=cls.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                logger.info(f"Collection '{cls.COLLECTION_NAME}' is ready.")
            except Exception as e:
                logger.error(f"Failed to get or create collection: {e}")
                raise RuntimeError(f"ChromaDB collection retrieval failed: {e}") from e
        return cls._collection

    @classmethod
    def get_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts."""
        model = cls.get_model()
        try:
            embeddings = model.encode(texts, convert_to_numpy=True)
            if hasattr(embeddings, "tolist"):
                return embeddings.tolist()
            return [list(emb) if hasattr(emb, "__iter__") else emb for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    @classmethod
    def add_document_chunks(
        cls, 
        doc_id: str, 
        filename: str, 
        chunks: List[Dict[str, Any]]
    ) -> None:
        """
        Add document chunks and their embeddings to the vector database.
        chunks schema: [{"text": str, "page_number": int/None, "chunk_index": int}]
        """
        if not chunks:
            logger.warning("No chunks to add to vector database.")
            return

        logger.info(f"Indexing {len(chunks)} chunks for document {filename} ({doc_id})")
        
        texts = [chunk["text"] for chunk in chunks]
        embeddings = cls.get_embeddings(texts)
        collection = cls.get_collection()
        
        ids = []
        metadatas = []
        documents = []
        
        for idx, chunk in enumerate(chunks):
            # Generate unique chunk ID: <doc_id>_<chunk_index>
            chunk_id = f"{doc_id}_{chunk['chunk_index']}"
            ids.append(chunk_id)
            
            # Metadata must not contain None, convert None to -1 (for pages) or empty strings
            page_num = chunk["page_number"]
            page_val = page_num if page_num is not None else -1
            
            metadatas.append({
                "document_id": doc_id,
                "filename": filename,
                "page_number": page_val,
                "chunk_index": chunk["chunk_index"]
            })
            documents.append(chunk["text"])
            
        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Successfully added vector embeddings for {filename} to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to add document vectors to ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB write failed: {e}") from e

    @classmethod
    def delete_document_vectors(cls, doc_id: str) -> None:
        """Delete all vectors associated with a document ID from ChromaDB."""
        logger.info(f"Deleting vector embeddings for document ID: {doc_id}")
        collection = cls.get_collection()
        try:
            collection.delete(where={"document_id": doc_id})
            logger.info(f"Successfully deleted vectors for document ID: {doc_id} from ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to delete vectors from ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB delete failed: {e}") from e
