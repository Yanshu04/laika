import os
from pathlib import Path

# Base directory of the project (y:\Local AI Knowledge Assistant\laika)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    # Directories
    DATA_DIR: Path = Path(os.getenv("LAIKA_DATA_DIR", str(BASE_DIR / "data")))
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    CHROMA_DIR: Path = DATA_DIR / "chroma"
    
    # SQLite Database
    DATABASE_URL: str = os.getenv("LAIKA_DATABASE_URL", f"sqlite:///{DATA_DIR}/metadata.db")
    DATABASE_PATH: Path = DATA_DIR / "metadata.db"
    
    # LLM (Ollama)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    
    # Search / Retrieval
    TOP_K: int = int(os.getenv("LAIKA_TOP_K", "5"))
    SCORE_THRESHOLD: float = float(os.getenv("LAIKA_SCORE_THRESHOLD", "0.42"))
    CHUNK_SIZE: int = int(os.getenv("LAIKA_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("LAIKA_CHUNK_OVERLAP", "100"))

    # Backend Server
    BACKEND_PORT: int = int(os.getenv("LAIKA_BACKEND_PORT", "8080"))

    def ensure_dirs(self):
        """Ensure all required data directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_dirs()
