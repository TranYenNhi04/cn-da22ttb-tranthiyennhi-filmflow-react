import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/data
DATA_DIR = os.path.join(BASE_DIR)                      # app/data
RAW_DIR = os.path.join(DATA_DIR, 'raw')                # app/data/raw
os.makedirs(RAW_DIR, exist_ok=True)                   # tạo raw nếu chưa có

def preprocess_movies_data():
    print("Đang xử lý dữ liệu phim...")
    movies_df = pd.read_csv(os.path.join(RAW_DIR, 'movies_metadata.csv'))
    selected_columns = ['id', 'title', 'overview', 'genres', 'release_date', 'vote_average', 'vote_count']
    movies_df = movies_df[selected_columns]
    
    movies_df['overview'] = movies_df['overview'].fillna('')
    movies_df['genres'] = movies_df['genres'].fillna('[]')
    movies_df['vote_average'] = movies_df['vote_average'].fillna(0)
    movies_df['vote_count'] = movies_df['vote_count'].fillna(0)
    movies_df['release_date'] = movies_df['release_date'].fillna('')
    movies_df['year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
    movies_df['id'] = pd.to_numeric(movies_df['id'], errors='coerce')
    movies_df = movies_df.dropna(subset=['id', 'title'])
    movies_df['id'] = movies_df['id'].astype(int)
    
    movies_df = movies_df[movies_df['vote_count'] > 0]
    movies_df = movies_df.sort_values('vote_count', ascending=False).head(5000)
    
    movies_df.to_csv(os.path.join(DATA_DIR, 'movies_processed.csv'), index=False)
    print(f"Đã xử lý xong dữ liệu phim. Số lượng phim: {len(movies_df)}")

def preprocess_ratings_data():
    print("Đang xử lý dữ liệu đánh giá...")
    ratings_df = pd.read_csv(os.path.join(RAW_DIR, 'ratings_small.csv'))
    movies_df = pd.read_csv(os.path.join(DATA_DIR, 'movies_processed.csv'))
    
    valid_movie_ids = set(movies_df['id'])
    ratings_df = ratings_df[ratings_df['movieId'].isin(valid_movie_ids)]
    
    user_rating_counts = ratings_df['userId'].value_counts()
    active_users = user_rating_counts[user_rating_counts >= 20].index
    ratings_df = ratings_df[ratings_df['userId'].isin(active_users)]
    
    ratings_df.to_csv(os.path.join(DATA_DIR, 'ratings_processed.csv'), index=False)
    print(f"Đã xử lý xong dữ liệu đánh giá. Số lượng đánh giá: {len(ratings_df)}")

def main():
    preprocess_movies_data()
    preprocess_ratings_data()
    print("Hoàn thành tiền xử lý dữ liệu!")

if __name__ == "__main__":
    main()
