"""
Utility functions for the Multilingual Text Intelligence Service.
"""
import uuid
import logging
from typing import Optional

from config import Config
from models import ProcessingMode

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """
    Generate a unique job identifier.
    
    Returns:
        Unique job ID string
    """
    return f"job-{uuid.uuid4().hex[:12]}"


def determine_processing_mode(text: str) -> ProcessingMode:
    """
    Determine whether text should be processed synchronously or asynchronously.
    
    Args:
        text: Text to evaluate
        
    Returns:
        ProcessingMode enum value
    """
    text_length = len(text)
    threshold = Config.SYNC_THRESHOLD
    
    if text_length <= threshold:
        logger.info(f"Text length {text_length} <= threshold {threshold}, using SYNC mode")
        return ProcessingMode.SYNC
    else:
        logger.info(f"Text length {text_length} > threshold {threshold}, using ASYNC mode")
        return ProcessingMode.ASYNC


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    level = log_level or Config.LOG_LEVEL
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

