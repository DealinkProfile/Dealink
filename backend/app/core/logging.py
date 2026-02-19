# backend/app/core/logging.py
"""
Structured logging with loguru
Replaces stdlib logging with loguru for better output, JSON support, and filtering.
"""
import sys
import logging
from loguru import logger

# ============================================================
# Intercept stdlib logging → redirect to loguru
# ============================================================

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging calls and redirect them to loguru.
    This ensures that FastAPI, uvicorn, and any library using stdlib logging
    all go through loguru's formatting/filtering.
    """
    def emit(self, record: logging.LogRecord):
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the log message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: str = "INFO"):
    """
    Setup loguru-based structured logging.
    
    Features:
    - Colored console output with timestamps
    - Structured format: timestamp | level | module | message
    - Intercepts all stdlib logging (FastAPI, uvicorn, serpapi, etc.)
    - Filters noisy libraries
    """
    # Remove default loguru handler
    logger.remove()
    
    # Add custom handler with structured format
    log_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Wrap sys.stdout to handle encoding on Windows (cp1252 → utf-8)
    import io
    if hasattr(sys.stdout, "buffer"):
        sink = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    else:
        sink = sys.stdout

    logger.add(
        sink,
        format=log_format,
        level=log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=False,  # Don't show variable values in tracebacks (security)
    )
    
    # Intercept stdlib logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Suppress noisy loggers
    for noisy_logger in ["uvicorn.access", "httpcore", "httpx", "hpack"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    
    logger.info(f"Loguru logging initialized at {log_level} level")
    return logger
