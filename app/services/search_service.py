from typing import List, Dict, Any
from app.utils.config import settings
from app.utils.logger import get_logger
from app.services.embedding_service import EmbeddingService
from app.repositories.database import get_db_connection

logger = get_logger(__name__)

class SearchService:
    @staticmethod
    def _semantic_search(
        query: str, 
        limit: int = 50, 
        score_threshold: float = settings.SCORE_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search in ChromaDB."""
        hits = []
        try:
            query_vector = EmbeddingService.get_embeddings([query])[0]
            collection = EmbeddingService.get_collection()
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit
            )
            
            if not results or not results.get("ids") or len(results["ids"][0]) == 0:
                return []
                
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
            
            for idx in range(len(ids)):
                dist = distances[idx]
                if dist > score_threshold:
                    continue
                    
                meta = metadatas[idx]
                page_val = meta.get("page_number")
                page_num = page_val if page_val != -1 else None
                
                doc_id = meta.get("document_id", "Unknown")
                chunk_index = meta.get("chunk_index", 0)
                
                hits.append({
                    "id": ids[idx],
                    "document_id": doc_id,
                    "chunk_index": chunk_index,
                    "text": documents[idx],
                    "filename": meta.get("filename", "Unknown"),
                    "page_number": page_num,
                    "score": dist
                })
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            
        return hits

    @staticmethod
    def _keyword_search(query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Perform lexical keyword search in SQLite FTS5 index."""
        cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in query)
        terms = [t for t in cleaned.split() if t]
        if not terms:
            return []
        
        fts_query = " OR ".join(terms)
        
        hits = []
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT document_id, filename, page_number, chunk_index, text, rank
                    FROM document_chunks_fts
                    WHERE document_chunks_fts MATCH ?
                    ORDER BY rank ASC
                    LIMIT ?
                    """,
                    (fts_query, limit)
                )
                rows = cursor.fetchall()
                for row in rows:
                    page_val = row["page_number"]
                    page_num = page_val if page_val != -1 else None
                    hits.append({
                        "id": f"{row['document_id']}_{row['chunk_index']}",
                        "document_id": row["document_id"],
                        "chunk_index": row["chunk_index"],
                        "text": row["text"],
                        "filename": row["filename"],
                        "page_number": page_num,
                        "score": float(row["rank"])
                    })
        except Exception as e:
            logger.error(f"FTS5 keyword search failed: {e}")
            
        return hits

    @classmethod
    def search(
        cls, 
        query: str, 
        top_k: int = settings.TOP_K,
        score_threshold: float = settings.SCORE_THRESHOLD,
        search_mode: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Executes a vector, keyword, or hybrid search based on the mode.
        """
        logger.info(f"Search triggered: query='{query}', mode={search_mode}, top_k={top_k}")
        
        search_mode = search_mode.lower()
        
        if search_mode == "semantic":
            return cls._semantic_search(query, limit=top_k, score_threshold=score_threshold)
            
        elif search_mode == "keyword":
            return cls._keyword_search(query, limit=top_k)
            
        elif search_mode == "hybrid":
            candidate_limit = max(top_k * 3, 30)
            semantic_hits = cls._semantic_search(query, limit=candidate_limit, score_threshold=score_threshold)
            keyword_hits = cls._keyword_search(query, limit=candidate_limit)
            
            semantic_ranks = { (h["document_id"], h["chunk_index"]): idx + 1 for idx, h in enumerate(semantic_hits) }
            keyword_ranks = { (h["document_id"], h["chunk_index"]): idx + 1 for idx, h in enumerate(keyword_hits) }
            
            all_unique_hits = {}
            for h in semantic_hits:
                key = (h["document_id"], h["chunk_index"])
                all_unique_hits[key] = h
            for h in keyword_hits:
                key = (h["document_id"], h["chunk_index"])
                if key not in all_unique_hits:
                    all_unique_hits[key] = h
            
            rrf_scores = {}
            k = 60.0
            for key in all_unique_hits:
                score = 0.0
                if key in semantic_ranks:
                    score += 1.0 / (k + semantic_ranks[key])
                if key in keyword_ranks:
                    score += 1.0 / (k + keyword_ranks[key])
                rrf_scores[key] = score
                
            sorted_keys = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
            
            fused_hits = []
            for key in sorted_keys[:top_k]:
                hit = all_unique_hits[key]
                hit["rrf_score"] = rrf_scores[key]
                fused_hits.append(hit)
                
            logger.info(f"Hybrid search returned {len(fused_hits)} fused hits using RRF.")
            return fused_hits
            
        else:
            logger.warning(f"Unknown search mode: {search_mode}. Falling back to hybrid.")
            return cls.search(query, top_k, score_threshold, search_mode="hybrid")
