import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta
from collections import Counter
import time

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.collaborative_model import CollaborativeModel
from app.models.content_based_model import ContentBasedModel

class PersonalizedRecommendationModel:
    """
    Model gợi ý cá nhân hóa dựa trên:
    - Lịch sử xem (watch history)
    - Thể loại yêu thích
    - Thời gian xem (ngữ cảnh thời gian)
    - Xu hướng xem gần đây
    - Đánh giá và phản hồi (ratings, likes)
    """
    
    def __init__(self, data_dir=None):
        self.data_dir = data_dir
        self.collaborative_model = CollaborativeModel(data_dir)
        self.content_based_model = ContentBasedModel(data_dir)
        # Cache for user behavior analysis
        self._behavior_cache = {}
        self._cache_duration = 300  # 5 minutes
    
    def analyze_user_behavior(self, user_id):
        """
        Phân tích hành vi người dùng từ:
        - Watch history (thời gian xem, thể loại)
        - Ratings
        - Interactions (likes, clicks)
        - Search history
        
        Uses caching to avoid repeated expensive computations
        """
        # Check cache first
        current_time = time.time()
        cache_key = f"behavior_{user_id}"
        
        if cache_key in self._behavior_cache:
            cached_entry = self._behavior_cache[cache_key]
            if current_time - cached_entry["timestamp"] < self._cache_duration:
                return cached_entry["data"]
        
        try:
            from app.data import db_postgresql
            from app.data.models import WatchHistory, Rating
        except Exception:
            from data import db_postgresql
            from data.models import WatchHistory, Rating
        
        behavior = {
            'favorite_genres': [],
            'watch_times': [],  # Thời gian trong ngày thường xem
            'recent_genres': [],  # Thể loại xem gần đây (7 ngày)
            'avg_rating': 0,
            'total_watched': 0,
            'preferred_decade': None
        }
        
        try:
            # 1. Analyze watch history from PostgreSQL
            with db_postgresql.get_db_session() as db:
                watch_history_records = db.query(WatchHistory).filter(
                    WatchHistory.user_id == str(user_id)
                ).order_by(WatchHistory.watched_at.desc()).limit(100).all()
                
                watch_history = []
                for record in watch_history_records:
                    watch_history.append({
                        'movieId': int(record.movie_id) if record.movie_id.isdigit() else record.movie_id,
                        'viewed_at': record.watched_at.isoformat() if record.watched_at else None
                    })
            
            behavior['total_watched'] = len(watch_history)
            
            # Extract watch times (hours of day)
            watch_times = []
            recent_movie_ids = []
            for entry in watch_history[:20]:  # Last 20 movies
                try:
                    timestamp = entry.get('viewed_at')
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp)
                        watch_times.append(dt.hour)
                        
                        # Recent movies (last 7 days)
                        if datetime.now() - dt < timedelta(days=7):
                            recent_movie_ids.append(entry.get('movieId'))
                except:
                    pass
            
            behavior['watch_times'] = watch_times
            
            # 2. Analyze genres from watched movies
            movies_df = self.content_based_model.movies_df
            genre_counter = Counter()
            recent_genre_counter = Counter()
            decades = []
            
            for entry in watch_history:
                movie_id = entry.get('movieId')
                movie = movies_df[movies_df['id'] == movie_id]
                if not movie.empty:
                    movie_data = movie.iloc[0]
                    genres = str(movie_data.get('genres', '')).split('|')
                    for genre in genres:
                        genre = genre.strip()
                        if genre:
                            genre_counter[genre] += 1
                            
                            # Recent genres
                            if movie_id in recent_movie_ids:
                                recent_genre_counter[genre] += 1
                    
                    # Analyze preferred decade
                    year = movie_data.get('year')
                    if year and year > 1900:
                        decades.append((year // 10) * 10)
            
            # Top 5 favorite genres (tăng từ 3 lên 5 để coverage tốt hơn)
            behavior['favorite_genres'] = [g for g, _ in genre_counter.most_common(5)]
            behavior['recent_genres'] = [g for g, _ in recent_genre_counter.most_common(5)]
            behavior['genre_weights'] = {g: count for g, count in genre_counter.most_common(10)}
            
            # Most watched decade
            if decades:
                behavior['preferred_decade'] = Counter(decades).most_common(1)[0][0]
            
            # 3. Analyze ratings from PostgreSQL
            with db_postgresql.get_db_session() as db:
                user_ratings = db.query(Rating).filter(
                    Rating.user_id == str(user_id)
                ).all()
                
                if user_ratings:
                    ratings = [r.rating for r in user_ratings]
                    behavior['avg_rating'] = sum(ratings) / len(ratings) if ratings else 0
        
        except Exception as e:
            print(f"Error analyzing user behavior: {e}")
        
        # Cache the result
        self._behavior_cache[cache_key] = {
            "data": behavior,
            "timestamp": current_time
        }
        
        return behavior
    
    def get_context_aware_recommendations(self, user_id, current_hour=None, n_recommendations=10):
        """
        Gợi ý phim dựa trên ngữ cảnh:
        - Thời gian trong ngày (sáng/chiều/tối)
        - Xu hướng xem gần đây
        - Thể loại yêu thích
        """
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # Analyze user behavior
        behavior = self.analyze_user_behavior(user_id)
        
        # Get base recommendations from collaborative filtering (tăng lên 5x để có nhiều lựa chọn hơn)
        base_recs = self.collaborative_model.get_recommendations(user_id, n_recommendations * 5)
        
        # Nếu không có collaborative recs, lấy từ content-based dựa trên thể loại yêu thích
        if not base_recs and behavior['favorite_genres']:
            # Lấy phim theo thể loại yêu thích
            all_movies = self.content_based_model.movies_df
            genre_movies = all_movies[all_movies['genres'].str.lower().str.contains(
                '|'.join([g.lower() for g in behavior['favorite_genres'][:3]]), 
                na=False, 
                regex=True
            )].sort_values('vote_average', ascending=False).head(n_recommendations * 5)
            base_recs = genre_movies.to_dict('records')
        
        # Score and filter based on context
        scored_movies = []
        for movie in base_recs:
            score = 0
            genre_match_count = 0
            
            # 1. Genre matching score (50% - tăng từ 40%)
            movie_genres = str(movie.get('genres', '')).lower()
            
            # Tính điểm dựa trên số lượng thể loại khớp
            for genre in behavior['favorite_genres']:
                if genre.lower() in movie_genres:
                    genre_match_count += 1
                    # Genre weights từ behavior
                    weight = behavior.get('genre_weights', {}).get(genre, 1)
                    score += 0.15 * min(weight / 5, 1)  # Normalize weight
            
            # Bonus nếu khớp nhiều thể loại
            if genre_match_count >= 2:
                score += 0.2
            elif genre_match_count >= 1:
                score += 0.1
            
            # Recent genre bonus (15% - giảm từ 20%)
            for genre in behavior['recent_genres']:
                if genre.lower() in movie_genres:
                    score += 0.15
                    break
            
            # 2. Time of day context (10% - giảm xuống)
            # Morning (6-12): Light, Comedy, Animation
            # Afternoon (12-18): Action, Adventure, Family
            # Evening (18-24): Drama, Thriller, Horror
            # Night (0-6): Horror, Thriller, Sci-Fi
            if 6 <= current_hour < 12:
                if any(g in movie_genres for g in ['comedy', 'animation', 'family']):
                    score += 0.1
            elif 12 <= current_hour < 18:
                if any(g in movie_genres for g in ['action', 'adventure', 'family']):
                    score += 0.1
            elif 18 <= current_hour < 24:
                if any(g in movie_genres for g in ['drama', 'thriller', 'horror', 'romance']):
                    score += 0.1
            else:  # 0-6
                if any(g in movie_genres for g in ['horror', 'thriller', 'sci-fi']):
                    score += 0.1
            
            # 3. Rating score (15% - giảm từ 20%)
            movie_rating = movie.get('vote_average', 0)
            if movie_rating >= 8.0:
                score += 0.15
            elif movie_rating >= 7.0:
                score += 0.1
            elif movie_rating >= 6.0:
                score += 0.05
            
            # 4. Decade preference (10% bonus)
            movie_year = movie.get('year', 0)
            if behavior['preferred_decade'] and movie_year:
                decade = (movie_year // 10) * 10
                if abs(decade - behavior['preferred_decade']) <= 10:
                    score += 0.1
            
            scored_movies.append((movie, score))
        
        # Lọc bỏ phim có điểm quá thấp (score < 0.2)
        scored_movies = [(movie, score) for movie, score in scored_movies if score >= 0.2]
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Đảm bảo diversity - không lấy quá nhiều phim cùng thể loại
        diverse_movies = []
        genre_count = {}
        
        for movie, score in scored_movies:
            movie_genres = str(movie.get('genres', '')).lower().split('|')
            
            # Kiểm tra xem có thể thêm phim này không (max 3 phim/thể loại)
            can_add = True
            for genre in movie_genres:
                genre = genre.strip()
                if genre and genre_count.get(genre, 0) >= 3:
                    can_add = False
                    break
            
            if can_add:
                diverse_movies.append(movie)
                # Update genre count
                for genre in movie_genres:
                    genre = genre.strip()
                    if genre:
                        genre_count[genre] = genre_count.get(genre, 0) + 1
                
                if len(diverse_movies) >= n_recommendations:
                    break
        
        # Nếu không đủ phim, thêm phim có score cao nhất vào
        if len(diverse_movies) < n_recommendations:
            remaining = [m for m, s in scored_movies if m not in diverse_movies]
            diverse_movies.extend(remaining[:n_recommendations - len(diverse_movies)])
        
        return diverse_movies[:n_recommendations]
    
    def get_personalized_recommendations(self, user_id, n_recommendations=10):
        """
        Gợi ý cá nhân hóa kết hợp tất cả yếu tố:
        - User behavior analysis
        - Context-aware (time of day)
        - Recent trends
        - Collaborative filtering
        """
        current_hour = datetime.now().hour
        return self.get_context_aware_recommendations(user_id, current_hour, n_recommendations)
    
    def refresh(self):
        """Refresh underlying models."""
        self.collaborative_model.refresh()
        return True
