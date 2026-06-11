from typing import List, Optional
from app.models.models import DocumentMetadata
from app.repositories.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentRepository:
    @staticmethod
    def save(doc: DocumentMetadata) -> None:
        """Insert or replace a document metadata record."""
        logger.info(f"Saving document metadata for {doc.filename} ({doc.id})")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO documents (id, filename, file_path, status, chunk_count, page_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (doc.id, doc.filename, doc.file_path, doc.status, doc.chunk_count, doc.page_count, doc.created_at)
            )

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[DocumentMetadata]:
        """Retrieve a document by its ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if row:
                return DocumentMetadata(
                    id=row["id"],
                    filename=row["filename"],
                    file_path=row["file_path"],
                    status=row["status"],
                    chunk_count=row["chunk_count"],
                    page_count=row["page_count"],
                    created_at=row["created_at"]
                )
        return None

    @staticmethod
    def get_all() -> List[DocumentMetadata]:
        """Retrieve all documents."""
        documents = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            for row in rows:
                documents.append(
                    DocumentMetadata(
                        id=row["id"],
                        filename=row["filename"],
                        file_path=row["file_path"],
                        status=row["status"],
                        chunk_count=row["chunk_count"],
                        page_count=row["page_count"],
                        created_at=row["created_at"]
                    )
                )
        return documents

    @staticmethod
    def delete(doc_id: str) -> None:
        """Delete a document by ID."""
        logger.info(f"Deleting document metadata and chunks for {doc_id}")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            cursor.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (doc_id,))

    @staticmethod
    def update_status(
        doc_id: str,
        status: str,
        chunk_count: Optional[int] = None,
        page_count: Optional[int] = None
    ) -> None:
        """Update the status and optionally chunk_count/page_count of a document."""
        logger.info(f"Updating status for document {doc_id} to {status}")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if chunk_count is not None and page_count is not None:
                cursor.execute(
                    "UPDATE documents SET status = ?, chunk_count = ?, page_count = ? WHERE id = ?",
                    (status, chunk_count, page_count, doc_id)
                )
            elif chunk_count is not None:
                cursor.execute(
                    "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
                    (status, chunk_count, doc_id)
                )
            elif page_count is not None:
                cursor.execute(
                    "UPDATE documents SET status = ?, page_count = ? WHERE id = ?",
                    (status, page_count, doc_id)
                )
            else:
                cursor.execute(
                    "UPDATE documents SET status = ? WHERE id = ?",
                    (status, doc_id)
                )

    @staticmethod
    def save_chunks(doc_id: str, filename: str, chunks: List[dict]) -> None:
        """Save text chunks into SQLite FTS5 index."""
        logger.info(f"Saving {len(chunks)} chunks to SQLite FTS index for {filename}")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                page_val = chunk.get("page_number")
                page_num = page_val if page_val is not None else -1
                cursor.execute(
                    """
                    INSERT INTO document_chunks_fts (document_id, filename, page_number, chunk_index, text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (doc_id, filename, page_num, chunk["chunk_index"], chunk["text"])
                )
