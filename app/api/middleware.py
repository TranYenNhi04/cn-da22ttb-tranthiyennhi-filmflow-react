"""
Rate limiting middleware for API protection
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import os

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 500):
        super().__init__(app)
        self.requests_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE', requests_per_minute))
        self.request_counts = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old entries
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip] 
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute."
            )
        
        # Add current request
        self.request_counts[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        return response
