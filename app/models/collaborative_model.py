import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics.pairwise import cosine_similarity
import time

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.movie_model import MovieModel

class CollaborativeModel:
    def __init__(self, data_dir=None):
        # Use MovieModel as the source of truth for movie & ratings data
        self.movie_model = MovieModel(data_dir=data_dir)
        self.ratings_matrix = None
        self.user_similarity = None
        self._last_build_time = 0
        self._build_cache_duration = 600  # Rebuild model only every 10 minutes
        # build model initially; allow refresh later to pick up new ratings
        self._build_model()
    
    def _build_model(self):
        """
        Xây dựng ma trận đánh giá và tính toán độ tương đồng giữa người dùng
        Cached for performance - rebuilds only when needed
        """
        current_time = time.time()
        
        # Skip rebuild if model was built recently (within cache duration)
        if (self.ratings_matrix is not None and 
            not self.ratings_matrix.empty and
            current_time - self._last_build_time < self._build_cache_duration):
            return
        
        try:
            # Use ratings_df from MovieModel (it already handles missing/empty files)
            ratings_df = self.movie_model.ratings_df
            required_columns = ['userId', 'movieId', 'rating']
            missing_columns = [col for col in required_columns if col not in ratings_df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in ratings.csv: {missing_columns}")

            # Create user x movie ratings matrix
            if ratings_df.empty:
                self.ratings_matrix = pd.DataFrame()
                self.user_similarity = np.array([])
                return

            self.ratings_matrix = ratings_df.pivot(
                index='userId',
                columns='movieId',
                values='rating'
            ).fillna(0)

            # Compute user similarity
            self.user_similarity = cosine_similarity(self.ratings_matrix)
            self._last_build_time = current_time
            print(f"✓ Collaborative model built/refreshed (users: {len(self.ratings_matrix)}, movies: {len(self.ratings_matrix.columns)})")

        except Exception as e:
            print(f"Error building collaborative model: {str(e)}")
            self.ratings_matrix = pd.DataFrame()
            self.user_similarity = np.array([])

    def refresh(self):
        """Reload ratings from MovieModel and rebuild matrices."""
        # reload ratings_df from the source (which may read from DB)
        try:
            # Force a rebuild by resetting the cache timer
            self._last_build_time = 0
            
            # If MovieModel supports reloading its ratings_df, ensure it's fresh
            if hasattr(self.movie_model, 'ratings_df'):
                # Some implementations may have a method to refresh; attempt to re-read from DB
                try:
                    # re-fetch from database if available
                    try:
                        from app.data import database as _db
                    except Exception:
                        from data import database as _db
                    self.movie_model.ratings_df = _db.fetch_ratings_df(self.movie_model.data_dir)
                except Exception:
                    pass
            self._build_model()
            return True
        except Exception:
            return False
    
    def get_recommendations(self, user_id=None, n_recommendations=10):
        """
        Lấy gợi ý phim dựa trên Collaborative Filtering với personalization
        """
        # Ensure model is up-to-date with latest ratings
        if self.ratings_matrix is None or (hasattr(self, 'ratings_matrix') and getattr(self, 'ratings_matrix', pd.DataFrame()).empty):
            # Attempt refresh
            self.refresh()

        if self.ratings_matrix is None or self.ratings_matrix.empty:
            return []
        
        # Try to enrich with user behavioral data from PostgreSQL
        user_watched_movies = set()
        if user_id:
            try:
                try:
                    from app.data import database as _db
                except Exception:
                    from data import database as _db
                # Get user's watch history to exclude from recommendations
                watch_history = _db.fetch_watch_history(user_id, limit=100, data_dir=self.movie_model.data_dir)
                user_watched_movies = {entry.get('movieId') for entry in watch_history if entry.get('movieId')}
            except Exception as e:
                print(f"Could not fetch watch history for {user_id}: {e}")
            
        if user_id is None:
            # Nếu không có user_id, lấy người dùng có nhiều đánh giá nhất
            user_id = self.ratings_matrix.sum(axis=1).idxmax()
        else:
            # user_id may be numeric or string; ensure it exists in index
            if user_id not in self.ratings_matrix.index:
                # Attempt to refresh once and check again
                self.refresh()
                if user_id not in self.ratings_matrix.index:
                    # User has no ratings yet - return popular movies they haven't watched
                    all_movies = self.movie_model.movies_df
                    popular_movies = all_movies.sort_values('vote_average', ascending=False).head(n_recommendations * 2)
                    
                    # Exclude watched movies
                    if user_watched_movies:
                        popular_movies = popular_movies[~popular_movies['id'].isin(user_watched_movies)]
                    
                    # Convert to dict format
                    results = []
                    for _, movie in popular_movies.head(n_recommendations).iterrows():
                        movie_dict = movie.to_dict()
                        # Ensure id field exists
                        if 'id' not in movie_dict and 'movieId' in movie_dict:
                            movie_dict['id'] = movie_dict['movieId']
                        results.append(movie_dict)
                    return results
        
        # Lấy các phim chưa được đánh giá bởi người dùng
        user_ratings = self.ratings_matrix.loc[user_id]
        unwatched_movies = user_ratings[user_ratings == 0].index
        
        # Exclude movies from watch history to avoid repetition
        if user_watched_movies:
            unwatched_movies = [m for m in unwatched_movies if m not in user_watched_movies]
        
        # Tính toán điểm dự đoán cho các phim chưa xem
        user_idx = self.ratings_matrix.index.get_loc(user_id)
        user_similarities = self.user_similarity[user_idx]
        
        # Lấy thể loại của phim người dùng đã đánh giá cao (>= 4 sao)
        user_high_ratings = self.ratings_matrix.loc[user_id]
        high_rated_movies = user_high_ratings[user_high_ratings >= 4.0].index
        
        preferred_genres = set()
        for movie_id in high_rated_movies:
            movie_info = self.movie_model.get_movie_by_id(movie_id)
            if movie_info:
                genres = str(movie_info.get('genres', '')).lower().split('|')
                for genre in genres:
                    genre = genre.strip()
                    if genre:
                        preferred_genres.add(genre)
        
        predictions = []
        for movie_id in unwatched_movies:
            movie_ratings = self.ratings_matrix[movie_id]
            # Tính điểm dự đoán dựa trên đánh giá của người dùng tương tự
            similarity_sum = np.sum(np.abs(user_similarities))
            if similarity_sum > 0:
                pred_rating = np.sum(user_similarities * movie_ratings) / similarity_sum
            else:
                pred_rating = movie_ratings.mean()
            predictions.append((movie_id, pred_rating))
        
        # Sắp xếp và lấy top N phim
        predictions.sort(key=lambda x: x[1], reverse=True)
        top_movies = []
        
        # Áp dụng genre filtering để đảm bảo relevance
        for movie_id, pred_rating in predictions:
            movie_info = self.movie_model.get_movie_by_id(movie_id)
            if movie_info:
                # Nếu có preferred genres, ưu tiên phim khớp thể loại
                if preferred_genres:
                    movie_genres = str(movie_info.get('genres', '')).lower().split('|')
                    genre_match = any(g.strip() in preferred_genres for g in movie_genres if g.strip())
                    
                    # Boost score nếu khớp thể loại
                    if genre_match:
                        movie_info['predicted_rating'] = float(pred_rating * 1.15)
                    else:
                        movie_info['predicted_rating'] = float(pred_rating)
                else:
                    movie_info['predicted_rating'] = float(pred_rating)
                
                top_movies.append(movie_info)
                
                if len(top_movies) >= n_recommendations * 2:
                    break
        
        # Re-sort sau khi boost
        top_movies.sort(key=lambda x: x.get('predicted_rating', 0), reverse=True)
        
        return top_movies[:n_recommendations] 