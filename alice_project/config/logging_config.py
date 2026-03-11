"""
Centralized logging configuration for Alice MLOps project
Supports structured logging with JSON output and console formatting
"""

import logging
import logging.handlers
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing and aggregation"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Format logs with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        format_str = (
            f"{color}[%(asctime)s]{self.RESET} "
            f"%(levelname)s - %(name)s - %(message)s"
        )
        
        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def setup_logging(
    name: Optional[str] = None,
    level: str = "INFO",
    log_dir: Optional[str] = None,
    use_console: bool = True,
    use_file: bool = True,
    json_format: bool = False,
) -> logging.Logger:
    """
    Setup logging with both console and file handlers
    
    Args:
        name: Logger name (defaults to root logger)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to ./logs)
        use_console: Enable console output
        use_file: Enable file output
        json_format: Use JSON format for files (vs text format)
    
    Returns:
        Configured logger instance
    
    Example:
        logger = setup_logging(name=__name__)
        logger.info("Application started", extra={"user_id": 123})
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if needed
    if use_file:
        log_dir = Path(log_dir or "./logs")
        log_dir.mkdir(exist_ok=True, parents=True)
    
    # Console handler
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        formatter = ColoredFormatter() if not json_format else JSONFormatter()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler - rotating file
    if use_file:
        log_file = log_dir / f"{name or 'app'}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        
        formatter = JSONFormatter() if json_format else logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance
    
    If logger doesn't have handlers, inherit from root logger
    
    Usage:
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    if name is None:
        return logging.getLogger(name)  # Return root logger
    
    logger = logging.getLogger(name)
    
    # If logger has no handlers, it will inherit from root logger
    # Make sure propagate is True (default)
    logger.propagate = True
    
    return logger


# Default setup on import
_log_level = os.getenv("LOG_LEVEL", "INFO")
_json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"
_log_dir = os.getenv("LOG_DIR", "./logs")

root_logger = setup_logging(
    name=None,
    level=_log_level,
    log_dir=_log_dir,
    json_format=_json_logs,
)