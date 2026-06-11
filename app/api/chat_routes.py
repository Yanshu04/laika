from fastapi import APIRouter, HTTPException, status
from app.models.models import QueryRequest, QueryResponse
from app.rag.rag_pipeline import RagPipeline
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/query", response_model=QueryResponse)
def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge assistant.
    The system will perform vector search across indexed documents,
    formulate a context-grounded prompt, and ask the local Ollama LLM for an answer.
    """
    logger.info(f"Received query request: '{request.question}'")
    try:
        response = RagPipeline.answer_question(
            question=request.question,
            history=request.history,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            temperature=request.temperature,
            search_mode=request.search_mode
        )
        return response
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(e)}"
        )
