from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.models import QueryRequest, QueryResponse
from app.rag.rag_pipeline import RagPipeline
from app.services.search_service import SearchService
from app.services.llm_service import LlmService
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/query/stream")
def stream_knowledge_base(request: QueryRequest):
    """
    Streaming endpoint for the knowledge assistant.
    Performs the same retrieval as /query but streams the LLM answer
    token-by-token as plain text.
    """
    logger.info(f"Received streaming query request: '{request.question}'")

    def token_generator():
        try:
            # Resolve defaults
            tk = request.top_k if request.top_k is not None else settings.TOP_K
            st_val = request.score_threshold if request.score_threshold is not None else settings.SCORE_THRESHOLD
            sm = request.search_mode if request.search_mode is not None else "hybrid"

            # 1. Rewrite query if history is present
            search_query = request.question
            if request.history:
                logger.info("Streaming: Conversational history present. Attempting query rewriting...")
                search_query = LlmService.rewrite_query(request.question, request.history)

            # 2. Retrieve top similar chunks
            search_hits = []
            try:
                search_hits = SearchService.search(
                    query=search_query, top_k=tk, score_threshold=st_val, search_mode=sm
                )
            except Exception as e:
                logger.error(f"Streaming: Error during document search: {e}")
                yield "I was unable to search documents because the search index is uninitialized or not loaded."
                return

            # 3. Extract contexts
            contexts = []
            for hit in search_hits:
                contexts.append(hit["text"])

            # 4. Stream LLM tokens
            if not contexts:
                logger.warning("No context found. LLM will be queried with empty context.")

            for token in LlmService.generate_answer_stream(
                question=request.question,
                contexts=contexts,
                history=request.history,
                temperature=request.temperature
            ):
                yield token

        except Exception as e:
            logger.error(f"Error in streaming query: {e}", exc_info=True)
            yield f"An error occurred while answering your question: {str(e)}"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain"
    )

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
