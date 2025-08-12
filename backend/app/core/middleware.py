import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, set_correlation_id

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())[:8]
        set_correlation_id(correlation_id)
        
        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "process_time": round(process_time, 4),
                    "error": str(e),
                }
            )
            raise
        
        # Log request completion
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
            }
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

def setup_middleware(app: FastAPI) -> None:
    """Set up logging middleware."""
    app.add_middleware(LoggingMiddleware)