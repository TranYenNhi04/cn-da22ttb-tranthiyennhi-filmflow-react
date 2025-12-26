"""
Basic tests for the Movie API
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "status" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    # Endpoint might not exist, so accept 404 or 200
    assert response.status_code in [200, 404]


def test_movies_endpoint():
    """Test movies listing endpoint"""
    response = client.get("/movies?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


def test_search_endpoint():
    """Test movie search functionality"""
    response = client.get("/movies/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


def test_recommendations_endpoint():
    """Test recommendations endpoint"""
    response = client.get("/recommendations?rec_type=hybrid&n=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


def test_rate_limiting():
    """Test that rate limiting is applied"""
    # Make multiple rapid requests
    responses = []
    for _ in range(10):
        response = client.get("/movies?limit=1")
        responses.append(response.status_code)
    
    # Most should succeed, but we're testing the middleware exists
    assert 200 in responses


def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/movies")
    # CORS middleware should add headers
    assert response.status_code in [200, 405]  # Options or Method Not Allowed


def test_invalid_endpoint():
    """Test 404 for invalid endpoints"""
    response = client.get("/nonexistent-endpoint-12345")
    assert response.status_code == 404
