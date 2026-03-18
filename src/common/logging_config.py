# src/common/logging_config.py
"""
Structured logging configuration for all services.
JSON logging for ELK/Datadog/CloudWatch compatibility.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict
import sys


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
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

        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user"):
            log_data["user"] = record.user
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        return json.dumps(log_data)


def setup_logging(service_name: str, log_level: str = "INFO"):
    """
    Configure structured logging for a service.

    Args:
        service_name: Name of the service (gateway, inference, training)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Set logger name
    root_logger.extra = {"service": service_name}

    return root_logger


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger with service context."""
    return logging.getLogger(name)
