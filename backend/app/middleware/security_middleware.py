"""
Security middleware implementing OWASP best practices.
Includes rate limiting, input sanitization, and security headers.
"""
import time
import re
import hashlib
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse and DDoS attacks.
    Implements token bucket algorithm per IP/user.
    
    OWASP: API4:2019 - Lack of Resources & Rate Limiting
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        excluded_paths: List[str] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json"]
        
        # In-memory storage (use Redis in production)
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client (IP + optional user)."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Include user ID if authenticated
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            user_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            return f"{client_ip}:{user_hash}"
        
        return client_ip
    
    def _clean_old_requests(self, client_id: str, window_seconds: int):
        """Remove requests older than the time window."""
        cutoff = time.time() - window_seconds
        self.request_counts[client_id] = [
            ts for ts in self.request_counts[client_id] if ts > cutoff
        ]
    
    def _is_rate_limited(self, client_id: str) -> tuple[bool, Optional[int]]:
        """Check if client is rate limited. Returns (is_limited, retry_after)."""
        now = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_id, 3600)  # 1 hour window
        
        requests = self.request_counts[client_id]
        
        # Check per-minute limit
        minute_ago = now - 60
        requests_last_minute = sum(1 for ts in requests if ts > minute_ago)
        
        if requests_last_minute >= self.requests_per_minute:
            retry_after = int(60 - (now - min(ts for ts in requests if ts > minute_ago)))
            return True, max(1, retry_after)
        
        # Check per-hour limit
        hour_ago = now - 3600
        requests_last_hour = sum(1 for ts in requests if ts > hour_ago)
        
        if requests_last_hour >= self.requests_per_hour:
            retry_after = int(3600 - (now - min(ts for ts in requests if ts > hour_ago)))
            return True, max(1, retry_after)
        
        return False, None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        client_id = self._get_client_identifier(request)
        is_limited, retry_after = self._is_rate_limited(client_id)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Content-Type": "application/json"
                }
            )
        
        # Record this request
        self.request_counts[client_id].append(time.time())
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len([
            ts for ts in self.request_counts[client_id] if ts > time.time() - 60
        ])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    OWASP: Security Misconfiguration, XSS Prevention
    """
    
    # Paths that need relaxed CSP for Swagger UI
    SWAGGER_PATHS = ["/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy - relaxed for Swagger UI paths
        if any(request.url.path.startswith(path) for path in self.SWAGGER_PATHS):
            # Swagger UI needs to load from CDN
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "frame-ancestors 'none'"
            )
        else:
            # Strict CSP for other endpoints
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "frame-ancestors 'none'"
            )
        
        # Strict Transport Security (for HTTPS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for input sanitization and validation.
    
    OWASP: Injection Prevention
    """
    
    # Patterns that might indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r"<script[^>]*>",  # Script tags
        r"javascript:",    # JavaScript protocol
        r"on\w+\s*=",      # Event handlers
        r"--",             # SQL comment
        r";\s*DROP\s+",    # SQL injection
        r"UNION\s+SELECT", # SQL injection
        r"\$\{",           # Template injection
        r"\{\{",           # Template injection
    ]
    
    def __init__(self, app, block_suspicious: bool = False):
        super().__init__(app)
        self.block_suspicious = block_suspicious
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SUSPICIOUS_PATTERNS
        ]
    
    def _check_suspicious(self, value: str) -> bool:
        """Check if value contains suspicious patterns."""
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check query parameters
        for key, value in request.query_params.items():
            if self._check_suspicious(value):
                logger.warning(
                    f"Suspicious input detected in query param '{key}': {value[:100]}"
                )
                if self.block_suspicious:
                    return Response(
                        content='{"detail": "Invalid input detected"}',
                        status_code=status.HTTP_400_BAD_REQUEST,
                        headers={"Content-Type": "application/json"}
                    )
        
        # Check headers for suspicious content
        suspicious_headers = ["X-Forwarded-For", "User-Agent", "Referer"]
        for header in suspicious_headers:
            value = request.headers.get(header, "")
            if self._check_suspicious(value):
                logger.warning(
                    f"Suspicious input detected in header '{header}': {value[:100]}"
                )
        
        return await call_next(request)


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input."""
    # Truncate to max length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Basic HTML encoding for special characters
    value = value.replace('<', '&lt;').replace('>', '&gt;')
    
    return value.strip()
