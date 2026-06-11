from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import document_routes, chat_routes
from app.repositories.database import init_db
from app.services.llm_service import LlmService
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="Local AI Knowledge Assistant (LAIKA) API",
    description="Offline API for document parsing, vector indexing, and local Q&A grounding using Ollama.",
    version="1.0.0"
)

# Set up CORS middleware to allow Streamlit UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to Streamlit's specific URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event: Initialize Database
@app.on_event("startup")
def startup_event():
    logger.info("Starting up LAIKA backend...")
    settings.ensure_dirs()
    init_db()
    
    # Check if Ollama is running
    ollama_connected = LlmService.test_connection()
    if ollama_connected:
        logger.info(f"Connected to local Ollama service at {settings.OLLAMA_BASE_URL}")
    else:
        logger.warning(
            f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}. "
            "Please ensure the service is running so Q&A functions work."
        )

# Register routers
app.include_router(document_routes.router)
app.include_router(chat_routes.router)

@app.get("/")
def read_root():
    """Root route returning service info and system statuses."""
    ollama_ok = LlmService.test_connection()
    return {
        "app": "Local AI Knowledge Assistant (LAIKA)",
        "version": "1.0.0",
        "status": "healthy",
        "configuration": {
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "ollama_model": settings.OLLAMA_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
        },
        "services": {
            "ollama_connected": ollama_ok
        }
    }
