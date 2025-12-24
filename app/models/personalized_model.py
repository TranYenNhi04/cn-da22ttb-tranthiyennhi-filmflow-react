import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta
from collections import Counter

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.collaborative_model import CollaborativeModel
from models.content_based_model import ContentBasedModel

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
    
    def analyze_user_behavior(self, user_id):
        """
        Phân tích hành vi người dùng từ:
        - Watch history (thời gian xem, thể loại)
        - Ratings
        - Interactions (likes, clicks)
        - Search history
        """
        try:
            from app.data import database as _db
        except Exception:
            from data import database as _db
        
        behavior = {
            'favorite_genres': [],
            'watch_times': [],  # Thời gian trong ngày thường xem
            'recent_genres': [],  # Thể loại xem gần đây (7 ngày)
            'avg_rating': 0,
            'total_watched': 0,
            'preferred_decade': None
        }
        
        try:
            # 1. Analyze watch history
            watch_history = _db.fetch_watch_history(user_id, limit=100, data_dir=self.data_dir)
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
            
            # Top 3 favorite genres
            behavior['favorite_genres'] = [g for g, _ in genre_counter.most_common(3)]
            behavior['recent_genres'] = [g for g, _ in recent_genre_counter.most_common(3)]
            
            # Most watched decade
            if decades:
                behavior['preferred_decade'] = Counter(decades).most_common(1)[0][0]
            
            # 3. Analyze ratings
            ratings_df = _db.fetch_ratings_df(data_dir=self.data_dir)
            user_ratings = ratings_df[ratings_df['userId'] == user_id]
            if not user_ratings.empty:
                behavior['avg_rating'] = user_ratings['rating'].mean()
            
            # 4. Get user preferences from metadata
            prefs = _db.get_user_metadata(user_id, data_dir=self.data_dir)
            if prefs and 'favorite_genres' in prefs:
                # Merge with watched genres
                pref_genres = prefs.get('favorite_genres', [])
                for genre in pref_genres:
                    if genre not in behavior['favorite_genres']:
                        behavior['favorite_genres'].append(genre)
        
        except Exception as e:
            print(f"Error analyzing user behavior: {e}")
        
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
        
        # Get base recommendations from collaborative filtering
        base_recs = self.collaborative_model.get_recommendations(user_id, n_recommendations * 3)
        
        # Score and filter based on context
        scored_movies = []
        for movie in base_recs:
            score = 0
            
            # 1. Genre matching score (40%)
            movie_genres = str(movie.get('genres', '')).lower()
            for genre in behavior['favorite_genres']:
                if genre.lower() in movie_genres:
                    score += 0.4
                    break
            
            # Recent genre bonus (20%)
            for genre in behavior['recent_genres']:
                if genre.lower() in movie_genres:
                    score += 0.2
                    break
            
            # 2. Time of day context (20%)
            # Morning (6-12): Light, Comedy, Animation
            # Afternoon (12-18): Action, Adventure, Family
            # Evening (18-24): Drama, Thriller, Horror
            # Night (0-6): Horror, Thriller, Sci-Fi
            if 6 <= current_hour < 12:
                if any(g in movie_genres for g in ['comedy', 'animation', 'family']):
                    score += 0.2
            elif 12 <= current_hour < 18:
                if any(g in movie_genres for g in ['action', 'adventure', 'family']):
                    score += 0.2
            elif 18 <= current_hour < 24:
                if any(g in movie_genres for g in ['drama', 'thriller', 'horror', 'romance']):
                    score += 0.2
            else:  # 0-6
                if any(g in movie_genres for g in ['horror', 'thriller', 'sci-fi']):
                    score += 0.2
            
            # 3. Rating score (20%)
            movie_rating = movie.get('vote_average', 0)
            if movie_rating >= 7.0:
                score += 0.2
            elif movie_rating >= 6.0:
                score += 0.1
            
            # 4. Decade preference (10% bonus)
            movie_year = movie.get('year', 0)
            if behavior['preferred_decade'] and movie_year:
                decade = (movie_year // 10) * 10
                if abs(decade - behavior['preferred_decade']) <= 10:
                    score += 0.1
            
            scored_movies.append((movie, score))
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return [movie for movie, score in scored_movies[:n_recommendations]]
    
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
