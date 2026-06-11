from typing import Dict, Any, List, Optional
from app.models.models import QueryResponse, SourceCitation
from app.services.search_service import SearchService
from app.services.llm_service import LlmService
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RagPipeline:
    @classmethod
    def answer_question(
        cls, 
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        temperature: Optional[float] = None,
        search_mode: Optional[str] = None
    ) -> QueryResponse:
        """
        Executes the full Retrieval-Augmented Generation (RAG) pipeline:
        1. Decontextualize query using chat history if present
        2. Retrieve similar chunks based on query and search mode
        3. Compile contexts and source citations
        4. Call local LLM with prompt (including history and temperature)
        5. Return response with answer and citations
        """
        logger.info(f"RAG Pipeline triggered for question: '{question}'")
        
        # Resolve defaults
        tk = top_k if top_k is not None else settings.TOP_K
        st = score_threshold if score_threshold is not None else settings.SCORE_THRESHOLD
        sm = search_mode if search_mode is not None else "hybrid"
        
        # 1. Rewrite query if history is present
        search_query = question
        if history:
            logger.info("Conversational history present. Attempting query rewriting...")
            search_query = LlmService.rewrite_query(question, history)
            
        # 2. Retrieve top similar chunks
        search_hits = []
        try:
            search_hits = SearchService.search(query=search_query, top_k=tk, score_threshold=st, search_mode=sm)
        except Exception as e:
            logger.error(f"Error during document search: {e}")
            return QueryResponse(
                answer="I was unable to search documents because the search index is uninitialized or not loaded.",
                sources=[]
            )
            
        # 3. Extract contexts and format citations
        contexts = []
        sources = []
        seen_citations = set()
        
        for hit in search_hits:
            text = hit["text"]
            filename = hit["filename"]
            page_num = hit["page_number"]
            
            contexts.append(text)
            
            # Format source citation key
            citation_key = (filename, page_num)
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                sources.append(
                    SourceCitation(
                        filename=filename,
                        page_number=page_num,
                        text_snippet=text
                    )
                )
        
        # 4. Request answer from local LLM
        if not contexts:
            logger.warning("No context found. LLM will be queried with empty context.")
            
        answer = LlmService.generate_answer(
            question=question, 
            contexts=contexts, 
            history=history, 
            temperature=temperature
        )
        
        # 5. Form response
        response = QueryResponse(
            answer=answer,
            sources=sources
        )
        
        logger.info("RAG Pipeline successfully completed.")
        return response
