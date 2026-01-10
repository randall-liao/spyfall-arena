import sys

from loguru import logger


def setup_console_logging(log_level: str = "INFO") -> None:
    """Configure Loguru console output with color-coded formatting."""
    logger.remove()

    log_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=log_format,
    )
