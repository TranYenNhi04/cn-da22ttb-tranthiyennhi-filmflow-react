"""
Event Tracking Service
Thu thập và xử lý tất cả user events cho recommendation system
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import hashlib

from data.models import (
    UserEvent, UserProfile, RecommendationFeedback,
    UserConsent, User
)


class EventTrackingService:
    """Service quản lý event tracking và user behavior"""
    
    # Event types definition
    IMPLICIT_EVENTS = ['view', 'click', 'scroll', 'hover', 'search']
    EXPLICIT_EVENTS = ['rating', 'add_watchlist', 'remove_watchlist', 'play', 'pause', 'complete']
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_event(
        self,
        user_id: str,
        event_type: str,
        movie_id: Optional[str] = None,
        event_value: Optional[float] = None,
        session_id: Optional[str] = None,
        device: Optional[str] = None,
        platform: Optional[str] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        page_url: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> UserEvent:
        """
        Track một event từ user
        
        Args:
            user_id: ID của user
            event_type: Loại event (view, click, rating, etc.)
            movie_id: ID phim (nếu có)
            event_value: Giá trị event (rating score, watch_time, etc.)
            session_id: Session ID
            device: Device type (mobile, desktop, tablet)
            platform: Platform (web, android, ios)
            metadata: Additional metadata
            ip_address: User IP
            user_agent: User agent string
            page_url: Current page URL
            referrer: Referrer URL
        """
        # Check consent
        if not self._check_consent(user_id):
            return None
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Determine event category
        event_category = 'explicit' if event_type in self.EXPLICIT_EVENTS else 'implicit'
        
        # Get timestamp info
        now = datetime.utcnow()
        
        # Create event
        event = UserEvent(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id or self._generate_session_id(user_id),
            movie_id=movie_id,
            event_type=event_type,
            event_category=event_category,
            event_value=event_value,
            event_metadata=metadata or {},
            device=device,
            platform=platform,
            user_agent=user_agent,
            ip_address=self._anonymize_ip(ip_address) if ip_address else None,
            timestamp=now,
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
            page_url=page_url,
            referrer=referrer,
            processed=False
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Async update user profile (trong production nên dùng queue)
        self._update_user_profile_async(user_id)
        
        return event
    
    def track_view(self, user_id: str, movie_id: str, **kwargs) -> UserEvent:
        """Track movie view event"""
        return self.track_event(
            user_id=user_id,
            event_type='view',
            movie_id=movie_id,
            **kwargs
        )
    
    def track_click(self, user_id: str, movie_id: str, **kwargs) -> UserEvent:
        """Track movie click event"""
        return self.track_event(
            user_id=user_id,
            event_type='click',
            movie_id=movie_id,
            **kwargs
        )
    
    def track_rating(self, user_id: str, movie_id: str, rating: float, **kwargs) -> UserEvent:
        """Track rating event"""
        return self.track_event(
            user_id=user_id,
            event_type='rating',
            movie_id=movie_id,
            event_value=rating,
            **kwargs
        )
    
    def track_watch(
        self,
        user_id: str,
        movie_id: str,
        watch_time: float,
        total_time: float,
        completed: bool = False,
        **kwargs
    ) -> UserEvent:
        """Track watch event với watch time"""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'watch_time': watch_time,
            'total_time': total_time,
            'completion_rate': watch_time / total_time if total_time > 0 else 0,
            'completed': completed
        })
        
        return self.track_event(
            user_id=user_id,
            event_type='complete' if completed else 'play',
            movie_id=movie_id,
            event_value=watch_time,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    def track_search(self, user_id: str, query: str, results_count: int = 0, **kwargs) -> UserEvent:
        """Track search query"""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'query': query,
            'results_count': results_count
        })
        
        return self.track_event(
            user_id=user_id,
            event_type='search',
            event_value=float(results_count),
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    def track_recommendation_feedback(
        self,
        user_id: str,
        movie_id: str,
        feedback_type: str,
        feedback_value: float,
        position: Optional[int] = None,
        model_type: Optional[str] = None,
        recommendation_id: Optional[str] = None
    ) -> RecommendationFeedback:
        """Track feedback về recommendation"""
        feedback = RecommendationFeedback(
            feedback_id=str(uuid.uuid4()),
            user_id=user_id,
            movie_id=movie_id,
            recommendation_id=recommendation_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            position=position,
            model_type=model_type,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(feedback)
        self.db.commit()
        
        return feedback
    
    def get_user_events(
        self,
        user_id: str,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[UserEvent]:
        """Lấy events của user"""
        query = self.db.query(UserEvent).filter(UserEvent.user_id == user_id)
        
        if event_types:
            query = query.filter(UserEvent.event_type.in_(event_types))
        
        if start_date:
            query = query.filter(UserEvent.timestamp >= start_date)
        
        if end_date:
            query = query.filter(UserEvent.timestamp <= end_date)
        
        return query.order_by(UserEvent.timestamp.desc()).limit(limit).all()
    
    def get_movie_events(
        self,
        movie_id: str,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[UserEvent]:
        """Lấy events cho một movie"""
        query = self.db.query(UserEvent).filter(UserEvent.movie_id == movie_id)
        
        if event_types:
            query = query.filter(UserEvent.event_type.in_(event_types))
        
        return query.order_by(UserEvent.timestamp.desc()).limit(limit).all()
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Lấy user profile"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def update_user_profile(self, user_id: str) -> UserProfile:
        """
        Cập nhật user profile từ events
        Tính toán preferences, patterns, và features
        """
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id, first_seen=datetime.utcnow())
            self.db.add(profile)
        
        # Get recent events (last 90 days)
        start_date = datetime.utcnow() - timedelta(days=90)
        events = self.get_user_events(user_id, start_date=start_date, limit=10000)
        
        if not events:
            self.db.commit()
            return profile
        
        # Calculate metrics
        rating_events = [e for e in events if e.event_type == 'rating' and e.event_value]
        watch_events = [e for e in events if e.event_type in ['play', 'complete']]
        
        profile.rating_count = len(rating_events)
        profile.watch_count = len(watch_events)
        
        if rating_events:
            profile.avg_rating = sum(e.event_value for e in rating_events) / len(rating_events)
        
        if watch_events:
            watch_times = [e.event_value for e in watch_events if e.event_value]
            profile.avg_watch_time = sum(watch_times) / len(watch_times) if watch_times else 0
        
        # Temporal patterns
        hour_counts = {}
        day_counts = {}
        for event in events:
            hour_counts[event.hour_of_day] = hour_counts.get(event.hour_of_day, 0) + 1
            day_counts[event.day_of_week] = day_counts.get(event.day_of_week, 0) + 1
        
        profile.preferred_watch_hours = hour_counts
        profile.preferred_watch_days = day_counts
        
        # Activity metrics
        unique_days = len(set(e.timestamp.date() for e in events))
        profile.active_days = unique_days
        profile.last_active = max(e.timestamp for e in events)
        
        profile.updated_at = datetime.utcnow()
        profile.version += 1
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def _check_consent(self, user_id: str) -> bool:
        """Kiểm tra user consent cho tracking"""
        consent = self.db.query(UserConsent).filter(UserConsent.user_id == user_id).first()
        
        # Nếu chưa có consent record, tạo mới với default = True (opt-out model)
        if not consent:
            consent = UserConsent(
                user_id=user_id,
                tracking_consent=True,
                personalization_consent=True,
                analytics_consent=True,
                consent_given_at=datetime.utcnow()
            )
            self.db.add(consent)
            self.db.commit()
            return True
        
        return consent.tracking_consent
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate session ID dựa trên user và timestamp"""
        # Session có thể kéo dài 30 phút
        timestamp = datetime.utcnow().replace(minute=datetime.utcnow().minute // 30 * 30, second=0, microsecond=0)
        session_string = f"{user_id}_{timestamp.isoformat()}"
        return hashlib.md5(session_string.encode()).hexdigest()[:16]
    
    def _anonymize_ip(self, ip_address: str) -> str:
        """Anonymize IP address (remove last octet)"""
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        return ip_address
    
    def _update_user_profile_async(self, user_id: str):
        """
        Update user profile asynchronously
        Trong production nên dùng Celery/RQ
        """
        try:
            self.update_user_profile(user_id)
        except Exception as e:
            print(f"Error updating user profile: {e}")
    
    def deduplicate_events(self, window_seconds: int = 5) -> int:
        """
        Xóa duplicate events trong một time window
        Returns: số events đã xóa
        """
        # Tìm duplicate events (same user, movie, event_type trong window)
        subquery = self.db.query(
            UserEvent.user_id,
            UserEvent.movie_id,
            UserEvent.event_type,
            func.min(UserEvent.timestamp).label('min_timestamp')
        ).group_by(
            UserEvent.user_id,
            UserEvent.movie_id,
            UserEvent.event_type
        ).subquery()
        
        # Delete duplicates
        deleted = self.db.query(UserEvent).filter(
            and_(
                UserEvent.user_id == subquery.c.user_id,
                UserEvent.movie_id == subquery.c.movie_id,
                UserEvent.event_type == subquery.c.event_type,
                UserEvent.timestamp > subquery.c.min_timestamp,
                UserEvent.timestamp <= subquery.c.min_timestamp + timedelta(seconds=window_seconds)
            )
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return deleted
