import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Path for log files
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "laika.log"

def get_logger(name: str) -> logging.Logger:
    """Get a standardized logger instance with file and stdout handlers."""
    logger = logging.getLogger(name)
    
    # If logger already has handlers, don't add them again
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Stream Handler (Stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # File Handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to set up file logger: {e}", file=sys.stderr)
        
    return logger
