import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics.pairwise import cosine_similarity

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.movie_model import MovieModel

class CollaborativeModel:
    def __init__(self, data_dir=None):
        # Use MovieModel as the source of truth for movie & ratings data
        self.movie_model = MovieModel(data_dir=data_dir)
        self.ratings_matrix = None
        self.user_similarity = None
        # build model initially; allow refresh later to pick up new ratings
        self._build_model()
    
    def _build_model(self):
        """
        Xây dựng ma trận đánh giá và tính toán độ tương đồng giữa người dùng
        """
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

        except Exception as e:
            print(f"Error building collaborative model: {str(e)}")
            self.ratings_matrix = pd.DataFrame()
            self.user_similarity = np.array([])

    def refresh(self):
        """Reload ratings from MovieModel and rebuild matrices."""
        # reload ratings_df from the source (which may read from DB)
        try:
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
        Lấy gợi ý phim dựa trên Collaborative Filtering
        """
        # Ensure model is up-to-date with latest ratings
        if self.ratings_matrix is None or (hasattr(self, 'ratings_matrix') and getattr(self, 'ratings_matrix', pd.DataFrame()).empty):
            # Attempt refresh
            self.refresh()

        if self.ratings_matrix is None or self.ratings_matrix.empty:
            return []
            
        if user_id is None:
            # Nếu không có user_id, lấy người dùng có nhiều đánh giá nhất
            user_id = self.ratings_matrix.sum(axis=1).idxmax()
        else:
            # user_id may be numeric or string; ensure it exists in index
            if user_id not in self.ratings_matrix.index:
                # Attempt to refresh once and check again
                self.refresh()
                if user_id not in self.ratings_matrix.index:
                    # fallback to default popular user
                    user_id = self.ratings_matrix.sum(axis=1).idxmax()
        
        # Lấy các phim chưa được đánh giá bởi người dùng
        user_ratings = self.ratings_matrix.loc[user_id]
        unwatched_movies = user_ratings[user_ratings == 0].index
        
        # Tính toán điểm dự đoán cho các phim chưa xem
        user_idx = self.ratings_matrix.index.get_loc(user_id)
        user_similarities = self.user_similarity[user_idx]
        
        predictions = []
        for movie_id in unwatched_movies:
            movie_ratings = self.ratings_matrix[movie_id]
            # Tính điểm dự đoán dựa trên đánh giá của người dùng tương tự
            pred_rating = np.sum(user_similarities * movie_ratings) / np.sum(np.abs(user_similarities))
            predictions.append((movie_id, pred_rating))
        
        # Sắp xếp và lấy top N phim
        predictions.sort(key=lambda x: x[1], reverse=True)
        top_movies = []
        for movie_id, pred_rating in predictions[:n_recommendations]:
            movie_info = self.movie_model.get_movie_by_id(movie_id)
            if movie_info:
                movie_info['predicted_rating'] = pred_rating
                top_movies.append(movie_info)
        
        return top_movies 