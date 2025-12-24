# app/data/db_postgresql.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator
from .models import Base, User, Movie, Rating, Review, WatchHistory, Watchlist

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://filmflow_user:filmflow_pass123@localhost:5432/filmflow'
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    Usage in FastAPI:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """
    Context manager for database session
    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def close_db():
    """Close database connection pool"""
    engine.dispose()

# ============ Helper Functions ============

def get_or_create_user(db: Session, user_id: str, name: str = None, email: str = None) -> User:
    """Get existing user or create new one"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, name=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_movie_by_id(db: Session, movie_id: str) -> Movie:
    """Get movie by movie_id"""
    return db.query(Movie).filter(Movie.movie_id == movie_id).first()

def get_user_ratings(db: Session, user_id: str, limit: int = None):
    """Get all ratings by a user"""
    query = db.query(Rating).filter(Rating.user_id == user_id).order_by(Rating.timestamp.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def get_movie_ratings(db: Session, movie_id: str, limit: int = None):
    """Get all ratings for a movie"""
    query = db.query(Rating).filter(Rating.movie_id == movie_id).order_by(Rating.timestamp.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def add_rating(db: Session, user_id: str, movie_id: str, rating: float) -> Rating:
    """Add or update rating"""
    existing = db.query(Rating).filter(
        Rating.user_id == user_id,
        Rating.movie_id == movie_id
    ).first()
    
    if existing:
        existing.rating = rating
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        return new_rating

def add_review(db: Session, movie_id: str, user_id: str, username: str, rating: int, review_text: str = "") -> Review:
    """Add movie review"""
    review = Review(
        movie_id=movie_id,
        user_id=user_id,
        username=username,
        rating=rating,
        review_text=review_text
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

def get_movie_reviews(db: Session, movie_id: str, limit: int = None):
    """Get reviews for a movie"""
    query = db.query(Review).filter(Review.movie_id == movie_id).order_by(Review.timestamp.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def add_to_watchlist(db: Session, user_id: str, movie_id: str) -> Watchlist:
    """Add movie to user's watchlist"""
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.movie_id == movie_id
    ).first()
    
    if not existing:
        item = Watchlist(user_id=user_id, movie_id=movie_id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    return existing

def remove_from_watchlist(db: Session, user_id: str, movie_id: str) -> bool:
    """Remove movie from watchlist"""
    item = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.movie_id == movie_id
    ).first()
    
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

def get_user_watchlist(db: Session, user_id: str):
    """Get user's watchlist"""
    return db.query(Watchlist).filter(Watchlist.user_id == user_id).order_by(Watchlist.added_at.desc()).all()

def add_watch_history(db: Session, user_id: str, movie_id: str, progress: float = 0.0, completed: bool = False) -> WatchHistory:
    """Add or update watch history"""
    history = WatchHistory(
        user_id=user_id,
        movie_id=movie_id,
        progress=progress,
        completed=completed
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_watch_history(db: Session, user_id: str, limit: int = None):
    """Get user's watch history"""
    query = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).order_by(WatchHistory.watched_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def search_movies(db: Session, query: str, limit: int = 20):
    """Search movies by title"""
    return db.query(Movie).filter(
        Movie.title.ilike(f'%{query}%')
    ).order_by(Movie.popularity.desc()).limit(limit).all()

def get_trending_movies(db: Session, limit: int = 20):
    """Get trending movies (by popularity)"""
    return db.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()

def get_top_rated_movies(db: Session, limit: int = 20, min_votes: int = 100):
    """Get top rated movies"""
    return db.query(Movie).filter(
        Movie.vote_count >= min_votes
    ).order_by(Movie.vote_average.desc()).limit(limit).all()

def get_new_releases(db: Session, limit: int = 20):
    """Get new release movies"""
    return db.query(Movie).order_by(Movie.year.desc()).limit(limit).all()

def get_movies_by_genre(db: Session, genre: str, limit: int = 20):
    """Get movies by genre"""
    # Since genres is stored as JSON, we need to use JSON operations
    return db.query(Movie).filter(
        Movie.genres.contains(genre)
    ).order_by(Movie.popularity.desc()).limit(limit).all()

def get_all_movies(db: Session, skip: int = 0, limit: int = 100):
    """Get all movies with pagination"""
    return db.query(Movie).offset(skip).limit(limit).all()

def count_movies(db: Session) -> int:
    """Count total movies in database"""
    return db.query(Movie).count()

def count_users(db: Session) -> int:
    """Count total users"""
    return db.query(User).count()

def count_ratings(db: Session) -> int:
    """Count total ratings"""
    return db.query(Rating).count()
