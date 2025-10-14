import logging
import sys
from datetime import datetime


def setup_logging(level: str = "INFO") -> None:
    """Configure logging"""
    
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            level = record.levelname
            message = record.getMessage()
            return f"{timestamp} - [{level}] - {message}"
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[handler]
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)