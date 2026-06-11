import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from app.models.models import DocumentMetadata
from app.repositories.document_repository import DocumentRepository
from app.services.parser_service import TextExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentService:
    @staticmethod
    def get_all_documents() -> List[DocumentMetadata]:
        """Fetch all documents from metadata repository."""
        return DocumentRepository.get_all()

    @staticmethod
    def get_document_by_id(doc_id: str) -> Optional[DocumentMetadata]:
        """Fetch document by ID."""
        return DocumentRepository.get_by_id(doc_id)

    @classmethod
    def save_and_initialize(cls, file_content: bytes, filename: str) -> DocumentMetadata:
        """
        Saves the file to local filesystem, creates an entry in SQLite 
        with status 'UPLOADING', and returns the document metadata object.
        """
        # Ensure directories exist
        settings.ensure_dirs()
        
        # 1. Create a unique document ID and file path
        doc_id = str(uuid.uuid4())
        suffix = Path(filename).suffix.lower()
        file_path = settings.UPLOAD_DIR / f"{doc_id}{suffix}"
        
        # 2. Write file content to disk
        logger.info(f"Writing uploaded file '{filename}' to disk: {file_path}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
            
        # 3. Save initial document metadata to DB
        doc = DocumentMetadata(
            id=doc_id,
            filename=filename,
            file_path=str(file_path),
            status="UPLOADING",
            chunk_count=0,
            page_count=None,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        DocumentRepository.save(doc)
        
        return doc

    @classmethod
    def process_document(cls, doc_id: str) -> None:
        """
        Processes an uploaded document in the background:
        - Extracts text page-by-page (or paragraphs)
        - Chunks text
        - Generates embeddings and writes to ChromaDB
        - Updates SQLite status to 'INDEXED' (or 'ERROR' on failure)
        """
        doc = DocumentRepository.get_by_id(doc_id)
        if not doc:
            logger.error(f"Cannot process document: ID {doc_id} not found in database.")
            return

        file_path = Path(doc.file_path)
        logger.info(f"Starting background processing for {doc.filename} ({doc_id})")
        
        try:
            # 1. Extract Text
            pages = TextExtractionService.extract_text(file_path)
            
            # Count pages for PDFs, set None for DOCX
            page_count = len(pages) if file_path.suffix.lower() == ".pdf" else None
            
            # 2. Chunk text
            chunks = ChunkingService.chunk_document(pages)
            chunk_count = len(chunks)
            
            # 3. Generate embeddings and store in ChromaDB
            EmbeddingService.add_document_chunks(doc_id, doc.filename, chunks)
            
            # Save chunks to SQLite FTS database as well for hybrid search
            DocumentRepository.save_chunks(doc_id, doc.filename, chunks)
            
            # 4. Update status in database
            DocumentRepository.update_status(
                doc_id=doc_id,
                status="INDEXED",
                chunk_count=chunk_count,
                page_count=page_count
            )
            logger.info(f"Successfully finished processing for document {doc.filename} ({doc_id})")
            
        except Exception as e:
            logger.error(f"Failed to process document {doc.filename} ({doc_id}): {e}", exc_info=True)
            DocumentRepository.update_status(doc_id=doc_id, status="ERROR")

    @classmethod
    def delete_document(cls, doc_id: str) -> None:
        """
        Completely deletes a document:
        - Removes its vector embeddings from ChromaDB
        - Removes the file from the local filesystem
        - Removes its metadata from SQLite database
        """
        doc = DocumentRepository.get_by_id(doc_id)
        if not doc:
            logger.warning(f"Delete requested for non-existent document ID: {doc_id}")
            return
            
        logger.info(f"Initiating complete deletion of document: {doc.filename} ({doc_id})")
        
        # 1. Delete vector embeddings
        try:
            EmbeddingService.delete_document_vectors(doc_id)
        except Exception as e:
            logger.error(f"Failed to delete vector embeddings for {doc.filename} during document deletion: {e}")
            
        # 2. Delete file from local filesystem
        file_path = Path(doc.file_path)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Removed file from upload folder: {file_path}")
            else:
                logger.warning(f"File not found on disk: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path} from disk: {e}")
            
        # 3. Delete metadata entry
        try:
            DocumentRepository.delete(doc_id)
            logger.info(f"Removed document metadata for ID {doc_id} from SQLite.")
        except Exception as e:
            logger.error(f"Failed to delete SQLite metadata for document {doc_id}: {e}")
            raise
