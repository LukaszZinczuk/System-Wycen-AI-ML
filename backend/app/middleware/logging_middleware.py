"""
Middleware for logging, tracing, and observability.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.logging import set_correlation_id, get_correlation_id, get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging with timing.
    Implements observability patterns for distributed tracing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
        set_correlation_id(correlation_id)
        
        # Request timing
        start_time = time.perf_counter()
        
        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-Duration-Ms"] = str(round(duration_ms, 2))
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
                exc_info=True
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics.
    In production, integrate with Prometheus/StatsD/CloudWatch.
    """
    
    # Simple in-memory metrics (use proper metrics system in production)
    request_count = 0
    request_duration_sum = 0.0
    error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            # Update metrics
            MetricsMiddleware.request_count += 1
            MetricsMiddleware.request_duration_sum += (time.perf_counter() - start_time)
            
            if response.status_code >= 400:
                MetricsMiddleware.error_count += 1
            
            return response
            
        except Exception as e:
            MetricsMiddleware.request_count += 1
            MetricsMiddleware.error_count += 1
            raise
    
    @classmethod
    def get_metrics(cls) -> dict:
        """Get current metrics snapshot."""
        avg_duration = (
            cls.request_duration_sum / cls.request_count 
            if cls.request_count > 0 else 0
        )
        error_rate = (
            cls.error_count / cls.request_count * 100
            if cls.request_count > 0 else 0
        )
        
        return {
            "total_requests": cls.request_count,
            "total_errors": cls.error_count,
            "error_rate_percent": round(error_rate, 2),
            "average_duration_seconds": round(avg_duration, 4),
        }
