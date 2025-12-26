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


# ===== NEW MODELS FOR RECOMMENDATION SYSTEM =====

class UserEvent(Base):
    """
    Event tracking system - thu thập tất cả tương tác người dùng
    Hỗ trợ cả implicit (view, click) và explicit (rating, add_watchlist) events
    """
    __tablename__ = 'user_events'
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)  # UUID
    
    # Core fields
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(100), index=True)
    movie_id = Column(String(50), index=True)
    
    # Event type and metadata
    event_type = Column(String(50), nullable=False, index=True)  # view, click, play, pause, rating, search, etc.
    event_category = Column(String(20), index=True)  # implicit, explicit
    event_value = Column(Float)  # rating value, watch_time, etc.
    event_metadata = Column(JSON)  # Additional context
    
    # Context information
    device = Column(String(50))  # mobile, desktop, tablet
    platform = Column(String(50))  # web, android, ios
    user_agent = Column(Text)
    ip_address = Column(String(50))
    geo_location = Column(JSON)  # {country, city, ...}
    
    # Temporal context
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    hour_of_day = Column(Integer)  # 0-23
    day_of_week = Column(Integer)  # 0-6
    
    # Session context
    session_duration = Column(Integer)  # seconds
    page_url = Column(String(500))
    referrer = Column(String(500))
    
    # Processing flags
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_movie_event', 'movie_id', 'event_type', 'timestamp'),
        Index('idx_session', 'session_id', 'timestamp'),
    )


class UserProfile(Base):
    """
    User profile aggregated từ events - phân tích sở thích và hành vi
    """
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Preference vectors
    genre_preferences = Column(JSON)  # {genre: score}
    actor_preferences = Column(JSON)  # {actor: score}
    director_preferences = Column(JSON)  # {director: score}
    
    # Behavioral patterns
    avg_rating = Column(Float)
    rating_count = Column(Integer, default=0)
    watch_count = Column(Integer, default=0)
    avg_watch_time = Column(Float)  # minutes
    
    # Temporal patterns
    preferred_watch_hours = Column(JSON)  # {hour: count}
    preferred_watch_days = Column(JSON)  # {day: count}
    
    # Engagement metrics
    active_days = Column(Integer, default=0)
    last_active = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)
    
    # Diversity & exploration
    genre_diversity = Column(Float)  # Shannon entropy
    exploration_rate = Column(Float)  # % new genres tried
    
    # Computed features for ML
    user_embedding = Column(JSON)  # Vector representation
    cluster_id = Column(Integer)  # User clustering
    
    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    __table_args__ = (
        Index('idx_cluster', 'cluster_id'),
        Index('idx_last_active', 'last_active'),
    )


class RecommendationCache(Base):
    """
    Cache cho pre-computed recommendations - tối ưu latency
    """
    __tablename__ = 'recommendation_cache'
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    
    user_id = Column(String(255), index=True)
    context = Column(JSON)  # {device, time, page, ...}
    
    # Recommendation data
    model_type = Column(String(50), nullable=False)  # collaborative, content, hybrid
    model_version = Column(String(50))
    recommendations = Column(JSON, nullable=False)  # [{movie_id, score, reason}, ...]
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    __table_args__ = (
        Index('idx_user_model', 'user_id', 'model_type'),
        Index('idx_expires', 'expires_at'),
    )


class RecommendationFeedback(Base):
    """
    Thu thập feedback về recommendations để đánh giá và cải thiện
    """
    __tablename__ = 'recommendation_feedback'
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(100), unique=True, nullable=False)
    
    user_id = Column(String(255), nullable=False, index=True)
    movie_id = Column(String(50), nullable=False, index=True)
    recommendation_id = Column(String(100), index=True)  # Link to source recommendation
    
    # Feedback type
    feedback_type = Column(String(50), nullable=False)  # click, watch, skip, hide, like, dislike
    feedback_value = Column(Float)  # 1 for positive, -1 for negative, 0 for neutral
    
    # Context
    position = Column(Integer)  # Position in recommendation list
    model_type = Column(String(50))
    model_version = Column(String(50))
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    time_to_action = Column(Integer)  # seconds from show to action
    
    __table_args__ = (
        Index('idx_user_movie_feedback', 'user_id', 'movie_id', 'timestamp'),
        Index('idx_recommendation', 'recommendation_id'),
    )


class ModelPerformance(Base):
    """
    Track model performance metrics theo thời gian
    """
    __tablename__ = 'model_performance'
    
    id = Column(Integer, primary_key=True, index=True)
    
    model_type = Column(String(50), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    
    # Offline metrics
    precision_at_5 = Column(Float)
    precision_at_10 = Column(Float)
    recall_at_5 = Column(Float)
    recall_at_10 = Column(Float)
    ndcg_at_10 = Column(Float)
    map_score = Column(Float)
    mrr = Column(Float)
    
    # Online metrics
    ctr = Column(Float)  # Click-through rate
    watch_rate = Column(Float)  # % recommendations watched
    avg_watch_time = Column(Float)
    diversity = Column(Float)
    coverage = Column(Float)  # % of catalog recommended
    
    # Business metrics
    engagement_lift = Column(Float)
    retention_impact = Column(Float)
    
    # Metadata
    evaluation_date = Column(DateTime, default=datetime.utcnow, index=True)
    sample_size = Column(Integer)
    test_set_size = Column(Integer)
    
    notes = Column(Text)
    
    __table_args__ = (
        Index('idx_model_date', 'model_type', 'model_version', 'evaluation_date'),
    )


class ABTest(Base):
    """
    A/B testing framework cho recommendations
    """
    __tablename__ = 'ab_tests'
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(100), unique=True, nullable=False, index=True)
    
    test_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Test configuration
    control_model = Column(String(50), nullable=False)
    treatment_model = Column(String(50), nullable=False)
    traffic_split = Column(Float, default=0.5)  # % for treatment
    
    # Status
    status = Column(String(20), default='draft')  # draft, running, completed, cancelled
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    
    # Results
    control_metrics = Column(JSON)
    treatment_metrics = Column(JSON)
    statistical_significance = Column(Float)
    winner = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_status_dates', 'status', 'start_date', 'end_date'),
    )


class UserConsent(Base):
    """
    Quản lý consent và privacy cho tracking
    """
    __tablename__ = 'user_consents'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Consent flags
    tracking_consent = Column(Boolean, default=False)
    personalization_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=False)
    
    # Data retention
    data_retention_days = Column(Integer, default=365)
    anonymize_after_days = Column(Integer, default=90)
    
    # Timestamps
    consent_given_at = Column(DateTime)
    consent_updated_at = Column(DateTime)
    last_reminder_at = Column(DateTime)
    
    # IP và location khi consent
    consent_ip = Column(String(50))
    consent_location = Column(String(100))
    
    __table_args__ = (
        Index('idx_consent_date', 'consent_given_at'),
    )
