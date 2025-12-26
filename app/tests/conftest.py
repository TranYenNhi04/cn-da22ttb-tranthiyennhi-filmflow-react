"""
Shared fixtures for tests
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def test_db():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_movie():
    """Sample movie data for testing"""
    return {
        "id": 1,
        "title": "Test Movie",
        "year": 2023,
        "vote_average": 8.5,
        "genres": ["Action", "Drama"]
    }


@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "userId": "test_user_123",
        "name": "Test User",
        "email": "test@example.com"
    }
