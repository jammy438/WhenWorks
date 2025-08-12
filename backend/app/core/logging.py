import logging
import logging.config
import sys
from datetime import datetime
from typing import Any, Dict, Optional, List
import json
import uuid
from contextvars import ContextVar

from app.config.settings import get_settings
from logging.handlers import RotatingFileHandler

# Context variable for request correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default="")

class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        setattr(record, 'correlation_id', correlation_id.get(""))
        return True

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if present
        correlation_id_value = getattr(record, 'correlation_id', '')
        if correlation_id_value:
            log_entry["correlation_id"] = correlation_id_value
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'correlation_id'
            }:
                log_entry[key] = value
                
        return json.dumps(log_entry, default=str)

def setup_logging() -> None:
    """Configure logging based on environment settings."""
    settings = get_settings()
    
    # Choose formatter based on environment
    if settings.environment.value == "production":
        json_formatter = JSONFormatter()
        text_formatter = JSONFormatter()  # Use JSON for both in production
    else:
        # Simple formatter for development
        text_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        json_formatter = JSONFormatter()
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(text_formatter)
    console_handler.addFilter(CorrelationFilter())
    
    # Start with console handler
    handlers: List[logging.Handler] = [console_handler]
    
    # Add file handler for non-development environments
    if settings.environment.value != "development":
        file_handler = RotatingFileHandler(
            settings.log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count
        )
        file_handler.setFormatter(json_formatter)
        file_handler.addFilter(CorrelationFilter())
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Configure specific loggers
    loggers = {
        "uvicorn.access": logging.WARNING,
        "sqlalchemy.engine": logging.WARNING if settings.environment.value == "production" else logging.INFO,
        "alembic": logging.INFO,
        "app": getattr(logging, settings.log_level.upper()),
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def set_correlation_id(request_id: Optional[str] = None) -> str:
    """Set correlation ID for request tracing."""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    correlation_id.set(request_id)
    return request_id

# Logger for this module
logger = get_logger(__name__)