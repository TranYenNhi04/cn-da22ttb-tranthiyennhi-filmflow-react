# app/api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import os
import re
from functools import lru_cache
from datetime import datetime, timedelta
import asyncio
import concurrent.futures
import time

# Controllers
from app.controllers.movie_controller import MovieController
from app.controllers.recommendation_controller import RecommendationController

# Middleware
from app.api.middleware import RateLimitMiddleware

# Database
try:
    from app.data.db_postgresql import (
        get_db, 
        get_or_create_user,
        get_user_ratings,
        get_user_watchlist,
        get_watch_history,
        add_to_watchlist,
        remove_from_watchlist,
        add_watch_history
    )
    from app.data.models import User, Movie, Rating, Review, WatchHistory, Watchlist
    USE_POSTGRESQL = True
    print("✅ Using PostgreSQL for user data")
except Exception as e:
    print(f"⚠️ PostgreSQL not available: {e}")
    USE_POSTGRESQL = False

# Utils
try:
    from app.utils.tmdb_api import get_movie_poster, get_movie_data
    TMDB_AVAILABLE = True
except:
    TMDB_AVAILABLE = False
    get_movie_poster = None
    get_movie_data = None

try:
    from app.utils.youtube_api import get_youtube_video
    YOUTUBE_AVAILABLE = True
except:
    YOUTUBE_AVAILABLE = False
    get_youtube_video = None

# FastAPI
app = FastAPI(title="Movie Recommendation API")

# Configure CORS with environment variables
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:80').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add rate limiting
app.add_middleware(RateLimitMiddleware)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

movie_controller = MovieController(data_dir=DATA_DIR)
recommendation_controller = RecommendationController(data_dir=DATA_DIR)

# In-memory cache for recommendations (expires after 5 minutes)
recommendation_cache = {}
CACHE_DURATION = 300  # 5 minutes in seconds

# Pre-computed popular movies cache (updated every 10 minutes)
popular_movies_cache = {"data": [], "timestamp": 0}
POPULAR_CACHE_DURATION = 600  # 10 minutes

# Helper functions for optimization
def get_popular_movies_fast(user_id=None, n=10):
    """Get popular movies with caching to avoid repeated dataframe operations"""
    global popular_movies_cache
    current_time = time.time()
    
    # Check if popular movies cache is valid
    if (popular_movies_cache["data"] and 
        current_time - popular_movies_cache["timestamp"] < POPULAR_CACHE_DURATION):
        movies = popular_movies_cache["data"]
    else:
        # Refresh popular movies cache
        popular_df = movie_controller.movie_model.movies_df.sort_values(
            'vote_average', ascending=False
        ).head(100)  # Cache top 100
        popular_movies_cache["data"] = popular_df.to_dict('records')
        popular_movies_cache["timestamp"] = current_time
        movies = popular_movies_cache["data"]
    
    # Shuffle based on user_id for personalization
    if user_id and movies:
        import random
        seed = abs(hash(user_id)) % 100000
        random.seed(seed)
        shuffled = movies.copy()
        random.shuffle(shuffled)
        return shuffled[:n]
    
    return movies[:n]

def enrich_movies_parallel(movies):
    """Enrich movies with posters using parallel processing for speed"""
    if not movies:
        return []
    
    def enrich_movie(movie):
        """Enrich a single movie with poster and placeholder"""
        # Priority 1: Use existing poster_url from movie data
        if movie.get("poster_url") and movie["poster_url"].startswith("http"):
            return movie
        
        # Priority 2: Check for poster_path field (TMDB format)
        if movie.get("poster_path"):
            poster_path = movie["poster_path"]
            if poster_path.startswith("/"):
                movie["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
                return movie
            elif poster_path.startswith("http"):
                movie["poster_url"] = poster_path
                return movie
        
        # Priority 3: Try TMDB API if available and we have a title
        title = movie.get('title', '')
        year = movie.get('year')
        
        if TMDB_AVAILABLE and title:
            try:
                tmdb_data = get_movie_data(title, year)
                if tmdb_data and tmdb_data.get('poster_url'):
                    movie['poster_url'] = tmdb_data['poster_url']
                    # Also save video URL if available
                    if tmdb_data.get('video_url'):
                        movie['video_url'] = tmdb_data['video_url']
                    return movie
            except Exception as e:
                # Silently fail and use placeholder
                pass
        
        # Priority 4: Use generic placeholder as last resort
        seed = movie.get('id') or movie.get('movieId') or movie.get('title', 'movie')
        t = str(seed).lower().replace(' ', '')
        movie["poster_url"] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
        
        # Lazy load video URL when needed (not on list view)
        if not movie.get("video_url"):
            movie["video_url"] = None
        
        return movie
    
    # Process in parallel using thread pool (fast for I/O-bound operations)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        enriched = list(executor.map(enrich_movie, movies))
    
    return enriched

# Pydantic models for request bodies
class ReviewRequest(BaseModel):
    rating: int
    review_text: str = ""
    username: Optional[str] = "Anonymous"


class CommentRequest(BaseModel):
    userId: str
    comment: str


class UserRequest(BaseModel):
    userId: str
    metadata: Optional[str] = None


class ItemRequest(BaseModel):
    movieId: int
    title: Optional[str] = None
    metadata: Optional[str] = None


class InteractionRequest(BaseModel):
    userId: str
    movieId: int
    action: str  # view, click, rating, like, dislike
    rating: Optional[float] = None


class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

# Routes
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/movies/search")
def search_movies(q: str, year_min: Optional[int] = None, year_max: Optional[int] = None, 
                  rating_min: Optional[float] = None, rating_max: Optional[float] = None,
                  genre: Optional[str] = None, limit: int = 20, user_id: Optional[str] = None):
    """Advanced search with filters: year range, rating range, genre"""
    try:
        results = movie_controller.search_movies(q)
        
        # Apply filters
        if year_min is not None:
            results = [m for m in results if m.get('year', 0) >= year_min]
        if year_max is not None:
            results = [m for m in results if m.get('year', 9999) <= year_max]
        if rating_min is not None:
            results = [m for m in results if m.get('vote_average', 0) >= rating_min]
        if rating_max is not None:
            results = [m for m in results if m.get('vote_average', 0) <= rating_max]
        if genre:
            genre_lower = genre.lower()
            results = [m for m in results if genre_lower in str(m.get('genres', '')).lower()]
        
        results = results[:limit]
        
        # NOTE: Search history tracking disabled (requires migration to PostgreSQL)
        
        for movie in results:
            title = movie.get("title", "")
            year = movie.get("year")
            
            # Lấy YouTube video từ API nếu có thể
            if YOUTUBE_AVAILABLE:
                yt_video = get_youtube_video(title, year)
                if yt_video:
                    movie["video_url"] = yt_video
            
            # Lấy poster từ TMDB nếu có thể
            if not movie.get("poster_url") and TMDB_AVAILABLE:
                tmdb_poster = get_movie_poster(title)
                if tmdb_poster:
                    movie["poster_url"] = tmdb_poster
            
            # Nếu không có poster, dùng placeholder
            if not movie.get("poster_url"):
                seed = movie.get('id') or title
                movie["poster_url"] = f"https://picsum.photos/seed/{str(seed).lower().replace(' ', '')[:20] or 'movie'}/300/450"
        
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movies/autocomplete")
def autocomplete_movies(q: str, n: int = 10):
    try:
        results = movie_controller.autocomplete(q, n=n)
        # enrich minimal fields if needed
        for movie in results:
            if not movie.get('poster_url') and TMDB_AVAILABLE:
                try:
                    movie['poster_url'] = get_movie_poster(movie.get('title', '')) or movie.get('poster_url')
                except Exception:
                    pass
            if not movie.get('poster_url'):
                seed = movie.get('id') or movie.get('title','')
                t = (str(seed) or '').lower().replace(' ', '')
                movie['poster_url'] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TRENDING & NEW RELEASES ====================

@app.get("/movies/trending")
def get_trending_movies(limit: int = 20):
    """Lấy phim trending với full movie data để tránh nhiều API calls."""
    try:
        trend_data = movie_controller.movie_model.get_trending_movies(limit=limit * 2)  # Fetch more to account for deduplication
        
        # Deduplication by movie ID
        seen_ids = set()
        unique_movies = []
        
        # Normalize field names and ensure all movies have required fields
        for movie in trend_data:
            # Ensure id field exists (normalize movieId to id)
            if 'movieId' in movie and 'id' not in movie:
                movie['id'] = movie['movieId']
            elif 'id' not in movie and 'movieId' not in movie:
                # Try to get from other fields as fallback
                continue
            
            # Check for duplicates
            movie_id = movie.get('id')
            if movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
                
            # Ensure poster_url
            if not movie.get('poster_url') and not movie.get('poster_path'):
                # Generate placeholder
                seed = movie.get('id') or movie.get('movieId') or movie.get('title', '')
                t = (str(seed) or '').lower().replace(' ', '')
                movie['poster_url'] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
            
            unique_movies.append(movie)
            if len(unique_movies) >= limit:
                break
        
        return {"movies": unique_movies}
    except Exception as e:
        return {"movies": []}


@app.get("/movies/new-releases")
def get_new_releases(limit: int = 20):
    """Lấy phim mới nhất - Vieon style."""
    try:
        movies = movie_controller.movie_model.get_new_releases(limit=limit * 2)  # Fetch more to account for deduplication
        
        # Deduplication by movie ID
        seen_ids = set()
        unique_movies = []
        
        # Ensure all movies have poster_url
        for movie in movies:
            # Check for duplicates
            movie_id = movie.get('id') or movie.get('movieId')
            if not movie_id or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            
            # Ensure id field
            if 'id' not in movie and 'movieId' in movie:
                movie['id'] = movie['movieId']
            
            if not movie.get('poster_url'):
                title = movie.get('title', '')
                year = movie.get('year')
                if TMDB_AVAILABLE:
                    poster = get_movie_poster(title)
                    if poster:
                        movie['poster_url'] = poster
            
            if not movie.get('poster_url'):
                seed = movie.get('id') or movie.get('title','')
                t = (str(seed) or '').lower().replace(' ', '')
                movie['poster_url'] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
            
            unique_movies.append(movie)
            if len(unique_movies) >= limit:
                break
        
        return {"movies": unique_movies}
    except Exception as e:
        return {"movies": []}

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = movie_controller.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Add trailer and poster on-demand
    title = movie.get("title", "")
    year = movie.get("year")
    
    # Lấy video từ TMDB trước (nhanh hơn)
    if TMDB_AVAILABLE and get_movie_data:
        tmdb_data = get_movie_data(title, year)
        if tmdb_data:
            if tmdb_data.get("video_url"):
                movie["video_url"] = tmdb_data["video_url"]
            if not movie.get("poster_url") and tmdb_data.get("poster_url"):
                movie["poster_url"] = tmdb_data["poster_url"]
    
    # Fallback YouTube nếu không có video
    if not movie.get("video_url") and YOUTUBE_AVAILABLE:
        yt_video = get_youtube_video(title, year)
        if yt_video:
            movie["video_url"] = yt_video
    
    # Poster placeholder
    if not movie.get("poster_url"):
        seed = movie.get('id') or title
        movie["poster_url"] = f"https://picsum.photos/seed/{str(seed).lower().replace(' ', '')[:20] or 'movie'}/300/450"
    
    return movie

# NOTE: review endpoint implemented below using Pydantic `ReviewRequest`

@app.get("/movies/{movie_id}/trailer")
def get_movie_trailer(movie_id: int):
    movie = movie_controller.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    title = movie.get("title", "")
    year = movie.get("year")
    
    # Lấy YouTube video từ API nếu có thể
    video_url = None
    if YOUTUBE_AVAILABLE:
        yt_video = get_youtube_video(title, year)
        if yt_video:
            # Nếu youtube util trả về một "search embed" (listType=search) or a plain search URL,
            # đó thường dẫn đến iframe "video unavailable". Trong trường hợp đó, thử TMDB để lấy video id.
            low = yt_video.lower()
            is_search_embed = ('listtype=search' in low) or ('/results?search_query=' in low) or ('list=' in low and 'embed?listtype' in low)
            if not is_search_embed:
                video_url = yt_video
            else:
                # Try TMDB for a direct video id/watch url
                if TMDB_AVAILABLE and get_movie_data:
                    try:
                        tmdb_data = get_movie_data(title, year)
                        if tmdb_data and tmdb_data.get('video_url'):
                            # TMDB returns a watch URL like https://www.youtube.com/watch?v=XXXXX
                            watch = tmdb_data.get('video_url')
                            # convert to embed
                            try:
                                from urllib.parse import urlparse, parse_qs
                                parsed = urlparse(watch)
                                if parsed.hostname and ('youtube.com' in parsed.hostname or 'youtu.be' in parsed.hostname):
                                    if 'v=' in parsed.query:
                                        vid = parse_qs(parsed.query).get('v', [None])[0]
                                    else:
                                        # youtu.be short link
                                        vid = parsed.path.lstrip('/')
                                    if vid:
                                        video_url = f"https://www.youtube-nocookie.com/embed/{vid}"
                            except Exception:
                                # fallback: do not set video_url
                                video_url = None
                    except Exception:
                        # TMDB lookup failed or raised; don't let this break trailer lookup
                        video_url = None
                # If still no direct video, leave video_url as None so frontend shows poster + open-YouTube button
    
    # Lấy poster từ TMDB nếu có thể
    poster_url = movie.get("poster_url")
    if not poster_url and TMDB_AVAILABLE:
        tmdb_poster = get_movie_poster(title)
        if tmdb_poster:
            poster_url = tmdb_poster
    
    if not poster_url:
        seed = movie.get('id') or movie_id or title
        poster_url = f"https://picsum.photos/seed/{str(seed).lower().replace(' ', '')[:20] or 'movie'}/300/450"

    return {"movie_id": movie_id, "title": title, "video_url": video_url, "poster_url": poster_url}

@app.get("/recommendations")
def get_recommendations(
    rec_type: str, user_id: Optional[str] = None, movie_id: Optional[int] = None, n: int = 10
):
    start_time = time.time()
    
    # Create cache key based on request parameters
    cache_key = f"{rec_type}_{user_id or 'anon'}_{movie_id or 'none'}_{n}"
    current_time = time.time()
    
    # Check cache first for instant response
    if cache_key in recommendation_cache:
        cached_entry = recommendation_cache[cache_key]
        if current_time - cached_entry["timestamp"] < CACHE_DURATION:
            print(f"⚡ Cache HIT for {cache_key} (age: {int(current_time - cached_entry['timestamp'])}s)")
            return cached_entry["data"]
        else:
            # Cache expired, remove it
            del recommendation_cache[cache_key]
    
    try:
        # Get recommendations from models
        data = None
        if rec_type == "collaborative":
            data = recommendation_controller.get_collaborative_recommendations(user_id, n)
        elif rec_type == "content":
            data = recommendation_controller.get_content_based_recommendations(movie_id, n)
        elif rec_type == "hybrid":
            data = recommendation_controller.get_hybrid_recommendations(user_id, movie_id, n)
        elif rec_type == "personalized":
            if not user_id:
                data = recommendation_controller.get_collaborative_recommendations(None, n)
            else:
                try:
                    data = recommendation_controller.get_personalized_recommendations(user_id, n)
                    if not data or len(data) == 0:
                        data = recommendation_controller.get_collaborative_recommendations(user_id, n)
                except Exception as e:
                    print(f"Personalized rec failed for {user_id}: {e}, falling back to collaborative")
                    data = recommendation_controller.get_collaborative_recommendations(user_id, n)
        else:
            raise HTTPException(status_code=400, detail="Unknown recommendation type")
        
        # Fast fallback to cached popular movies if no results
        if not data or len(data) == 0:
            print(f"⚠️ No recommendations for {rec_type}/{user_id}, using popular movies")
            data = get_popular_movies_fast(user_id, n)
        
        # OPTIMIZED: Parallel poster enrichment
        enriched = enrich_movies_parallel(data[:n])
        
        # DEDUPLICATION: Remove any duplicate movies by ID
        seen_ids = set()
        unique_movies = []
        for movie in enriched:
            movie_id = movie.get('id') or movie.get('movieId')
            if movie_id and movie_id not in seen_ids:
                seen_ids.add(movie_id)
                unique_movies.append(movie)
        
        result = {"type": rec_type, "results": unique_movies}
        
        # Cache the result for 5 minutes
        recommendation_cache[cache_key] = {
            "data": result,
            "timestamp": current_time
        }
        
        elapsed = (time.time() - start_time) * 1000
        print(f"✓ Recommendations generated in {elapsed:.0f}ms (type={rec_type}, count={len(unique_movies)})")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/movies/{movie_id}/like")
def like_movie(movie_id: int):
    """Mark a movie as liked by the user."""
    try:
        # Persist interaction (no auth yet - username fallback to Anonymous)
        user = "Anonymous"
        try:
            movie_controller.add_interaction(movie_id, user, "like")
        except Exception:
            pass
        return {"status": "ok", "movie_id": movie_id, "action": "liked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/movies/{movie_id}/dislike")
def dislike_movie(movie_id: int):
    """Mark a movie as disliked by the user."""
    try:
        user = "Anonymous"
        try:
            movie_controller.add_interaction(movie_id, user, "dislike")
        except Exception:
            pass
        return {"status": "ok", "movie_id": movie_id, "action": "disliked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users")
def create_user(request: UserRequest):
    try:
        ok = movie_controller.add_user(request.userId, request.metadata)
        return {"status": "ok", "userId": request.userId, "created": ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password"""
    try:
        from app.data.models import User as UserModel
        from app.utils.auth import hash_password, generate_user_id
        
        # Check if email already exists
        existing_user = db.query(UserModel).filter(UserModel.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        
        # Create new user with hashed password
        user_id = generate_user_id()
        password_hash = hash_password(request.password)
        
        new_user = UserModel(
            user_id=user_id,
            name=request.name,
            email=request.email,
            password_hash=password_hash
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Also register with movie controller for compatibility
        try:
            metadata = f'{{"email":"{request.email}","name":"{request.name}"}}'
            movie_controller.add_user(user_id, metadata)
        except:
            pass
        
        return {
            "status": "ok",
            "message": "Đăng ký thành công",
            "user": {
                "id": new_user.user_id,
                "email": new_user.email,
                "name": new_user.name,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi đăng ký: {str(e)}")


@app.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password verification"""
    try:
        from app.data.models import User as UserModel
        from app.utils.auth import verify_password
        
        # Find user by email
        user = db.query(UserModel).filter(UserModel.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email chưa được đăng ký")
        
        # Check if user has a password (old users might not have)
        if not user.password_hash:
            raise HTTPException(
                status_code=400, 
                detail="Tài khoản chưa có mật khẩu. Vui lòng đăng ký lại."
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Mật khẩu không chính xác")
        
        return {
            "status": "ok",
            "message": "Đăng nhập thành công",
            "user": {
                "id": user.user_id,
                "email": user.email,
                "name": user.name,
                "metadata": f'{{"email":"{user.email}","name":"{user.name}"}}',
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đăng nhập: {str(e)}")



@app.post("/items")
def create_item(request: ItemRequest):
    try:
        ok = movie_controller.add_item(request.movieId, request.title, request.metadata)
        return {"status": "ok", "movieId": request.movieId, "created": ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interactions")
def create_interaction(request: InteractionRequest):
    try:
        user = request.userId or "Anonymous"
        action = request.action.lower()
        if action == 'view':
            movie_controller.record_view(request.movieId, user)
        elif action == 'click':
            movie_controller.record_click(request.movieId, user)
        elif action == 'rating':
            if request.rating is None:
                raise HTTPException(status_code=400, detail="rating required for action=rating")
            movie_controller.record_rating(request.movieId, user, request.rating)
        elif action in ('like', 'dislike'):
            movie_controller.add_interaction(request.movieId, user, action)
        else:
            raise HTTPException(status_code=400, detail="Unknown action")

        return {"status": "ok", "action": action}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interactions")
def get_interactions(user_id: Optional[str] = None, movie_id: Optional[int] = None, limit: Optional[int] = 1):
    """Return interactions filtered by user_id and/or movie_id.

    Default `limit=1` to fetch only the most recent action for quick checks.
    """
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database

        results = _db.fetch_interactions(user_id=user_id, movie_id=movie_id, limit=limit, data_dir=DATA_DIR)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/movies/{movie_id}/review")
def add_movie_review(movie_id: int, request: ReviewRequest):
    """Add a review to a movie and save to reviews.csv"""
    try:
        rating = request.rating
        review_text = request.review_text
        username = (request.username or "Anonymous").strip() or "Anonymous"
        
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        print(f"📝 Adding review: movie_id={movie_id}, rating={rating}, username={username}, review_text={review_text[:50] if review_text else '(empty)'}...")
        
        res = movie_controller.add_review(movie_id, rating, review_text or "", username)
        
        print(f"✅ Review saved successfully to CSV!")
        return {
            "status": "ok", 
            "movie_id": movie_id, 
            "rating": rating, 
            "username": username,
            "review": review_text,
            "message": "Review saved successfully!"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving review: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save review: {str(e)}")


@app.post("/movies/{movie_id}/comment")
def add_movie_comment(movie_id: int, request: CommentRequest):
    try:
        user = (request.userId or "Anonymous").strip() or "Anonymous"
        comment_text = (request.comment or "").strip()
        if not comment_text:
            raise HTTPException(status_code=400, detail="Empty comment")
        movie_controller.add_comment(movie_id, user, comment_text)
        # Optionally record interaction
        try:
            movie_controller.add_interaction(movie_id, user, 'comment')
        except Exception:
            pass
        return {"status": "ok", "movie_id": movie_id, "userId": user, "comment": comment_text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movies/{movie_id}/comments")
def get_movie_comments(movie_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    try:
        comments = movie_controller.get_movie_comments(movie_id, limit=limit, offset=offset)
        # Enrich comments with display_name from users table
        try:
            from app.data.models import User as UserModel
            enriched = []
            for c in comments:
                user_id = c.get('userId')
                if user_id:
                    user = db.query(UserModel).filter(UserModel.user_id == str(user_id)).first()
                    display = user.name if user else f"User {user_id}"
                else:
                    display = "Anonymous"
                enriched.append({**c, 'display_name': display})
            return {"movie_id": movie_id, "comments": enriched}
        except Exception:
            return {"movie_id": movie_id, "comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movies/comments/counts")
def get_comments_counts_get(movie_ids: str, db: Session = Depends(get_db)):
    """Return comment counts for comma-separated movie_ids"""
    try:
        if not movie_ids:
            raise HTTPException(status_code=400, detail="movie_ids required")
        ids = [int(part.strip()) for part in movie_ids.split(',') if part.strip().isdigit()]
        
        from app.data.models import Review
        from sqlalchemy import func
        
        # Count reviews per movie
        counts_query = db.query(
            Review.movie_id,
            func.count(Review.id).label('count')
        ).filter(
            Review.movie_id.in_([str(mid) for mid in ids])
        ).group_by(Review.movie_id).all()
        
        counts = {int(movie_id): count for movie_id, count in counts_query}
        return {"counts": counts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/movies/comments/counts")
def get_comments_counts_post(body: dict, db: Session = Depends(get_db)):
    """Return comment counts for list of movie_ids via POST"""
    try:
        ids = body.get("movie_ids", [])
        if not ids:
            raise HTTPException(status_code=400, detail="movie_ids required")
        
        from app.data.models import Review
        from sqlalchemy import func
        
        # Count reviews per movie
        counts_query = db.query(
            Review.movie_id,
            func.count(Review.id).label('count')
        ).filter(
            Review.movie_id.in_([str(mid) for mid in ids])
        ).group_by(Review.movie_id).all()
        
        counts = {int(movie_id): count for movie_id, count in counts_query}
        return {"counts": counts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WATCHLIST & FAVORITES ====================
# DEPRECATED: Use PostgreSQL endpoints below (user/{user_id}/watchlist/toggle)

class WatchlistRequest(BaseModel):
    movie_id: int
    user_id: str = "Anonymous"
    action: str = "add"  # "add" or "remove"


@app.post("/watchlist")
def manage_watchlist(request: WatchlistRequest, db: Session = Depends(get_db)):
    """DEPRECATED: Use /user/{user_id}/watchlist/toggle instead"""
    try:
        from app.data.db_postgresql import add_to_watchlist, remove_from_watchlist, get_or_create_user
        
        user_id = (request.user_id or "Anonymous").strip() or "Anonymous"
        movie_id = str(request.movie_id)
        action = request.action.lower()
        
        # Auto-create user if doesn't exist
        get_or_create_user(db, user_id=user_id)
        
        if action == "add":
            add_to_watchlist(db, user_id, movie_id)
            movie_controller.add_interaction(request.movie_id, user_id, "watchlist_add")
            return {"status": "added", "movie_id": request.movie_id, "user_id": user_id}
        elif action == "remove":
            remove_from_watchlist(db, user_id, movie_id)
            movie_controller.add_interaction(request.movie_id, user_id, "watchlist_remove")
            return {"status": "removed", "movie_id": request.movie_id, "user_id": user_id}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/profile")
def get_user_profile(user_id: str):
    """Lấy thông tin profile user: watchlist, history, stats."""
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database
        
        watchlist = _db.get_user_watchlist(user_id, data_dir=DATA_DIR)
        history = _db.fetch_watch_history(user_id, limit=100, data_dir=DATA_DIR)
        
        return {
            "user_id": user_id,
            "watchlist_count": len(watchlist),
            "watched_count": len(history),
            "watchlist": watchlist[:20],  # Return latest 20
            "recent_watched": history[:10]  # Return latest 10
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "watchlist_count": 0,
            "watched_count": 0,
            "watchlist": [],
            "recent_watched": []
        }


@app.post("/user/{user_id}/preferences")
def update_user_preferences(user_id: str, request: dict, db: Session = Depends(get_db)):
    """Lưu user preferences: favorite genres, quality, language."""
    try:
        # Get or create user
        user = get_or_create_user(db, user_id)
        
        # Store preferences in user metadata as JSON
        import json
        user.metadata = json.dumps(request)
        db.commit()
        
        return {"status": "ok", "user_id": user_id, "preferences": request}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/preferences")
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Lấy user preferences."""
    try:
        # Get user
        user = get_or_create_user(db, user_id)
        
        # Parse metadata JSON
        if user.metadata:
            import json
            try:
                prefs = json.loads(user.metadata)
                return {"user_id": user_id, "preferences": prefs}
            except:
                pass
        
        return {"user_id": user_id, "preferences": {}}
    except Exception as e:
        return {"user_id": user_id, "preferences": {}}


# ==================== WATCH HISTORY ====================

class WatchHistoryRequest(BaseModel):
    movie_id: int
    user_id: str = "Anonymous"
    timestamp: Optional[int] = None  # seconds watched
    duration: Optional[int] = None   # total duration


@app.post("/watch-history")
async def add_watch_history_new(request: WatchHistoryRequest, db: Session = Depends(get_db)):
    """Ghi lại lịch sử xem phim."""
    try:
        user_id = (request.user_id or "").strip()
        movie_id = str(request.movie_id)
        
        # Reject Anonymous users to prevent shared watch history
        if not user_id or user_id == "Anonymous":
            raise HTTPException(
                status_code=400, 
                detail="Watch history requires authenticated user. Please login."
            )
        
        from app.data.db_postgresql import add_watch_history, get_or_create_user
        
        # Auto-create user if doesn't exist
        get_or_create_user(db, user_id=user_id)
        
        add_watch_history(db, user_id, movie_id)
        
        return {"status": "ok", "movie_id": movie_id, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/watchlist/{user_id}")
def get_user_watchlist(user_id: str, db: Session = Depends(get_db)):
    """DEPRECATED: Use /user/{user_id}/watchlist instead"""
    try:
        from app.data.db_postgresql import get_user_watchlist as pg_get_watchlist
        watchlist_items = pg_get_watchlist(db, user_id)
        movies = [item.movie_id for item in watchlist_items if item.movie_id]
        return {"user_id": user_id, "movies": movies}
    except Exception as e:
        return {"user_id": user_id, "movies": []}


@app.get("/watch-history/{user_id}")
def get_user_watch_history(user_id: str, limit: int = 200, db: Session = Depends(get_db)):
    """DEPRECATED: Use /user/{user_id}/watched instead"""
    try:
        from app.data.db_postgresql import get_watch_history as pg_get_history
        history = pg_get_history(db, user_id, limit=limit)
        movies = [item.movie_id for item in history if item.movie_id]
        return {"user_id": user_id, "movies": movies}
    except Exception as e:
        return {"user_id": user_id, "movies": []}


@app.get("/movies/{movie_id}/streams")
def get_movie_streams(movie_id: int):
    """Lấy available video streams (quality options)."""
    try:
        # Fallback: return default streams
        # In production, này would query video hosting service
        streams = {
            "480p": f"/stream/{movie_id}/480p.mp4",
            "720p": f"/stream/{movie_id}/720p.mp4",
            "1080p": f"/stream/{movie_id}/1080p.mp4",
        }
        return {
            "movie_id": movie_id,
            "streams": streams,
            "default_quality": "720p"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movies/{movie_id}/subtitles")
def get_movie_subtitles(movie_id: int):
    """Lấy danh sách subtitles available."""
    try:
        # Fallback: return common languages
        subtitles = {
            "vi": f"/subtitles/{movie_id}/vi.vtt",
            "en": f"/subtitles/{movie_id}/en.vtt",
            "zh": f"/subtitles/{movie_id}/zh.vtt",
        }
        return {
            "movie_id": movie_id,
            "subtitles": subtitles,
            "languages": ["Vietnamese", "English", "Chinese"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOVIE COLLECTIONS ====================

@app.get("/collections/{collection_id}")
def get_collection(collection_id: str, limit: int = 20):
    """Lấy phim từ curated collection."""
    try:
        collections = {
            "best_2024": {
                "title": "Best of 2024",
                "description": "Những bộ phim hay nhất năm 2024",
                "filter": lambda m: m.get('year') == 2024 and m.get('vote_average', 0) >= 7
            },
            "horror": {
                "title": "Horror Collection",
                "description": "Những bộ phim kinh dị đáng xem",
                "filter": lambda m: 'horror' in str(m.get('genres', '')).lower()
            },
            "action": {
                "title": "Action Movies",
                "description": "Những bộ phim hành động kịch tính",
                "filter": lambda m: 'action' in str(m.get('genres', '')).lower()
            },
            "top_rated": {
                "title": "Top Rated",
                "description": "Những bộ phim được đánh giá cao nhất",
                "filter": lambda m: m.get('vote_average', 0) >= 8
            }
        }
        
        if collection_id not in collections:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        collection = collections[collection_id]
        all_movies = movie_controller.movie_model.get_all_movies()
        filtered = [m for m in all_movies if collection['filter'](m)][:limit]
        
        # Enrich with posters
        for movie in filtered:
            if not movie.get('poster_url'):
                title = movie.get('title', '')
                if TMDB_AVAILABLE:
                    try:
                        poster = get_movie_poster(title)
                        if poster:
                            movie['poster_url'] = poster
                    except Exception:
                        pass
            
            # Add unique placeholder if still no poster
            if not movie.get('poster_url'):
                seed = movie.get('id') or title
                movie['poster_url'] = f"https://picsum.photos/seed/{str(seed).lower().replace(' ', '')[:20] or 'movie'}/300/450"
        
        return {
            "collection_id": collection_id,
            "title": collection['title'],
            "description": collection['description'],
            "movies": filtered
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NOTIFICATIONS ====================

class NotificationRequest(BaseModel):
    user_id: str
    genres: list = []  # Favorite genres to track
    notify_new_releases: bool = True


@app.post("/notifications/subscribe")
def subscribe_notifications(request: NotificationRequest):
    """Subscribe user to notifications."""
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database
        
        import json
        prefs = {
            "genres": request.genres,
            "notify_new_releases": request.notify_new_releases
        }
        _db.update_user_metadata(request.user_id, json.dumps(prefs), data_dir=DATA_DIR)
        
        return {
            "status": "subscribed",
            "user_id": request.user_id,
            "preferences": prefs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/{user_id}")
def get_user_notifications(user_id: str):
    """Lấy notifications cho user (movies mới theo genres yêu thích)."""
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database
        
        # Get user preferences
        prefs = _db.get_user_metadata(user_id, data_dir=DATA_DIR)
        favorite_genres = prefs.get('genres', []) if prefs else []
        
        # Get new movies that match user's favorite genres
        new_movies = movie_controller.movie_model.get_new_releases(limit=50)
        
        notifications = []
        for movie in new_movies:
            genres = str(movie.get('genres', '')).lower()
            for genre in favorite_genres:
                if genre.lower() in genres:
                    notifications.append({
                        "movie_id": movie.get('id'),
                        "title": movie.get('title'),
                        "year": movie.get('year'),
                        "genre": genre,
                        "message": f"New {genre} movie: {movie.get('title')}"
                    })
                    break
        
        return {
            "user_id": user_id,
            "notifications": notifications[:10]  # Top 10
        }
    except Exception as e:
        return {"user_id": user_id, "notifications": []}

# ==================== SEARCH HISTORY ====================

@app.get("/search-history/{user_id}")
def get_search_history(user_id: str, limit: int = 50):
    """Lấy lịch sử tìm kiếm của user."""
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database
        
        history = _db.fetch_search_history(user_id, limit=limit, data_dir=DATA_DIR)
        return {"user_id": user_id, "history": history}
    except Exception as e:
        return {"user_id": user_id, "history": []}


@app.get("/search/popular")
def get_popular_searches(days: int = 7, limit: int = 10):
    """Lấy từ khóa tìm kiếm phổ biến."""
    try:
        try:
            from app.data import db_postgresql, database
        except Exception:
            from data import db_postgresql, database
        
        popular = _db.get_popular_searches(limit=limit, days=days, data_dir=DATA_DIR)
        return {"popular_searches": popular}
    except Exception as e:
        return {"popular_searches": []}


# ==================== USER BEHAVIOR ANALYSIS ====================

@app.get("/user/{user_id}/behavior")
def get_user_behavior_analysis(user_id: str):
    """Phân tích hành vi người dùng: thể loại yêu thích, thời gian xem, xu hướng."""
    try:
        behavior = recommendation_controller.analyze_user_behavior(user_id)
        return {
            "user_id": user_id,
            "behavior": behavior
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "behavior": {},
            "error": str(e)
        }


@app.post("/models/refresh")
def refresh_recommendation_models():
    """Cập nhật models với dữ liệu mới (để học liên tục)."""
    try:
        success = recommendation_controller.refresh_models()
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER PROFILE API (PostgreSQL) ====================

@app.get("/user/{user_id}/stats")
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Lấy thống kê người dùng từ PostgreSQL"""
    try:
        # Get or create user
        user = get_or_create_user(db, user_id)
        
        # Import with alias to avoid conflicts
        from app.data.db_postgresql import (
            get_user_ratings as pg_get_ratings,
            get_user_watchlist as pg_get_watchlist,
            get_watch_history as pg_get_history
        )
        
        # Get statistics from PostgreSQL
        ratings = pg_get_ratings(db, user_id)
        watchlist_items = pg_get_watchlist(db, user_id)
        watch_history = pg_get_history(db, user_id)
        reviews = db.query(Review).filter(Review.user_id == user_id).all()
        
        # Calculate additional stats
        completed_movies = [h for h in watch_history if h.completed]
        
        # Get favorite genres from ratings
        favorite_genres = {}
        for rating in ratings:
            if rating.movie and rating.movie.genres:
                for genre in rating.movie.genres:
                    if isinstance(genre, dict) and 'name' in genre:
                        genre_name = genre['name']
                    else:
                        genre_name = str(genre)
                    favorite_genres[genre_name] = favorite_genres.get(genre_name, 0) + 1
        
        # Top 3 genres
        top_genres = sorted(favorite_genres.items(), key=lambda x: x[1], reverse=True)[:3]
        top_genres = [g[0] for g in top_genres]
        
        return {
            "user_id": user_id,
            "name": user.name or f"User {user_id}",
            "email": user.email,
            "total_ratings": len(ratings),
            "total_watchlist": len(watchlist_items),
            "total_watched": len(completed_movies),
            "total_reviews": len(reviews),
            "favorite_genres": top_genres,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user stats: {str(e)}")


@app.get("/user/{user_id}/watchlist")
def get_user_watchlist_movies(user_id: str, db: Session = Depends(get_db)):
    """Lấy danh sách phim trong watchlist"""
    try:
        from app.data.db_postgresql import get_user_watchlist as pg_get_watchlist
        watchlist_items = pg_get_watchlist(db, user_id)
        movies = []
        
        for item in watchlist_items:
            if item.movie:
                # Handle NaN values
                import math
                vote_avg = item.movie.vote_average
                if isinstance(vote_avg, float) and (math.isnan(vote_avg) or math.isinf(vote_avg)):
                    vote_avg = 0.0
                
                movies.append({
                    "id": item.movie.movie_id,
                    "title": item.movie.title,
                    "poster_url": item.movie.poster_url or item.movie.poster_path,
                    "year": item.movie.year,
                    "vote_average": vote_avg,
                    "genres": item.movie.genres,
                    "added_at": item.added_at.isoformat()
                })
        
        # Enrich with TMDB posters if available
        if TMDB_AVAILABLE:
            for movie in movies:
                if not movie.get('poster_url') or 'picsum' in movie.get('poster_url', ''):
                    try:
                        tmdb_poster = get_movie_poster(movie['title'], movie.get('year'))
                        if tmdb_poster:
                            movie['poster_url'] = tmdb_poster
                    except Exception:
                        pass
        
        return {"movies": movies}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/watched")
def get_user_watched_movies(user_id: str, limit: int = 200, db: Session = Depends(get_db)):
    """Lấy danh sách phim đã xem"""
    try:
        # Never return watch history for Anonymous users
        if not user_id or user_id == "Anonymous":
            return {"movies": []}
        
        from app.data.db_postgresql import get_watch_history as pg_get_history
        history = pg_get_history(db, user_id, limit=limit)
        movies = []
        
        for item in history:
            if item.movie:
                # Handle NaN values
                import math
                vote_avg = item.movie.vote_average
                if isinstance(vote_avg, float) and (math.isnan(vote_avg) or math.isinf(vote_avg)):
                    vote_avg = 0.0
                
                movies.append({
                    "id": item.movie.movie_id,
                    "title": item.movie.title,
                    "poster_url": item.movie.poster_url or item.movie.poster_path,
                    "year": item.movie.year,
                    "vote_average": vote_avg,
                    "watched_at": item.watched_at.isoformat(),
                    "progress": item.progress,
                    "completed": item.completed
                })
        
        # Enrich with TMDB posters if available
        if TMDB_AVAILABLE:
            for movie in movies:
                if not movie.get('poster_url') or 'picsum' in movie.get('poster_url', ''):
                    try:
                        tmdb_poster = get_movie_poster(movie['title'])
                        if tmdb_poster:
                            movie['poster_url'] = tmdb_poster
                    except Exception:
                        pass
        
        return {"movies": movies}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/{user_id}/watchlist/toggle")
def toggle_watchlist(user_id: str, movie_id: int, db: Session = Depends(get_db)):
    """Thêm/xóa phim khỏi watchlist"""
    try:
        # Ensure user exists first
        get_or_create_user(db, user_id)
        
        movie_id_str = str(movie_id)
        
        # Check if exists
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == user_id,
            Watchlist.movie_id == movie_id_str
        ).first()
        
        if existing:
            remove_from_watchlist(db, user_id, movie_id_str)
            return {"action": "removed", "in_watchlist": False}
        else:
            add_to_watchlist(db, user_id, movie_id_str)
            return {"action": "added", "in_watchlist": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/{user_id}/watch-progress")
def update_watch_progress(
    user_id: str, 
    movie_id: int, 
    progress: float = 0.0, 
    completed: bool = False,
    db: Session = Depends(get_db)
):
    """Cập nhật tiến độ xem phim"""
    try:
        # Reject Anonymous users to prevent shared watch history
        if not user_id or user_id == "Anonymous":
            raise HTTPException(
                status_code=400, 
                detail="Watch progress requires authenticated user. Please login."
            )
        
        movie_id_str = str(movie_id)
        add_watch_history(db, user_id, movie_id_str, progress, completed)
        return {"success": True, "progress": progress, "completed": completed}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


