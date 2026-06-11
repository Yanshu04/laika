import pytest
from pathlib import Path
from app.utils.config import settings
from app.repositories.database import init_db

@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    """
    Fixture to set up a clean, separate database for the testing session
    and clean it up afterward.
    """
    # Override database path to a test-specific file
    original_path = settings.DATABASE_PATH
    test_db_path = Path(__file__).resolve().parent / "test_metadata.db"
    settings.DATABASE_PATH = test_db_path
    
    # Override uploads directory for tests
    original_upload_dir = settings.UPLOAD_DIR
    test_upload_dir = Path(__file__).resolve().parent / "test_uploads"
    settings.UPLOAD_DIR = test_upload_dir
    settings.ensure_dirs()
    
    # Initialize SQLite database
    init_db()
    
    yield
    
    # Tear down database
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass
            
    # Tear down test uploads
    if test_upload_dir.exists():
        try:
            import shutil
            shutil.rmtree(test_upload_dir)
        except Exception:
            pass
            
    settings.DATABASE_PATH = original_path
    settings.UPLOAD_DIR = original_upload_dir
