import pandas as pd
import numpy as np
import sys
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.movie_model import MovieModel

def parse_genres(genres_data):
    """Parse genres from JSON string to set of genre names"""
    if pd.isna(genres_data) or genres_data == '[]' or genres_data == '':
        return set()
    try:
        genres_list = json.loads(genres_data) if isinstance(genres_data, str) else genres_data
        if isinstance(genres_list, list):
            return set([g.get('name', '') for g in genres_list if g.get('name')])
    except:
        return set()
    return set()

def genres_to_text(genres_data):
    """Convert genres JSON to text for TF-IDF"""
    genres_set = parse_genres(genres_data)
    return ' '.join(genres_set)

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
        Sử dụng nhiều features: genres, cast, director, keywords, overview
        """
        try:
            # Use movies_df from MovieModel
            self.movies_df = self.movie_model.movies_df

            required_columns = ['title']
            missing_columns = [col for col in required_columns if col not in self.movies_df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in movies.csv: {missing_columns}")

            if self.movies_df.empty:
                self.tfidf_matrix = None
                self.movie_similarity = None
                return

            # Build rich content combining multiple features with appropriate weights
            # Genres: 7x weight (MOST CRITICAL - phải match genre trước tiên, tăng từ x5)
            genres_text = self.movies_df['genres'].apply(genres_to_text).fillna('')
            genres_weighted = (genres_text + ' ') * 7
            
            # Overview: 4x weight (chứa keywords quan trọng như "Godzilla", "monster", "zombie")
            overview = ((self.movies_df['overview'].fillna('') + ' ') * 4) if 'overview' in self.movies_df.columns else ''
            
            # Keywords: 3x weight (quan trọng cho content matching)
            keywords_weighted = (self.movies_df['keywords'].fillna('') + ' ') * 3 if 'keywords' in self.movies_df.columns else ''
            
            # Director: 1x weight (giảm xuống vì có thể làm nhiễu)
            director_weighted = (self.movies_df['director'].fillna('') + ' ') * 1 if 'director' in self.movies_df.columns else ''
            
            # Cast: 1x weight (giảm xuống để tránh gợi ý sai do cùng diễn viên)
            def extract_cast(cast_data):
                """Safely extract cast names from JSON string"""
                if pd.isna(cast_data) or cast_data == '[]' or cast_data == '':
                    return ''
                try:
                    import json
                    cast_list = json.loads(cast_data) if isinstance(cast_data, str) else cast_data
                    if isinstance(cast_list, list):
                        return ' '.join([actor.get('name', '') for actor in cast_list[:3]])  # Chỉ lấy 3 actors
                except:
                    return ''
                return ''
            
            cast_text = self.movies_df['cast_data'].apply(extract_cast) if 'cast_data' in self.movies_df.columns else pd.Series([''] * len(self.movies_df))
            cast_weighted = (cast_text + ' ') * 1
            
            # Tagline: 1x weight
            tagline = self.movies_df['tagline'].fillna('') if 'tagline' in self.movies_df.columns else ''
            
            # Combine all features với thứ tự ưu tiên: Genres > Overview > Keywords > Director > Cast > Tagline
            self.movies_df['content'] = (
                genres_weighted.astype(str) + 
                overview.astype(str) +
                (keywords_weighted.astype(str) if isinstance(keywords_weighted, pd.Series) else '') +
                (director_weighted.astype(str) if isinstance(director_weighted, pd.Series) else '') +
                cast_weighted.astype(str) +
                (tagline.astype(str) if isinstance(tagline, pd.Series) else '')
            )

            # Build TF-IDF with optimized parameters for better similarity detection
            tfidf = TfidfVectorizer(
                stop_words='english',
                max_features=5000,  # Limit features for performance
                ngram_range=(1, 2),  # Use unigrams and bigrams
                min_df=2  # Ignore very rare terms
            )
            self.tfidf_matrix = tfidf.fit_transform(self.movies_df['content'])
            self.movie_similarity = cosine_similarity(self.tfidf_matrix)

        except Exception as e:
            print(f"Error building content-based model: {str(e)}")
            import traceback
            traceback.print_exc()
            self.tfidf_matrix = None
            self.movie_similarity = None
            self.movies_df = pd.DataFrame()
    
    def get_recommendations(self, movie_id=None, n_recommendations=10):
        """
        Lấy gợi ý phim dựa trên Content-based Filtering với scoring thông minh
        """
        if self.movie_similarity is None or self.movies_df.empty:
            return []
            
        if movie_id is None:
            # Nếu không có movie_id, lấy phim có đánh giá cao nhất
            if not self.movie_model.ratings_df.empty:
                movie_id = self.movie_model.ratings_df.groupby('movieId')['rating'].mean().idxmax()
            else:
                # Fallback: top rated movie by vote_average
                if 'vote_average' in self.movies_df.columns:
                    movie_id = self.movies_df.nlargest(1, 'vote_average')['id'].iloc[0]
                else:
                    return []
        
        # Tìm index của phim trong dataframe
        movie_matches = self.movies_df[self.movies_df['id'] == movie_id]
        if movie_matches.empty:
            print(f"⚠️ Movie {movie_id} not found in content-based model")
            return []
        
        movie_idx = movie_matches.index[0]
        source_movie = self.movies_df.iloc[movie_idx]
        
        # Lấy độ tương đồng với phim được chọn
        movie_similarities = self.movie_similarity[movie_idx]
        
        # Tạo dataframe với similarity scores và additional scoring factors
        similar_df = self.movies_df.copy()
        similar_df['similarity_score'] = movie_similarities
        
        # CRITICAL: Filter out movies with NO genre overlap (tránh gợi ý phim hoàn toàn khác thể loại)
        if 'genres' in similar_df.columns and pd.notna(source_movie.get('genres')):
            source_genres = parse_genres(source_movie.get('genres', ''))
            
            def has_genre_overlap(genres):
                """Check if movie has at least 1 common genre"""
                movie_genres = parse_genres(genres)
                return len(source_genres & movie_genres) > 0
            
            # Chỉ giữ phim có ít nhất 1 thể loại chung
            similar_df = similar_df[similar_df['genres'].apply(has_genre_overlap)]
        
        # Bonus scoring cho các phim có cùng:
        # 1. Genres overlap (tối đa +0.40 - TĂNG MẠNH để ưu tiên genre matching)
        if 'genres' in similar_df.columns:
            source_genres = parse_genres(source_movie.get('genres', ''))
            similar_df['genre_bonus'] = similar_df['genres'].apply(
                lambda x: min(0.40, len(source_genres & parse_genres(x)) * 0.10)  # 0.10 per genre match
            )
        else:
            similar_df['genre_bonus'] = 0
        
        # 2. Franchise/Title similarity bonus (+0.30 if title contains common keywords)
        if 'title' in similar_df.columns and pd.notna(source_movie.get('title')):
            source_title_words = set(str(source_movie['title']).lower().split())
            # Remove common words
            common_words = {'the', 'a', 'an', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for'}
            source_title_words = source_title_words - common_words
            
            def check_title_similarity(title):
                if pd.isna(title):
                    return 0
                title_words = set(str(title).lower().split()) - common_words
                # If any significant word matches, give big bonus (franchise/series)
                if len(source_title_words & title_words) > 0:
                    return 0.30
                return 0
            
            similar_df['title_bonus'] = similar_df['title'].apply(check_title_similarity)
        else:
            similar_df['title_bonus'] = 0
        
        # 3. Same director (giảm xuống +0.05 để tránh overweight)
        if 'director' in similar_df.columns and pd.notna(source_movie.get('director')):
            similar_df['director_bonus'] = similar_df['director'].apply(
                lambda x: 0.05 if pd.notna(x) and x == source_movie['director'] else 0
            )
        else:
            similar_df['director_bonus'] = 0
        
        # 4. Similar year (±5 years: +0.05)
        if 'year' in similar_df.columns and pd.notna(source_movie.get('year')):
            source_year = source_movie['year']
            similar_df['year_bonus'] = similar_df['year'].apply(
                lambda x: 0.05 if pd.notna(x) and abs(x - source_year) <= 5 else 0
            )
        else:
            similar_df['year_bonus'] = 0
        
        # 5. Quality factor: vote_average >= 6.0 gets small boost
        if 'vote_average' in similar_df.columns:
            similar_df['quality_bonus'] = similar_df['vote_average'].apply(
                lambda x: 0.03 if pd.notna(x) and x >= 6.0 else 0
            )
        else:
            similar_df['quality_bonus'] = 0
        
        # Calculate final score
        similar_df['final_score'] = (
            similar_df['similarity_score'] + 
            similar_df['genre_bonus'] + 
            similar_df['title_bonus'] +
            similar_df['director_bonus'] +
            similar_df['year_bonus'] +
            similar_df['quality_bonus']
        )
        
        # Loại bỏ phim gốc và sort theo final_score
        similar_df = similar_df[similar_df['id'] != movie_id]
        similar_df = similar_df.sort_values('final_score', ascending=False)
        
        # Lấy top N recommendations
        top_similar = similar_df.head(n_recommendations)
        
        # Convert to list of dicts
        recommendations = []
        for idx, movie in top_similar.iterrows():
            movie_dict = movie.to_dict()
            # Handle NaN values before JSON serialization
            for key, value in movie_dict.items():
                if pd.isna(value):
                    movie_dict[key] = None
                elif isinstance(value, (np.floating, float)):
                    if np.isnan(value) or np.isinf(value):
                        movie_dict[key] = None
                    else:
                        movie_dict[key] = float(value)
            
            movie_dict['similarity_score'] = float(movie['similarity_score']) if not pd.isna(movie['similarity_score']) else 0.0
            movie_dict['final_score'] = float(movie['final_score']) if not pd.isna(movie['final_score']) else 0.0
            recommendations.append(movie_dict)
        
        return recommendations 