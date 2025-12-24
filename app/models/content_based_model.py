import pandas as pd
import numpy as np
import sys
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.movie_model import MovieModel

class ContentBasedModel:
    def __init__(self, data_dir=None):
        # Use MovieModel to load movies data (handles missing files)
        self.movie_model = MovieModel(data_dir=data_dir)
        self.tfidf_matrix = None
        self.movie_similarity = None
        self.movies_df = None
        self._build_model()
    
    def _build_model(self):
        """
        Xây dựng ma trận TF-IDF và tính toán độ tương đồng giữa các phim
        """
        try:
            # Use movies_df from MovieModel
            self.movies_df = self.movie_model.movies_df

            required_columns = ['title', 'overview', 'genres']
            missing_columns = [col for col in required_columns if col not in self.movies_df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in movies.csv: {missing_columns}")

            if self.movies_df.empty:
                self.tfidf_matrix = None
                self.movie_similarity = None
                return

            # Combine textual fields
            self.movies_df['content'] = self.movies_df['overview'].fillna('') + ' ' + self.movies_df['genres'].fillna('')

            # Build TF-IDF and similarity matrix
            tfidf = TfidfVectorizer(stop_words='english')
            self.tfidf_matrix = tfidf.fit_transform(self.movies_df['content'])
            self.movie_similarity = cosine_similarity(self.tfidf_matrix)

        except Exception as e:
            print(f"Error building content-based model: {str(e)}")
            self.tfidf_matrix = None
            self.movie_similarity = None
            self.movies_df = pd.DataFrame()
    
    def get_recommendations(self, movie_id=None, n_recommendations=10):
        """
        Lấy gợi ý phim dựa trên Content-based Filtering
        """
        if self.movie_similarity is None or self.movies_df.empty:
            return []
            
        if movie_id is None:
            # Nếu không có movie_id, lấy phim có đánh giá cao nhất
            movie_id = self.movie_model.ratings_df.groupby('movieId')['rating'].mean().idxmax()
        
        # Lấy index của phim trong ma trận
        movie_idx = self.movies_df[self.movies_df['id'] == movie_id].index[0]
        
        # Lấy độ tương đồng với phim được chọn
        movie_similarities = self.movie_similarity[movie_idx]
        
        # Lấy top N phim tương tự
        similar_movie_indices = movie_similarities.argsort()[::-1][1:n_recommendations+1]
        similar_movies = self.movies_df.iloc[similar_movie_indices]
        
        # Thêm thông tin độ tương đồng vào kết quả
        recommendations = []
        for idx, movie in similar_movies.iterrows():
            movie_dict = movie.to_dict()
            movie_dict['similarity_score'] = movie_similarities[idx]
            recommendations.append(movie_dict)
        
        return recommendations 