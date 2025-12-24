import pandas as pd
import os
try:
    from app.data import database
except Exception:
    # fallback when package root is different inside containers
    from data import database


def _safe_read_csv(path, default_columns=None, usecols=None, low_memory=True):
    """Read CSV safely: return empty DataFrame with `default_columns` when file is missing/empty."""
    if not os.path.exists(path):
        if default_columns is not None:
            return pd.DataFrame(columns=default_columns)
        raise FileNotFoundError(f"Required data file not found: {path}")

    try:
        # If file exists but is empty, return empty DataFrame with columns
        if os.path.getsize(path) == 0:
            return pd.DataFrame(columns=default_columns if default_columns is not None else [])
        
        # Optimize memory usage
        return pd.read_csv(
            path, 
            low_memory=low_memory,
            usecols=usecols,
            dtype={'id': 'int32'} if 'id' in (usecols or []) else None,
            engine='c'
        )
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=default_columns if default_columns is not None else [])


class MovieModel:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # mặc định chạy local
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, 'app', 'data')

        movies_path = os.path.join(data_dir, 'movies_processed.csv')
        ratings_path = os.path.join(data_dir, 'ratings_processed.csv')
        reviews_path = os.path.join(data_dir, 'reviews.csv')

        # Read movies from CSV (static metadata)
        self.movies_df = _safe_read_csv(movies_path)

        # Initialize database and import CSVs into SQLite if needed
        try:
            database.init_db(data_dir)
        except Exception:
            # ignore DB init failures for environments without pandas/sqlite
            pass

        # Load ratings/reviews from DB (fallback to CSV if DB not available)
        try:
            self.ratings_df = database.fetch_ratings_df(data_dir)
        except Exception:
            self.ratings_df = _safe_read_csv(ratings_path)

        try:
            self.reviews_df = database.fetch_reviews_df(data_dir)
        except Exception:
            self.reviews_df = _safe_read_csv(reviews_path, default_columns=['movieId', 'userId', 'rating', 'review'])

        self.data_dir = data_dir
        self.reviews_path = reviews_path
        # Precompute lowercase titles for fast searching/autocomplete
        try:
            if 'title' in self.movies_df.columns:
                self.movies_df['title_lower'] = self.movies_df['title'].astype(str).str.lower()
            else:
                self.movies_df['title_lower'] = ''
        except Exception:
            self.movies_df['title_lower'] = ''

    def search_movies(self, query):
        """Search movies by partial/prefix matching with relevance scoring.
        
        Returns results sorted by relevance:
        1. Exact title match (case-insensitive)
        2. Title starts with query
        3. Title contains query
        Then sorted by vote_average descending.
        """
        if not query or not query.strip():
            return []
        
        query_lower = query.lower().strip()
        df = self.movies_df.copy()
        df['title_lower'] = df['title'].str.lower()
        
        # Score matches: higher score = better match
        df['relevance'] = 0
        
        # Exact match: score 3
        df.loc[df['title_lower'] == query_lower, 'relevance'] = 3
        
        # Starts with query: score 2
        df.loc[df['title_lower'].str.startswith(query_lower), 'relevance'] = 2
        
        # Contains query: score 1
        df.loc[df['title_lower'].str.contains(query_lower, case=False, na=False), 'relevance'] = 1
        
        # Filter to matches only
        results = df[df['relevance'] > 0].copy()
        
        # Sort by: relevance (desc), then vote_average (desc)
        results = results.sort_values(
            by=['relevance', 'vote_average'],
            ascending=[False, False]
        ).head(20)  # Limit to top 20 results
        
        # Return as list of dicts, drop helper columns
        return results.drop(columns=['title_lower', 'relevance']).to_dict('records')

    def autocomplete(self, query, n=10):
        """Fast autocomplete: return up to `n` movies matching the query prefix or word-start.

        Strategy:
        - normalize query to lowercase
        - exact title match -> score 4
        - title startswith query -> score 3
        - any word in title startswith query -> score 2
        - contains query anywhere -> score 1
        Returns list of dicts with same shape as search results.
        """
        if not query or not query.strip():
            return []
        q = query.lower().strip()
        df = self.movies_df.copy()

        # initialize score
        df['score'] = 0

        # exact match
        try:
            df.loc[df['title_lower'] == q, 'score'] = 4
        except Exception:
            pass

        # startswith full title
        try:
            df.loc[df['title_lower'].str.startswith(q, na=False), 'score'] = df['score'].clip(lower=3)
        except Exception:
            pass

        # any word startswith
        try:
            df_word = df['title_lower'].str.split('\\s+')
            mask = df_word.apply(lambda toks: any(t.startswith(q) for t in toks) if isinstance(toks, list) else False)
            df.loc[mask, 'score'] = df['score'].clip(lower=2)
        except Exception:
            pass

        # contains
        try:
            df.loc[df['title_lower'].str.contains(q, case=False, na=False), 'score'] = df['score'].clip(lower=1)
        except Exception:
            pass

        results = df[df['score'] > 0].copy()
        if results.empty:
            return []

        results = results.sort_values(by=['score', 'vote_average'], ascending=[False, False]).head(n)
        # drop helper cols
        for col in ['title_lower', 'score']:
            if col in results.columns:
                results = results.drop(columns=[col])
        return results.to_dict('records')
    
    def get_movie_by_id(self, movie_id):
        movie = self.movies_df[self.movies_df['id'] == movie_id]
        if not movie.empty:
            return movie.iloc[0].to_dict()
        return None
    
    def add_review(self, movie_id, rating, review, username="Anonymous"):
        """Add a review to the persistent DB (and fallback CSV if DB unavailable)."""
        try:
            database.insert_review(movie_id, username, rating, review, data_dir=self.data_dir)
            # refresh in-memory dataframe
            self.reviews_df = database.fetch_reviews_df(self.data_dir)
            print(f"✓ Review saved to DB: movie_id={movie_id}, username={username}, rating={rating}")
            return True
        except Exception:
            # fallback to CSV append
            import datetime
            new_review = pd.DataFrame({
                'movieId': [movie_id],
                'userId': [username],
                'rating': [rating],
                'review': [review],
                'timestamp': [datetime.datetime.now().isoformat()]
            })
            self.reviews_df = pd.concat([self.reviews_df, new_review], ignore_index=True)
            try:
                self.reviews_df.to_csv(self.reviews_path, index=False)
            except Exception:
                pass
            print(f"✓ Review saved to CSV fallback: movie_id={movie_id}, username={username}, rating={rating}")
            return True

    def add_user(self, user_id, metadata=None):
        try:
            database.insert_user(user_id, metadata, data_dir=self.data_dir)
            return True
        except Exception:
            return False

    def add_item(self, movie_id, title=None, metadata=None):
        try:
            database.insert_item(movie_id, title, metadata, data_dir=self.data_dir)
            return True
        except Exception:
            return False

    def record_view(self, movie_id, user_id='Anonymous'):
        try:
            database.record_view(user_id, movie_id, data_dir=self.data_dir)
            return True
        except Exception:
            return False

    def record_click(self, movie_id, user_id='Anonymous'):
        try:
            database.record_click(user_id, movie_id, data_dir=self.data_dir)
            return True
        except Exception:
            return False

    def record_rating(self, movie_id, user_id='Anonymous', rating=5):
        try:
            database.insert_rating(movie_id, user_id, rating, data_dir=self.data_dir)
            # refresh ratings_df
            try:
                self.ratings_df = database.fetch_ratings_df(self.data_dir)
            except Exception:
                pass
            return True
        except Exception:
            return False
    
    def get_movie_reviews(self, movie_id):
        return self.reviews_df[self.reviews_df['movieId'] == movie_id].to_dict('records')

    def add_comment(self, movie_id, user_id, comment_text):
        try:
            database.insert_comment(movie_id, user_id, comment_text, data_dir=self.data_dir)
            return True
        except Exception:
            return False

    def get_movie_comments(self, movie_id, limit=50, offset=0):
        try:
            return database.fetch_comments(movie_id, limit=limit, offset=offset, data_dir=self.data_dir)
        except Exception:
            # fallback to no comments
            return []

    def add_interaction(self, movie_id, user_id='Anonymous', action='like'):
        """Persist simple interactions like 'like'/'dislike'."""
        try:
            database.insert_interaction(user_id, movie_id, action, data_dir=self.data_dir)
            print(f"✓ Interaction saved: {action} movie {movie_id} by {user_id}")
            return True
        except Exception:
            # if DB not available, no-op but return False
            print(f"⚠ Failed to persist interaction to DB: {action} {movie_id}")
            return False

    def get_trending_movies(self, limit=20):
        """Lấy phim trending dựa trên views, ratings gần đây, và interactions.
        
        Vieon-style: Kết hợp:
        - Số lượng views gần đây (24h, 7d)
        - Average rating cao
        - Số lượng ratings/interactions
        """
        try:
            # Lấy phim có interactions gần đây từ DB
            trending_data = database.get_trending_movies(limit=limit, data_dir=self.data_dir)
            if trending_data:
                # Enrich with full movie data from CSV
                movie_ids = [m.get('movieId') or m.get('id') for m in trending_data if m.get('movieId') or m.get('id')]
                if movie_ids and len(self.movies_df) > 0:
                    movies_dict = self.movies_df[self.movies_df['id'].isin(movie_ids)].set_index('id').to_dict('index')
                    for item in trending_data:
                        mid = item.get('movieId') or item.get('id')
                        if mid in movies_dict:
                            # Merge interaction data with full movie data
                            item.update(movies_dict[mid])
                return trending_data
        except Exception:
            pass
        
        # Fallback: lấy top rated films từ CSV
        if len(self.movies_df) > 0:
            df = self.movies_df.copy()
            # Ensure vote_average exists and sort
            if 'vote_average' in df.columns:
                df = df.dropna(subset=['vote_average'])
                df = df.sort_values('vote_average', ascending=False).head(limit)
                return df.to_dict('records')
        
        return []

    def get_new_releases(self, limit=20):
        """Lấy phim mới nhất."""
        try:
            df = self.movies_df.copy()
            if 'release_date' in df.columns:
                df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
                df = df.dropna(subset=['release_date'])
                df = df.sort_values('release_date', ascending=False).head(limit)
                return df.to_dict('records')
            elif 'year' in df.columns:
                df = df.sort_values('year', ascending=False).head(limit)
                return df.to_dict('records')
        except Exception:
            pass
        
        return self.get_all_movies(limit=limit)

    def get_all_movies(self, limit=None):
        """Lấy tất cả phim hoặc limit."""
        df = self.movies_df.copy()
        if limit:
            df = df.head(limit)
        return df.to_dict('records')
