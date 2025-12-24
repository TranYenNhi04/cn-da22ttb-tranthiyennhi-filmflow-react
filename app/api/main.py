# app/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import re

# Controllers
from controllers.movie_controller import MovieController
from controllers.recommendation_controller import RecommendationController

# Utils
try:
    from utils.tmdb_api import get_movie_poster, get_movie_data
    TMDB_AVAILABLE = True
except:
    TMDB_AVAILABLE = False
    get_movie_poster = None
    get_movie_data = None

try:
    from utils.youtube_api import get_youtube_video
    YOUTUBE_AVAILABLE = True
except:
    YOUTUBE_AVAILABLE = False
    get_youtube_video = None

# FastAPI
app = FastAPI(title="Movie Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

movie_controller = MovieController(data_dir=DATA_DIR)
recommendation_controller = RecommendationController(data_dir=DATA_DIR)

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
        
        # Save search history if user_id is provided
        if user_id and q:
            try:
                try:
                    from app.data import database as _db
                except Exception:
                    from data import database as _db
                _db.insert_search_history(user_id, q, len(results), data_dir=DATA_DIR)
            except Exception as e:
                print(f"Failed to save search history: {e}")
        
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
        trend_data = movie_controller.movie_model.get_trending_movies(limit=limit)
        
        # Normalize field names and ensure all movies have required fields
        for movie in trend_data:
            # Ensure id field exists (normalize movieId to id)
            if 'movieId' in movie and 'id' not in movie:
                movie['id'] = movie['movieId']
            elif 'id' not in movie and 'movieId' not in movie:
                # Try to get from other fields as fallback
                continue
                
            # Ensure poster_url
            if not movie.get('poster_url') and not movie.get('poster_path'):
                # Generate placeholder
                seed = movie.get('id') or movie.get('movieId') or movie.get('title', '')
                t = (str(seed) or '').lower().replace(' ', '')
                movie['poster_url'] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
        
        return {"movies": trend_data}
    except Exception as e:
        return {"movies": []}


@app.get("/movies/new-releases")
def get_new_releases(limit: int = 20):
    """Lấy phim mới nhất - Vieon style."""
    try:
        movies = movie_controller.movie_model.get_new_releases(limit=limit)
        
        # Ensure all movies have poster_url
        for movie in movies:
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
        
        return {"movies": movies}
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
    try:
        if rec_type == "collaborative":
            data = recommendation_controller.get_collaborative_recommendations(user_id, n)
        elif rec_type == "content":
            data = recommendation_controller.get_content_based_recommendations(movie_id, n)
        elif rec_type == "hybrid":
            data = recommendation_controller.get_hybrid_recommendations(user_id, movie_id, n)
        elif rec_type == "personalized":
            # New: personalized recommendations based on user behavior and context
            if not user_id:
                raise HTTPException(status_code=400, detail="user_id required for personalized recommendations")
            data = recommendation_controller.get_personalized_recommendations(user_id, n)
        else:
            raise HTTPException(status_code=400, detail="Unknown recommendation type")
        
        # Enrich each movie with video_url and poster_url (optimized)
        enriched = []
        for movie in data:
            title = movie.get("title", "")
            year = movie.get("year")
            
            # Chỉ lấy poster từ TMDB, bỏ qua video để nhanh hơn
            if not movie.get("poster_url") and TMDB_AVAILABLE:
                tmdb_poster = get_movie_poster(title)
                if tmdb_poster:
                    movie["poster_url"] = tmdb_poster
            
            # Thêm poster placeholder nếu chưa có
            if not movie.get("poster_url"):
                seed = movie.get('id') or title
                t = str(seed).lower().replace(' ', '')
                movie["poster_url"] = f"https://picsum.photos/seed/{t[:20] or 'movie'}/300/450"
            
            # Video URL sẽ load khi click vào phim (lazy loading)
            if not movie.get("video_url"):
                movie["video_url"] = None
            
            
            enriched.append(movie)
        
        return {"type": rec_type, "results": enriched}
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


@app.post("/auth/login")
def login(request: LoginRequest):
    """Simple login: find user by email in metadata; password is ignored (mock)."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        user = _db.get_user_by_email(request.email, DATA_DIR)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "ok", "user": user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            from app.data import database as _db
        except Exception:
            from data import database as _db

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
def get_movie_comments(movie_id: int, limit: int = 50, offset: int = 0):
    try:
        comments = movie_controller.get_movie_comments(movie_id, limit=limit, offset=offset)
        # enrich comments with display_name from users table
        try:
            try:
                from app.data import database as _db
            except Exception:
                from data import database as _db
            enriched = []
            for c in comments:
                display = _db.get_user_display_name(c.get('userId'), data_dir=DATA_DIR)
                enriched.append({**c, 'display_name': display})
            return {"movie_id": movie_id, "comments": enriched}
        except Exception:
            return {"movie_id": movie_id, "comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movies/comments/counts")
def get_comments_counts_get(movie_ids: str):
    """Return comment counts for comma-separated movie_ids, e.g. movie_ids=1,2,3"""
    try:
        if not movie_ids:
            raise HTTPException(status_code=400, detail="movie_ids required")
        ids = []
        for part in movie_ids.split(','):
            try:
                ids.append(int(part.strip()))
            except Exception:
                continue
        try:
            try:
                from app.data import database as _db
            except Exception:
                from data import database as _db
            counts = _db.fetch_comment_counts(ids, data_dir=DATA_DIR)
            return {"counts": counts}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/movies/comments/counts")
def get_comments_counts_post(body: dict):
    """Return comment counts for list of movie_ids via POST. Expects {"movie_ids": [1,2,3]}"""
    try:
        ids = body.get("movie_ids", [])
        if not ids:
            raise HTTPException(status_code=400, detail="movie_ids required")
        try:
            try:
                from app.data import database as _db
            except Exception:
                from data import database as _db
            counts = _db.fetch_comment_counts(ids, data_dir=DATA_DIR)
            return {"counts": counts}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WATCHLIST & FAVORITES ====================

class WatchlistRequest(BaseModel):
    movie_id: int
    user_id: str = "Anonymous"
    action: str = "add"  # "add" or "remove"


@app.post("/watchlist")
def manage_watchlist(request: WatchlistRequest):
    """Thêm/xóa phim từ watchlist."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        user_id = (request.user_id or "Anonymous").strip() or "Anonymous"
        movie_id = request.movie_id
        action = request.action.lower()
        
        if action == "add":
            # Add to actual watchlist table
            _db.add_to_watchlist(user_id, movie_id, data_dir=DATA_DIR)
            # Also track interaction
            movie_controller.add_interaction(movie_id, user_id, "watchlist_add")
            return {"status": "added", "movie_id": movie_id, "user_id": user_id}
        elif action == "remove":
            # Remove from watchlist table
            _db.remove_from_watchlist(user_id, movie_id, data_dir=DATA_DIR)
            # Also track interaction
            movie_controller.add_interaction(movie_id, user_id, "watchlist_remove")
            return {"status": "removed", "movie_id": movie_id, "user_id": user_id}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error managing watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/profile")
def get_user_profile(user_id: str):
    """Lấy thông tin profile user: watchlist, history, stats."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
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
def update_user_preferences(user_id: str, request: dict):
    """Lưu user preferences: favorite genres, quality, language."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        import json
        prefs = json.dumps(request)
        _db.update_user_metadata(user_id, prefs, data_dir=DATA_DIR)
        
        return {"status": "ok", "user_id": user_id, "preferences": request}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/preferences")
def get_user_preferences(user_id: str):
    """Lấy user preferences."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        prefs = _db.get_user_metadata(user_id, data_dir=DATA_DIR)
        return {"user_id": user_id, "preferences": prefs}
    except Exception as e:
        return {"user_id": user_id, "preferences": {}}


# ==================== WATCH HISTORY ====================

class WatchHistoryRequest(BaseModel):
    movie_id: int
    user_id: str = "Anonymous"
    timestamp: Optional[int] = None  # seconds watched
    duration: Optional[int] = None   # total duration


@app.post("/watch-history")
def add_watch_history(request: WatchHistoryRequest):
    """Ghi lại lịch sử xem phim."""
    try:
        user_id = (request.user_id or "Anonymous").strip() or "Anonymous"
        movie_id = request.movie_id
        
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        _db.insert_watch_history(user_id, movie_id, request.timestamp, request.duration, data_dir=DATA_DIR)
        return {"status": "ok", "movie_id": movie_id, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/watchlist/{user_id}")
def get_user_watchlist(user_id: str):
    """Lấy danh sách phim yêu thích của user."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        watchlist = _db.get_user_watchlist(user_id, data_dir=DATA_DIR)
        return {"user_id": user_id, "movies": watchlist}
    except Exception as e:
        return {"user_id": user_id, "movies": []}


@app.get("/watch-history/{user_id}")
def get_user_watch_history(user_id: str):
    """Lấy lịch sử xem phim của user."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        history = _db.fetch_watch_history(user_id, data_dir=DATA_DIR)
        return {"user_id": user_id, "movies": history}
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
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
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
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
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
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        history = _db.fetch_search_history(user_id, limit=limit, data_dir=DATA_DIR)
        return {"user_id": user_id, "history": history}
    except Exception as e:
        return {"user_id": user_id, "history": []}


@app.get("/search/popular")
def get_popular_searches(days: int = 7, limit: int = 10):
    """Lấy từ khóa tìm kiếm phổ biến."""
    try:
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
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
