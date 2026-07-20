"""
Security utilities for FastAPI ML service
- Environment variable validation
- Rate limiting middleware
- Request validation
"""

import os
import logging
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

logger = logging.getLogger(__name__)


def validate_ml_environment_vars():
    """Validate required environment variables for ML service."""
    required_vars = [
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing = []
    warnings = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    # Warnings for weak/default passwords
    db_pass = os.getenv('DB_PASSWORD', '')
    if db_pass == 'vayuguard_pass' or len(db_pass) < 12:
        warnings.append(f'DB_PASSWORD is weak ({len(db_pass)} chars) - use strong password in production')
    
    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(f"[SECURITY] {error_msg}")
        raise RuntimeError(error_msg)
    
    for warn in warnings:
        logger.warning(f"[SECURITY] WARNING: {warn}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter: 100 requests per minute per client IP."""
    
    RATE_LIMIT = 100  # requests per minute
    WINDOW_SECONDS = 60
    
    def __init__(self, app):
        super().__init__(app)
        self.request_log = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()
        window_start = now - timedelta(seconds=self.WINDOW_SECONDS)
        
        # Clean old entries
        self.request_log[client_ip] = [
            ts for ts in self.request_log[client_ip] 
            if ts > window_start
        ]
        
        # Check rate limit
        if len(self.request_log[client_ip]) >= self.RATE_LIMIT:
            return HTTPException(
                status_code=429,
                detail={
                    "error": "Too many requests",
                    "message": f"Rate limit: {self.RATE_LIMIT} requests/minute",
                    "retry_after": self.WINDOW_SECONDS
                }
            )
        
        # Log this request
        self.request_log[client_ip].append(now)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.RATE_LIMIT - len(self.request_log[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = (now + timedelta(seconds=self.WINDOW_SECONDS)).isoformat()
        
        return response


def scan_code_for_secrets():
    """Scan common code files for hardcoded secrets."""
    
    secret_patterns = [
        'api_key',
        'secret',
        'password',
        'token',
        'credentials',
        'private_key'
    ]
    
    suspicious_files = []
    
    try:
        files_to_check = ['app_production.py', 'model_loader.py', 'run_production.py']
        
        for filename in files_to_check:
            if not os.path.exists(filename):
                continue
                
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                for i, line in enumerate(content.split('\n'), 1):
                    # Look for assignments with secret patterns
                    for pattern in secret_patterns:
                        if f'{pattern} =' in line and '=' in line:
                            # Check if value looks like a hardcoded secret
                            parts = line.split('=', 1)
                            if len(parts) > 1:
                                value = parts[1].strip()
                                if value and not value.startswith('os.getenv') and \
                                   not value.startswith('environ') and \
                                   not value.startswith(''"'"'"') and \
                                   len(value) > 10:
                                    suspicious_files.append({
                                        'file': filename,
                                        'line': i,
                                        'pattern': pattern
                                    })
        
        if suspicious_files:
            logger.warning("[SECURITY] Potential hardcoded secrets detected:")
            for item in suspicious_files:
                logger.warning(f"  - {item['file']}:{item['line']} (pattern: {item['pattern']})")
        
        return suspicious_files
        
    except Exception as e:
        logger.error(f"[SECURITY] Secret scanning failed: {e}")
        return []
