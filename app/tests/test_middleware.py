"""
Tests for rate limiting middleware
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.middleware import RateLimitMiddleware


def test_rate_limit_middleware():
    """Test rate limiting middleware functionality"""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=5)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "ok"}
    
    client = TestClient(app)
    
    # First 5 requests should succeed
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()
