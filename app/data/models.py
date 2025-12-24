# app/data/models.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    watch_history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    original_title = Column(String(500))
    overview = Column(Text)
    tagline = Column(String(500))
    genres = Column(JSON)  # Store as JSON array
    keywords = Column(Text)
    cast_data = Column(JSON)  # Store cast as JSON
    director = Column(String(255))
    
    # Media
    poster_url = Column(String(500))
    poster_path = Column(String(500))
    backdrop_path = Column(String(500))
    trailer_url = Column(String(500))
    
    # Metadata
    release_date = Column(String(50))
    year = Column(Integer, index=True)
    runtime = Column(Integer)
    budget = Column(Float)
    revenue = Column(Float)
    
    # Ratings
    vote_average = Column(Float, index=True)
    vote_count = Column(Integer)
    popularity = Column(Float, index=True)
    
    # Status
    status = Column(String(50))
    original_language = Column(String(10))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    watch_history = relationship("WatchHistory", back_populates="movie", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="movie", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_movie_year_rating', 'year', 'vote_average'),
        Index('idx_movie_popularity', 'popularity'),
    )

class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False, index=True)
    movie_id = Column(String(50), ForeignKey('movies.movie_id'), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")
    
    __table_args__ = (
        Index('idx_user_movie_rating', 'user_id', 'movie_id'),
    )

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(String(50), ForeignKey('movies.movie_id'), nullable=False, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False, index=True)
    username = Column(String(255))
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    helpful_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")
    
    __table_args__ = (
        Index('idx_movie_timestamp', 'movie_id', 'timestamp'),
    )

class WatchHistory(Base):
    __tablename__ = 'watch_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False, index=True)
    movie_id = Column(String(50), ForeignKey('movies.movie_id'), nullable=False, index=True)
    watched_at = Column(DateTime, default=datetime.utcnow, index=True)
    progress = Column(Float, default=0.0)  # Watch progress percentage
    completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="watch_history")
    movie = relationship("Movie", back_populates="watch_history")
    
    __table_args__ = (
        Index('idx_user_watched', 'user_id', 'watched_at'),
    )

class Watchlist(Base):
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False, index=True)
    movie_id = Column(String(50), ForeignKey('movies.movie_id'), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="watchlist")
    movie = relationship("Movie", back_populates="watchlist")
    
    __table_args__ = (
        Index('idx_user_movie_watchlist', 'user_id', 'movie_id'),
    )
