"""
Recommendation Evaluation Service
Đánh giá chất lượng recommendations với các metrics chuẩn
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict

from data.models import (
    Rating, UserEvent, RecommendationFeedback,
    ModelPerformance, Movie
)


class RecommendationEvaluationService:
    """
    Service đánh giá chất lượng recommendation models
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== OFFLINE METRICS ====================
    
    def calculate_precision_at_k(
        self,
        recommendations: List[str],
        relevant_items: List[str],
        k: int = 10
    ) -> float:
        """
        Precision@K: Tỷ lệ items relevant trong top K recommendations
        
        Args:
            recommendations: List of recommended movie IDs (sorted by score)
            relevant_items: List of relevant movie IDs (ground truth)
            k: Number of top recommendations to consider
        """
        if not recommendations or not relevant_items:
            return 0.0
        
        top_k = recommendations[:k]
        relevant_in_top_k = len(set(top_k) & set(relevant_items))
        
        return relevant_in_top_k / k
    
    def calculate_recall_at_k(
        self,
        recommendations: List[str],
        relevant_items: List[str],
        k: int = 10
    ) -> float:
        """
        Recall@K: Tỷ lệ relevant items được tìm thấy trong top K
        
        Args:
            recommendations: List of recommended movie IDs
            relevant_items: List of relevant movie IDs (ground truth)
            k: Number of top recommendations to consider
        """
        if not relevant_items:
            return 0.0
        
        top_k = recommendations[:k]
        relevant_in_top_k = len(set(top_k) & set(relevant_items))
        
        return relevant_in_top_k / len(relevant_items)
    
    def calculate_ndcg_at_k(
        self,
        recommendations: List[str],
        relevance_scores: Dict[str, float],
        k: int = 10
    ) -> float:
        """
        NDCG@K (Normalized Discounted Cumulative Gain)
        Đo chất lượng ranking của recommendations
        
        Args:
            recommendations: List of recommended movie IDs (sorted)
            relevance_scores: Dict mapping movie_id -> relevance score (0-5)
            k: Number of top recommendations
        """
        def dcg_at_k(scores, k):
            scores = np.array(scores)[:k]
            if scores.size:
                return np.sum(scores / np.log2(np.arange(2, scores.size + 2)))
            return 0.0
        
        # Calculate DCG
        actual_scores = [relevance_scores.get(movie_id, 0) for movie_id in recommendations[:k]]
        dcg = dcg_at_k(actual_scores, k)
        
        # Calculate IDCG (Ideal DCG)
        ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = dcg_at_k(ideal_scores, k)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def calculate_map(
        self,
        recommendations: List[str],
        relevant_items: List[str]
    ) -> float:
        """
        MAP (Mean Average Precision)
        
        Args:
            recommendations: List of recommended movie IDs
            relevant_items: List of relevant movie IDs
        """
        if not relevant_items:
            return 0.0
        
        score = 0.0
        num_hits = 0.0
        
        for i, movie_id in enumerate(recommendations, 1):
            if movie_id in relevant_items:
                num_hits += 1.0
                score += num_hits / i
        
        if num_hits == 0:
            return 0.0
        
        return score / len(relevant_items)
    
    def calculate_mrr(
        self,
        recommendations: List[str],
        relevant_items: List[str]
    ) -> float:
        """
        MRR (Mean Reciprocal Rank)
        1 / rank của relevant item đầu tiên
        
        Args:
            recommendations: List of recommended movie IDs
            relevant_items: List of relevant movie IDs
        """
        for i, movie_id in enumerate(recommendations, 1):
            if movie_id in relevant_items:
                return 1.0 / i
        
        return 0.0
    
    def calculate_diversity(
        self,
        recommendations: List[str]
    ) -> float:
        """
        Diversity: Đo độ đa dạng của recommendations
        Dựa trên số genres khác nhau
        """
        if not recommendations:
            return 0.0
        
        all_genres = set()
        for movie_id in recommendations:
            movie = self.db.query(Movie).filter(Movie.movie_id == movie_id).first()
            if movie and movie.genres:
                import json
                genres = movie.genres if isinstance(movie.genres, list) else json.loads(movie.genres)
                genre_names = [g['name'] if isinstance(g, dict) else g for g in genres]
                all_genres.update(genre_names)
        
        # Diversity = unique genres / total recommendations
        return len(all_genres) / len(recommendations)
    
    def calculate_coverage(
        self,
        all_recommendations: List[List[str]],
        catalog_size: int
    ) -> float:
        """
        Coverage: % của catalog được recommend
        
        Args:
            all_recommendations: List of recommendation lists for multiple users
            catalog_size: Total number of items in catalog
        """
        unique_recommended = set()
        for recs in all_recommendations:
            unique_recommended.update(recs)
        
        return len(unique_recommended) / catalog_size
    
    # ==================== ONLINE METRICS ====================
    
    def calculate_ctr(
        self,
        start_date: datetime,
        end_date: datetime,
        model_type: Optional[str] = None
    ) -> float:
        """
        CTR (Click-Through Rate): % recommendations được click
        """
        # Get impressions (views of recommendations)
        impressions = self.db.query(func.count(UserEvent.id)).filter(
            and_(
                UserEvent.event_type == 'recommendation_shown',
                UserEvent.timestamp >= start_date,
                UserEvent.timestamp <= end_date,
                UserEvent.event_metadata['model_type'].astext == model_type if model_type else True
            )
        ).scalar() or 0
        
        # Get clicks on recommendations
        clicks = self.db.query(func.count(RecommendationFeedback.id)).filter(
            and_(
                RecommendationFeedback.feedback_type == 'click',
                RecommendationFeedback.timestamp >= start_date,
                RecommendationFeedback.timestamp <= end_date,
                RecommendationFeedback.model_type == model_type if model_type else True
            )
        ).scalar() or 0
        
        if impressions == 0:
            return 0.0
        
        return clicks / impressions
    
    def calculate_watch_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        model_type: Optional[str] = None
    ) -> float:
        """
        Watch Rate: % recommendations được xem hoàn chỉnh
        """
        # Get total recommendations
        total_recs = self.db.query(func.count(RecommendationFeedback.id)).filter(
            and_(
                RecommendationFeedback.feedback_type == 'click',
                RecommendationFeedback.timestamp >= start_date,
                RecommendationFeedback.timestamp <= end_date,
                RecommendationFeedback.model_type == model_type if model_type else True
            )
        ).scalar() or 0
        
        # Get completed watches
        completed = self.db.query(func.count(RecommendationFeedback.id)).filter(
            and_(
                RecommendationFeedback.feedback_type == 'complete',
                RecommendationFeedback.timestamp >= start_date,
                RecommendationFeedback.timestamp <= end_date,
                RecommendationFeedback.model_type == model_type if model_type else True
            )
        ).scalar() or 0
        
        if total_recs == 0:
            return 0.0
        
        return completed / total_recs
    
    # ==================== FULL EVALUATION ====================
    
    def evaluate_model(
        self,
        model_type: str,
        model_version: str,
        test_users: Optional[List[str]] = None,
        k_values: List[int] = [5, 10, 20]
    ) -> Dict:
        """
        Đánh giá toàn diện một model
        
        Args:
            model_type: Loại model (collaborative, content, hybrid)
            model_version: Version của model
            test_users: List user IDs để test (None = all)
            k_values: List các giá trị K để evaluate
        
        Returns:
            Dict chứa tất cả metrics
        """
        from services.recommendation_service import AdvancedRecommendationService
        
        rec_service = AdvancedRecommendationService(self.db)
        
        # Get test users
        if test_users is None:
            test_users = self._get_active_users(min_interactions=5)
        
        # Initialize metrics
        metrics = {
            f'precision@{k}': [] for k in k_values
        }
        metrics.update({
            f'recall@{k}': [] for k in k_values
        })
        metrics.update({
            f'ndcg@{k}': [] for k in k_values
        })
        metrics['map'] = []
        metrics['mrr'] = []
        metrics['diversity'] = []
        
        all_recommendations = []
        
        # Evaluate each user
        for user_id in test_users:
            # Get ground truth (future interactions)
            ground_truth = self._get_ground_truth(user_id)
            if not ground_truth:
                continue
            
            # Get recommendations
            if model_type == 'collaborative':
                recs = rec_service.get_collaborative_recommendations(user_id, n=max(k_values))
            elif model_type == 'content':
                # Content-based needs a seed movie
                recent_movie = self._get_recent_movie(user_id)
                if recent_movie:
                    recs = rec_service.get_content_based_recommendations(recent_movie, n=max(k_values))
                else:
                    continue
            elif model_type == 'hybrid':
                recs = rec_service.get_hybrid_recommendations(user_id, n=max(k_values))
            else:
                recs = rec_service.get_personalized_recommendations(user_id, n=max(k_values))
            
            rec_ids = [r['movie_id'] for r in recs]
            all_recommendations.append(rec_ids)
            
            # Calculate metrics for different K values
            for k in k_values:
                metrics[f'precision@{k}'].append(
                    self.calculate_precision_at_k(rec_ids, ground_truth, k)
                )
                metrics[f'recall@{k}'].append(
                    self.calculate_recall_at_k(rec_ids, ground_truth, k)
                )
                
                # NDCG needs relevance scores
                relevance_scores = {movie_id: 1.0 for movie_id in ground_truth}
                metrics[f'ndcg@{k}'].append(
                    self.calculate_ndcg_at_k(rec_ids, relevance_scores, k)
                )
            
            # MAP and MRR
            metrics['map'].append(self.calculate_map(rec_ids, ground_truth))
            metrics['mrr'].append(self.calculate_mrr(rec_ids, ground_truth))
            metrics['diversity'].append(self.calculate_diversity(rec_ids))
        
        # Calculate averages
        results = {}
        for metric_name, values in metrics.items():
            if values:
                results[metric_name] = np.mean(values)
            else:
                results[metric_name] = 0.0
        
        # Coverage
        catalog_size = self.db.query(func.count(Movie.id)).scalar()
        results['coverage'] = self.calculate_coverage(all_recommendations, catalog_size)
        
        # Online metrics (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        results['ctr'] = self.calculate_ctr(start_date, end_date, model_type)
        results['watch_rate'] = self.calculate_watch_rate(start_date, end_date, model_type)
        
        # Save to database
        self._save_evaluation(model_type, model_version, results)
        
        return results
    
    def _get_active_users(self, min_interactions: int = 5) -> List[str]:
        """Get users with minimum number of interactions"""
        users = self.db.query(
            UserEvent.user_id,
            func.count(UserEvent.id).label('count')
        ).group_by(UserEvent.user_id).having(
            func.count(UserEvent.id) >= min_interactions
        ).limit(100).all()
        
        return [user[0] for user in users]
    
    def _get_ground_truth(self, user_id: str) -> List[str]:
        """
        Get ground truth for evaluation
        Use future interactions as ground truth
        """
        # Get recent high-rated movies as ground truth
        recent = self.db.query(Rating).filter(
            and_(
                Rating.user_id == user_id,
                Rating.rating >= 4.0
            )
        ).order_by(Rating.timestamp.desc()).limit(10).all()
        
        return [r.movie_id for r in recent]
    
    def _get_recent_movie(self, user_id: str) -> Optional[str]:
        """Get user's most recent movie interaction"""
        event = self.db.query(UserEvent).filter(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.movie_id.isnot(None)
            )
        ).order_by(UserEvent.timestamp.desc()).first()
        
        return event.movie_id if event else None
    
    def _save_evaluation(
        self,
        model_type: str,
        model_version: str,
        metrics: Dict
    ):
        """Save evaluation results to database"""
        performance = ModelPerformance(
            model_type=model_type,
            model_version=model_version,
            precision_at_5=metrics.get('precision@5', 0.0),
            precision_at_10=metrics.get('precision@10', 0.0),
            recall_at_5=metrics.get('recall@5', 0.0),
            recall_at_10=metrics.get('recall@10', 0.0),
            ndcg_at_10=metrics.get('ndcg@10', 0.0),
            map_score=metrics.get('map', 0.0),
            mrr=metrics.get('mrr', 0.0),
            ctr=metrics.get('ctr', 0.0),
            watch_rate=metrics.get('watch_rate', 0.0),
            diversity=metrics.get('diversity', 0.0),
            coverage=metrics.get('coverage', 0.0),
            evaluation_date=datetime.utcnow(),
            sample_size=len(metrics.get('precision@5', []))
        )
        
        self.db.add(performance)
        self.db.commit()
    
    def compare_models(
        self,
        model_types: List[str],
        days: int = 30
    ) -> Dict:
        """
        So sánh performance của nhiều models
        
        Args:
            model_types: List các model types cần compare
            days: Số ngày data để compare
        
        Returns:
            Dict chứa comparison results
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = {}
        for model_type in model_types:
            performances = self.db.query(ModelPerformance).filter(
                and_(
                    ModelPerformance.model_type == model_type,
                    ModelPerformance.evaluation_date >= start_date
                )
            ).order_by(ModelPerformance.evaluation_date.desc()).limit(10).all()
            
            if performances:
                # Average metrics
                results[model_type] = {
                    'precision@10': np.mean([p.precision_at_10 for p in performances]),
                    'recall@10': np.mean([p.recall_at_10 for p in performances]),
                    'ndcg@10': np.mean([p.ndcg_at_10 for p in performances]),
                    'ctr': np.mean([p.ctr for p in performances if p.ctr]),
                    'diversity': np.mean([p.diversity for p in performances if p.diversity]),
                    'evaluations_count': len(performances)
                }
        
        return results
