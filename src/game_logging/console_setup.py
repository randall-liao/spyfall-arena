import sys
from loguru import logger

def setup_console_logging(log_level: str = "INFO") -> None:
    """
    Configures the console logging for the application.

    Removes default handlers and adds a formatted handler to stderr.

    Args:
        log_level: The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
    """
    logger.remove()

    log_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=log_format,
    )
