from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger
from app.utils.config import settings

logger = get_logger(__name__)

class ChunkingService:
    @staticmethod
    def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Splits text into chunks of target size while attempting to split on 
        whitespace or word boundaries. Respects the overlap configuration.
        """
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Determine potential end of the chunk
            end = min(start + chunk_size, text_len)
            
            # If we're not at the very end of the text, find a boundary to split on
            if end < text_len:
                # Look for a whitespace character in the last 80 characters of the window
                boundary = text.rfind(" ", max(start, end - 80), end)
                if boundary != -1:
                    end = boundary + 1  # Include the boundary whitespace in current chunk
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # If we reached the end, terminate
            if end >= text_len:
                break
                
            # Move the start pointer back by the overlap, relative to our actual end
            start = max(start + 1, end - overlap)
            
        return chunks

    @classmethod
    def chunk_document(
        cls, 
        pages: List[Dict[str, Any]], 
        chunk_size: int = settings.CHUNK_SIZE, 
        overlap: int = settings.CHUNK_OVERLAP
    ) -> List[Dict[str, Any]]:
        """
        Chunks pages extracted from a document. Chunks each page independently 
        so that each chunk is uniquely tied to a specific page number.
        Returns a list of chunk dicts: [{"text": str, "page_number": int/None, "chunk_index": int}]
        """
        logger.info(f"Chunking document with chunk_size={chunk_size}, overlap={overlap}")
        all_chunks = []
        chunk_index = 0
        
        for page in pages:
            page_num = page.get("page_number")
            text = page.get("text", "")
            
            page_chunks = cls.split_text(text, chunk_size, overlap)
            
            for chunk_text in page_chunks:
                all_chunks.append({
                    "text": chunk_text,
                    "page_number": page_num,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                
        logger.info(f"Generated {len(all_chunks)} chunks from document.")
        return all_chunks
