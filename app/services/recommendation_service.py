"""
Advanced Recommendation Service
Triển khai content-based, collaborative filtering và hybrid recommendations
với cold-start handling và personalization
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import json

from data.models import (
    Movie, Rating, UserEvent, UserProfile,
    WatchHistory, RecommendationCache
)


class AdvancedRecommendationService:
    """
    Service cung cấp recommendations với nhiều strategies
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.tfidf = None
        self.movie_features = None
        self.user_item_matrix = None
        
    # ==================== CONTENT-BASED FILTERING ====================
    
    def get_content_based_recommendations(
        self,
        movie_id: str,
        n: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Content-based recommendations dựa trên similarity của movie features
        
        Args:
            movie_id: ID của movie làm base
            n: Số recommendations
            filters: Filters (year, genres, etc.)
        """
        # Get target movie
        target_movie = self.db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not target_movie:
            return []
        
        # Build TF-IDF matrix nếu chưa có
        if self.tfidf is None or self.movie_features is None:
            self._build_content_features()
        
        # Get similar movies
        similar_movies = self._find_similar_movies(
            movie_id, 
            n=n*2,  # Get more to filter
            filters=filters
        )
        
        # Format results
        results = []
        for movie, score in similar_movies[:n]:
            results.append({
                'movie_id': movie.movie_id,
                'title': movie.title,
                'score': float(score),
                'reason': f'Similar to {target_movie.title}',
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'year': movie.year,
                'genres': movie.genres
            })
        
        return results
    
    def _build_content_features(self):
        """Build TF-IDF features từ movie metadata"""
        movies = self.db.query(Movie).all()
        
        # Combine features: overview + genres + keywords
        texts = []
        movie_ids = []
        
        for movie in movies:
            # Combine text features
            text_parts = []
            
            if movie.overview:
                text_parts.append(movie.overview)
            
            if movie.genres:
                genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                genre_names = [g['name'] if isinstance(g, dict) else g for g in genres]
                text_parts.extend(genre_names * 3)  # Weight genres more
            
            if movie.keywords:
                text_parts.append(movie.keywords)
            
            if movie.director:
                text_parts.append(movie.director * 2)  # Weight director
            
            texts.append(' '.join(text_parts))
            movie_ids.append(movie.movie_id)
        
        # Build TF-IDF
        self.tfidf = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.movie_features = self.tfidf.fit_transform(texts)
        self.movie_id_to_index = {mid: i for i, mid in enumerate(movie_ids)}
    
    def _find_similar_movies(
        self,
        movie_id: str,
        n: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Tuple]:
        """Find similar movies using cosine similarity"""
        if movie_id not in self.movie_id_to_index:
            return []
        
        idx = self.movie_id_to_index[movie_id]
        movie_vector = self.movie_features[idx]
        
        # Calculate similarities
        similarities = cosine_similarity(movie_vector, self.movie_features).flatten()
        
        # Get top similar (excluding self)
        similar_indices = similarities.argsort()[::-1][1:n+100]
        
        # Get movies
        movies = self.db.query(Movie).all()
        similar_movies = []
        
        for idx in similar_indices:
            movie = movies[idx]
            
            # Apply filters
            if filters:
                if 'year' in filters and movie.year != filters['year']:
                    continue
                if 'min_rating' in filters and (movie.vote_average or 0) < filters['min_rating']:
                    continue
            
            similar_movies.append((movie, similarities[idx]))
            
            if len(similar_movies) >= n:
                break
        
        return similar_movies
    
    # ==================== COLLABORATIVE FILTERING ====================
    
    def get_collaborative_recommendations(
        self,
        user_id: str,
        n: int = 10,
        method: str = 'user_based'  # user_based or item_based
    ) -> List[Dict]:
        """
        Collaborative filtering recommendations
        
        Args:
            user_id: User ID
            n: Số recommendations
            method: 'user_based' hoặc 'item_based'
        """
        # Get user ratings
        user_ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).all()
        
        if not user_ratings:
            # Cold start - return popular
            return self.get_popular_recommendations(n=n)
        
        if method == 'user_based':
            return self._user_based_cf(user_id, n)
        else:
            return self._item_based_cf(user_id, n)
    
    def _user_based_cf(self, user_id: str, n: int) -> List[Dict]:
        """User-based collaborative filtering"""
        # Get all ratings
        ratings_data = []
        for rating in self.db.query(Rating).all():
            ratings_data.append({
                'user_id': rating.user_id,
                'movie_id': rating.movie_id,
                'rating': rating.rating
            })
        
        if not ratings_data:
            return []
        
        df = pd.DataFrame(ratings_data)
        
        # Create user-item matrix
        user_item_matrix = df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            fill_value=0
        )
        
        if user_id not in user_item_matrix.index:
            return []
        
        # Calculate user similarities
        user_vector = user_item_matrix.loc[user_id].values.reshape(1, -1)
        similarities = cosine_similarity(user_vector, user_item_matrix.values).flatten()
        
        # Find similar users (excluding self)
        similar_user_indices = similarities.argsort()[::-1][1:21]
        similar_users = user_item_matrix.index[similar_user_indices].tolist()
        
        # Get movies rated by similar users but not by target user
        user_movies = set(df[df['user_id'] == user_id]['movie_id'].values)
        
        candidate_movies = {}
        for sim_user in similar_users:
            sim_user_movies = df[df['user_id'] == sim_user]
            for _, row in sim_user_movies.iterrows():
                movie_id = row['movie_id']
                if movie_id not in user_movies:
                    if movie_id not in candidate_movies:
                        candidate_movies[movie_id] = []
                    candidate_movies[movie_id].append(row['rating'])
        
        # Calculate predicted ratings
        movie_scores = []
        for movie_id, ratings in candidate_movies.items():
            avg_rating = np.mean(ratings)
            movie_scores.append((movie_id, avg_rating, len(ratings)))
        
        # Sort by score
        movie_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Get movie details
        results = []
        for movie_id, score, count in movie_scores[:n]:
            movie = self.db.query(Movie).filter(Movie.movie_id == movie_id).first()
            if movie:
                results.append({
                    'movie_id': movie.movie_id,
                    'title': movie.title,
                    'score': float(score),
                    'reason': f'Recommended by similar users ({count} ratings)',
                    'poster_url': movie.poster_url,
                    'vote_average': movie.vote_average,
                    'year': movie.year,
                    'genres': movie.genres
                })
        
        return results
    
    def _item_based_cf(self, user_id: str, n: int) -> List[Dict]:
        """Item-based collaborative filtering"""
        # Get user's rated movies
        user_ratings = self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(Rating.rating.desc()).limit(10).all()
        
        if not user_ratings:
            return []
        
        # For each liked movie, get similar movies
        all_recommendations = []
        
        for rating in user_ratings:
            if rating.rating >= 4.0:  # Only from liked movies
                similar = self.get_content_based_recommendations(
                    movie_id=rating.movie_id,
                    n=5
                )
                for rec in similar:
                    rec['base_movie'] = rating.movie_id
                    rec['user_rating'] = rating.rating
                all_recommendations.extend(similar)
        
        # Aggregate scores
        movie_scores = {}
        for rec in all_recommendations:
            movie_id = rec['movie_id']
            score = rec['score'] * rec['user_rating']
            
            if movie_id in movie_scores:
                movie_scores[movie_id]['score'] += score
                movie_scores[movie_id]['count'] += 1
            else:
                movie_scores[movie_id] = {
                    **rec,
                    'score': score,
                    'count': 1
                }
        
        # Sort and return
        results = sorted(
            movie_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:n]
        
        return results
    
    # ==================== HYBRID RECOMMENDATIONS ====================
    
    def get_hybrid_recommendations(
        self,
        user_id: str,
        n: int = 10,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Hybrid recommendations kết hợp nhiều strategies
        
        Args:
            user_id: User ID
            n: Số recommendations
            context: Context info (device, time, etc.)
        """
        # Get recommendations from different strategies
        content_recs = []
        collab_recs = self.get_collaborative_recommendations(user_id, n=n*2)
        personalized_recs = self.get_personalized_recommendations(user_id, n=n*2)
        popular_recs = self.get_popular_recommendations(n=n)
        
        # Get user's recently viewed movies for content-based
        recent_views = self.db.query(UserEvent).filter(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.event_type.in_(['view', 'click']),
                UserEvent.movie_id.isnot(None)
            )
        ).order_by(UserEvent.timestamp.desc()).limit(5).all()
        
        for event in recent_views:
            content_recs.extend(
                self.get_content_based_recommendations(event.movie_id, n=5)
            )
        
        # Combine and score
        all_recs = {}
        
        # Content-based: weight 0.3
        for rec in content_recs:
            movie_id = rec['movie_id']
            if movie_id not in all_recs:
                all_recs[movie_id] = {**rec, 'combined_score': 0, 'sources': []}
            all_recs[movie_id]['combined_score'] += rec['score'] * 0.3
            all_recs[movie_id]['sources'].append('content')
        
        # Collaborative: weight 0.4
        for rec in collab_recs:
            movie_id = rec['movie_id']
            if movie_id not in all_recs:
                all_recs[movie_id] = {**rec, 'combined_score': 0, 'sources': []}
            all_recs[movie_id]['combined_score'] += rec['score'] * 0.4
            all_recs[movie_id]['sources'].append('collaborative')
        
        # Personalized: weight 0.5
        for rec in personalized_recs:
            movie_id = rec['movie_id']
            if movie_id not in all_recs:
                all_recs[movie_id] = {**rec, 'combined_score': 0, 'sources': []}
            all_recs[movie_id]['combined_score'] += rec['score'] * 0.5
            all_recs[movie_id]['sources'].append('personalized')
        
        # Popular as fallback: weight 0.2
        for rec in popular_recs:
            movie_id = rec['movie_id']
            if movie_id not in all_recs:
                all_recs[movie_id] = {**rec, 'combined_score': 0, 'sources': []}
            all_recs[movie_id]['combined_score'] += rec['score'] * 0.2
            all_recs[movie_id]['sources'].append('popular')
        
        # Remove already watched
        watched = self._get_watched_movies(user_id)
        for movie_id in watched:
            all_recs.pop(movie_id, None)
        
        # Sort by combined score
        results = sorted(
            all_recs.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:n]
        
        # Update reasons
        for rec in results:
            sources = rec.get('sources', [])
            rec['reason'] = f"Recommended based on {', '.join(set(sources))}"
        
        return results
    
    # ==================== PERSONALIZED RECOMMENDATIONS ====================
    
    def get_personalized_recommendations(
        self,
        user_id: str,
        n: int = 10
    ) -> List[Dict]:
        """
        Personalized recommendations dựa trên user profile và behavior
        """
        # Get user profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return self.get_popular_recommendations(n=n)
        
        # Get candidate movies
        movies = self.db.query(Movie).filter(
            Movie.vote_average >= 6.0
        ).all()
        
        # Score each movie
        scored_movies = []
        for movie in movies:
            score = self._calculate_personalization_score(movie, profile)
            scored_movies.append((movie, score))
        
        # Sort and filter
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Remove watched
        watched = self._get_watched_movies(user_id)
        filtered = [(m, s) for m, s in scored_movies if m.movie_id not in watched]
        
        # Format results
        results = []
        for movie, score in filtered[:n]:
            results.append({
                'movie_id': movie.movie_id,
                'title': movie.title,
                'score': float(score),
                'reason': 'Personalized for you',
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'year': movie.year,
                'genres': movie.genres
            })
        
        return results
    
    def _calculate_personalization_score(self, movie: Movie, profile: UserProfile) -> float:
        """Calculate personalization score cho một movie"""
        score = 0.0
        
        # Base score from movie rating
        score += (movie.vote_average or 0) * 0.1
        
        # Genre preferences
        if profile.genre_preferences and movie.genres:
            genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
            genre_names = [g['name'] if isinstance(g, dict) else g for g in genres]
            
            for genre in genre_names:
                pref_score = profile.genre_preferences.get(genre, 0)
                score += pref_score * 0.3
        
        # Recency boost
        if movie.year and movie.year >= datetime.now().year - 2:
            score += 0.5
        
        # Popularity boost
        if movie.popularity:
            score += min(movie.popularity / 100, 1.0) * 0.2
        
        return score
    
    # ==================== POPULAR & TRENDING ====================
    
    def get_popular_recommendations(
        self,
        n: int = 10,
        time_window_days: int = 30
    ) -> List[Dict]:
        """Get popular movies based on recent activity"""
        # Calculate popularity from recent events
        start_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        popular_query = self.db.query(
            UserEvent.movie_id,
            func.count(UserEvent.id).label('event_count')
        ).filter(
            and_(
                UserEvent.timestamp >= start_date,
                UserEvent.movie_id.isnot(None)
            )
        ).group_by(UserEvent.movie_id).order_by(
            func.count(UserEvent.id).desc()
        ).limit(n).all()
        
        results = []
        for movie_id, count in popular_query:
            movie = self.db.query(Movie).filter(Movie.movie_id == movie_id).first()
            if movie:
                results.append({
                    'movie_id': movie.movie_id,
                    'title': movie.title,
                    'score': float(count / 100),  # Normalize
                    'reason': f'Popular ({count} views)',
                    'poster_url': movie.poster_url,
                    'vote_average': movie.vote_average,
                    'year': movie.year,
                    'genres': movie.genres
                })
        
        # Fallback to TMDB ratings if not enough data
        if len(results) < n:
            fallback = self.db.query(Movie).order_by(
                Movie.vote_average.desc()
            ).limit(n - len(results)).all()
            
            for movie in fallback:
                if movie.movie_id not in [r['movie_id'] for r in results]:
                    results.append({
                        'movie_id': movie.movie_id,
                        'title': movie.title,
                        'score': (movie.vote_average or 0) / 10,
                        'reason': f'Highly rated ({movie.vote_average:.1f}/10)',
                        'poster_url': movie.poster_url,
                        'vote_average': movie.vote_average,
                        'year': movie.year,
                        'genres': movie.genres
                    })
        
        return results
    
    # ==================== HELPER METHODS ====================
    
    def _get_watched_movies(self, user_id: str) -> set:
        """Get set of movies user has already watched"""
        watched = self.db.query(WatchHistory.movie_id).filter(
            WatchHistory.user_id == user_id
        ).all()
        
        rated = self.db.query(Rating.movie_id).filter(
            Rating.user_id == user_id
        ).all()
        
        return set([w[0] for w in watched] + [r[0] for r in rated])
