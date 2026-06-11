from fastapi import APIRouter, File, UploadFile, BackgroundTasks, HTTPException, status
from typing import List
from app.models.models import DocumentMetadata
from app.services.document_service import DocumentService
from app.repositories.document_repository import DocumentRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

def validate_file(filename: str):
    """Validate file extension."""
    import pathlib
    suffix = pathlib.Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Only PDF, DOCX, TXT, and MD files are allowed."
        )

@router.post("/upload", response_model=List[DocumentMetadata], status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Upload multiple document files (PDF, DOCX, TXT, or MD).
    Files are stored on disk and parsed/indexed asynchronously.
    """
    logger.info(f"Received request to upload {len(files)} files.")
    created_docs = []
    
    for upload_file in files:
        if not upload_file.filename:
            continue
            
        # Validate extension
        validate_file(upload_file.filename)
        
        try:
            # Read file content
            content = await upload_file.read()
            
            # Initialize record and store file
            doc = DocumentService.save_and_initialize(content, upload_file.filename)
            created_docs.append(doc)
            
            # Queue the heavy parsing & vectorization job to background tasks
            background_tasks.add_task(DocumentService.process_document, doc.id)
            
        except Exception as e:
            logger.error(f"Error handling file upload for '{upload_file.filename}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload '{upload_file.filename}': {str(e)}"
            )
            
    return created_docs

@router.get("", response_model=List[DocumentMetadata])
def list_documents():
    """Retrieve metadata of all uploaded documents."""
    return DocumentService.get_all_documents()

@router.post("/{doc_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_document(
    doc_id: str,
    background_tasks: BackgroundTasks
):
    """
    Retry indexing a document that previously failed.
    Resets its status to UPLOADING and re-queues the processing pipeline.
    """
    doc = DocumentService.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {doc_id} not found."
        )

    if doc.status != "ERROR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not in ERROR state"
        )

    logger.info(f"Retry requested for document '{doc.filename}' ({doc_id})")

    try:
        # Reset status back to UPLOADING
        DocumentRepository.update_status(doc_id, "UPLOADING")

        # Re-queue the processing pipeline
        background_tasks.add_task(DocumentService.process_document, doc_id)

        return {"message": f"Reprocessing started for document '{doc.filename}'"}
    except Exception as e:
        logger.error(f"Error retrying document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry document: {str(e)}"
        )

@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(doc_id: str):
    """Delete a document, its file on disk, and its vector embeddings."""
    doc = DocumentService.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {doc_id} not found."
        )
        
    try:
        DocumentService.delete_document(doc_id)
        return {"message": f"Successfully deleted document '{doc.filename}'"}
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
