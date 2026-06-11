import sqlite3
from pathlib import Path
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Create a raw connection to the SQLite database."""
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    conn.row_factory = sqlite3.Row  # Enable access by column name
    return conn

def init_db():
    """Create database tables if they do not exist."""
    db_path = settings.DATABASE_PATH
    logger.info(f"Initializing SQLite database at {db_path}")
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT NOT NULL,
        chunk_count INTEGER NOT NULL DEFAULT 0,
        page_count INTEGER,
        created_at TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
        document_id,
        filename,
        page_number,
        chunk_index,
        text
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")
