from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class DocumentMetadata(BaseModel):
    id: str = Field(..., description="Unique ID (UUID) of the document")
    filename: str = Field(..., description="Original name of the file")
    file_path: str = Field(..., description="Absolute path on local disk")
    status: str = Field(..., description="Processing status: UPLOADING, INDEXED, ERROR")
    chunk_count: int = Field(0, description="Number of parsed text chunks")
    page_count: Optional[int] = Field(None, description="Number of pages in the document")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to ask the knowledge assistant")
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Conversation history")
    top_k: Optional[int] = Field(default=None, description="Number of retrieved chunks")
    score_threshold: Optional[float] = Field(default=None, description="Retrieval score threshold")
    temperature: Optional[float] = Field(default=None, description="LLM temperature override")
    search_mode: Optional[str] = Field(default=None, description="Search mode: semantic, keyword, or hybrid")

class SourceCitation(BaseModel):
    filename: str = Field(..., description="Name of the source file")
    page_number: Optional[int] = Field(None, description="Page number of the citation (1-indexed, PDF only)")
    text_snippet: str = Field(..., description="Matching text segment used to answer the question")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="LLM generated answer")
    sources: List[SourceCitation] = Field(default_factory=list, description="List of document segments referenced")
