"""
Centralized logging configuration for the application.
"""
import logging
import sys
from backend.settings import settings


def setup_logging():
    """
    Configure application logging with appropriate level and format.

    This should be called once at application startup.
    """
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Suppress noisy third-party loggers
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
