from loguru import logger
import sys
import os
from typing import Optional

def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "500 MB",
    retention: str = "10 days",
    compression: str = "zip"
) -> None:
    """
    Configure the logger with the specified settings.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file. If None, logs will only be written to stdout
        rotation: When to rotate the log file (e.g., "500 MB", "1 day")
        retention: How long to keep rotated log files
        compression: Compression format for rotated log files
    """
    # Remove default handler
    logger.remove()
    
    # Add stdout handler
    # logger.add(
    #     sys.stdout,
    #     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>dipagt</level> | <level>{level}</level> | <level>{message}</level>",
    #     level=log_level
    # )
    
    # Add file handler if log_file is specified
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logger.add(
            log_file,
            rotation=rotation,
            retention=retention,
            compression=compression,
            format="{time:YYYY-MM-DD HH:mm:ss} | dipagt | {level} | {message}",
            level=log_level
        )

def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
        The configured logger instance
    """
    return logger 