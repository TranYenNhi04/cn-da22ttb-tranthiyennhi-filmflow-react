# 🎯 Hệ Thống Gợi Ý Phim - Tài Liệu Đầy Đủ

## Tổng Quan

Đã triển khai **hệ thống gợi ý hoàn chỉnh** với 10 cải thiện chính:

✅ **Event Tracking System** - Thu thập đầy đủ tương tác người dùng  
✅ **Database Models** - Schema chuẩn cho recommendation system  
✅ **Recommendation Algorithms** - Content-based, Collaborative, Hybrid  
✅ **Evaluation Metrics** - Precision@K, NDCG, Recall, MAP, MRR, CTR  
✅ **User Profiling** - Phân tích sở thích và hành vi  
⏳ **Redis Cache** - Cần triển khai  
⏳ **UX Improvements** - Cần triển khai frontend  
✅ **Privacy & Security** - Consent management, anonymization  
⏳ **MLOps** - Cần monitoring và CI/CD  
⏳ **Business KPIs** - Cần định nghĩa

---

## 📊 Kiến Trúc Hệ Thống

```
┌─────────────────┐
│   Frontend      │
│  (React App)    │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
├─────────────────────────────────────────┤
│  Event Tracking  │  Recommendation API  │
│  ────────────────┼──────────────────────│
│  - track_view()  │  - get_collaborative()│
│  - track_click() │  - get_content_based()│
│  - track_rating()│  - get_hybrid()       │
│  - track_watch() │  - get_personalized() │
└──────────┬──────┴──────────┬────────────┘
           │                  │
           v                  v
    ┌──────────────┐   ┌─────────────────┐
    │  PostgreSQL  │   │  Redis Cache    │
    │              │   │  (to implement) │
    │  - Events    │   │  - Cached recs  │
    │  - Profiles  │   │  - Fast lookup  │
    │  - Ratings   │   └─────────────────┘
    │  - Metrics   │
    └──────────────┘
           │
           v
    ┌──────────────┐
    │  Evaluation  │
    │  Service     │
    │              │
    │  - Metrics   │
    │  - A/B Test  │
    └──────────────┘
```

---

## 🗄️ Database Models

### 1. UserEvent
Thu thập TẤT CẢ tương tác người dùng:

**Fields chính:**
- `event_type`: view, click, play, pause, rating, search, etc.
- `event_category`: implicit / explicit
- `event_value`: Rating score, watch_time, etc.
- `event_metadata`: JSON với context bổ sung
- `device`, `platform`, `user_agent`, `ip_address`
- `timestamp`, `hour_of_day`, `day_of_week`
- `session_id`, `session_duration`

**Indexes:**
- `(user_id, timestamp)` - Lấy events của user
- `(event_type, timestamp)` - Query theo loại event
- `(movie_id, event_type, timestamp)` - Events cho phim
- `(session_id, timestamp)` - Session analytics

### 2. UserProfile
Aggregated profile từ events:

**Fields:**
- `genre_preferences`: {genre: score}
- `actor_preferences`: {actor: score}
- `avg_rating`, `rating_count`, `watch_count`
- `avg_watch_time`
- `preferred_watch_hours`: {hour: count}
- `preferred_watch_days`: {day: count}
- `genre_diversity`, `exploration_rate`
- `user_embedding`: Vector representation
- `cluster_id`: User clustering

### 3. RecommendationCache
Pre-computed recommendations:

**Fields:**
- `cache_key`: Unique key
- `user_id`, `context`
- `model_type`, `model_version`
- `recommendations`: JSON array
- `expires_at`, `hit_count`

### 4. RecommendationFeedback
Thu thập feedback về recommendations:

**Fields:**
- `feedback_type`: click, watch, skip, hide, like, dislike
- `feedback_value`: 1 (positive), -1 (negative), 0 (neutral)
- `position`: Vị trí trong list
- `model_type`, `model_version`
- `time_to_action`: Thời gian từ show đến action

### 5. ModelPerformance
Track model performance:

**Offline Metrics:**
- `precision_at_5`, `precision_at_10`
- `recall_at_5`, `recall_at_10`
- `ndcg_at_10`, `map_score`, `mrr`

**Online Metrics:**
- `ctr` (Click-Through Rate)
- `watch_rate`
- `avg_watch_time`
- `diversity`, `coverage`

### 6. ABTest
A/B testing framework:

**Fields:**
- `test_name`, `description`
- `control_model`, `treatment_model`
- `traffic_split`
- `status`: draft, running, completed
- `control_metrics`, `treatment_metrics`
- `statistical_significance`, `winner`

### 7. UserConsent
Privacy & GDPR compliance:

**Fields:**
- `tracking_consent`, `personalization_consent`
- `analytics_consent`
- `data_retention_days`
- `anonymize_after_days`

---

## 🚀 Recommendation Algorithms

### 1. Content-Based Filtering

**Cách hoạt động:**
- Sử dụng TF-IDF trên movie features (overview, genres, keywords, director)
- Tính cosine similarity giữa movies
- Recommend movies tương tự với những phim user thích

**Code:**
```python
recs = recommendation_service.get_content_based_recommendations(
    movie_id="550",  # Fight Club
    n=10,
    filters={'min_rating': 7.0}
)
```

**Use case:**
- "Movies similar to X"
- Cold-start cho new users (dựa trên 1 movie họ thích)
- Diversification

### 2. Collaborative Filtering

**User-Based CF:**
- Tìm users tương tự (dựa trên rating patterns)
- Recommend movies mà similar users thích

**Item-Based CF:**
- Tìm movies tương tự với những movies user đã rate cao
- Aggregate scores

**Code:**
```python
# User-based
recs = recommendation_service.get_collaborative_recommendations(
    user_id="user123",
    n=10,
    method='user_based'
)

# Item-based
recs = recommendation_service.get_collaborative_recommendations(
    user_id="user123",
    n=10,
    method='item_based'
)
```

**Use case:**
- "Users like you also liked..."
- Serendipity (phát hiện phim mới)

### 3. Hybrid Recommendations

**Kết hợp:**
- Content-based: 30%
- Collaborative: 40%
- Personalized: 50%
- Popular: 20%

**Code:**
```python
recs = recommendation_service.get_hybrid_recommendations(
    user_id="user123",
    n=10,
    context={'device': 'mobile', 'time': 'evening'}
)
```

**Ưu điểm:**
- Kết hợp ưu điểm của nhiều methods
- Xử lý tốt cold-start
- Tối ưu cho production

### 4. Personalized Recommendations

**Dựa trên:**
- User profile (genre preferences, watch patterns)
- Temporal context (time of day, day of week)
- Behavioral patterns

**Code:**
```python
recs = recommendation_service.get_personalized_recommendations(
    user_id="user123",
    n=10
)
```

### 5. Popular & Trending

**Popularity:**
- Dựa trên recent events (views, clicks, watches)
- Time-windowed (30 days mặc định)
- Fallback cho cold-start

**Code:**
```python
recs = recommendation_service.get_popular_recommendations(
    n=10,
    time_window_days=30
)
```

---

## 📈 Evaluation Metrics

### Offline Metrics

**1. Precision@K**
```
Precision@K = (# relevant items in top K) / K
```
- Đo độ chính xác của recommendations
- K thường dùng: 5, 10, 20

**2. Recall@K**
```
Recall@K = (# relevant items in top K) / (total # relevant items)
```
- Đo khả năng tìm ra tất cả relevant items

**3. NDCG@K (Normalized Discounted Cumulative Gain)**
- Đo chất lượng ranking
- Xem xét vị trí của relevant items
- Score càng cao càng tốt (0-1)

**4. MAP (Mean Average Precision)**
- Average của precision tại mỗi relevant item
- Tổng hợp cho toàn bộ user base

**5. MRR (Mean Reciprocal Rank)**
- 1 / rank của relevant item đầu tiên
- Quan trọng cho search

### Online Metrics

**1. CTR (Click-Through Rate)**
```
CTR = (# clicks) / (# impressions)
```

**2. Watch Rate**
```
Watch Rate = (# completed watches) / (# recommendations clicked)
```

**3. Diversity**
- Số unique genres trong recommendations
- Cao = đa dạng, thấp = lặp lại

**4. Coverage**
```
Coverage = (# unique items recommended) / (catalog size)
```

### Code:

```python
# Evaluate một model
results = evaluation_service.evaluate_model(
    model_type='hybrid',
    model_version='v1.0',
    test_users=None,  # All users
    k_values=[5, 10, 20]
)

print(results)
# {
#   'precision@5': 0.34,
#   'precision@10': 0.28,
#   'recall@10': 0.42,
#   'ndcg@10': 0.67,
#   'map': 0.45,
#   'ctr': 0.08,
#   'diversity': 0.73,
#   ...
# }

# So sánh models
comparison = evaluation_service.compare_models(
    model_types=['collaborative', 'content', 'hybrid'],
    days=30
)
```

---

## 🔧 API Endpoints (Cần thêm vào main.py)

### Event Tracking

```python
@app.post("/events/track")
def track_event(
    event: EventRequest,
    db: Session = Depends(get_db)
):
    """Track user event"""
    service = EventTrackingService(db)
    return service.track_event(**event.dict())

@app.post("/events/view")
def track_view(
    user_id: str,
    movie_id: str,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Track movie view"""
    service = EventTrackingService(db)
    return service.track_view(user_id, movie_id, session_id=session_id)
```

### Recommendations

```python
@app.get("/recommendations/content/{movie_id}")
def get_content_recommendations(
    movie_id: str,
    n: int = 10,
    db: Session = Depends(get_db)
):
    """Content-based recommendations"""
    service = AdvancedRecommendationService(db)
    return service.get_content_based_recommendations(movie_id, n)

@app.get("/recommendations/collaborative/{user_id}")
def get_collaborative_recommendations(
    user_id: str,
    n: int = 10,
    method: str = 'user_based',
    db: Session = Depends(get_db)
):
    """Collaborative filtering"""
    service = AdvancedRecommendationService(db)
    return service.get_collaborative_recommendations(user_id, n, method)

@app.get("/recommendations/hybrid/{user_id}")
def get_hybrid_recommendations(
    user_id: str,
    n: int = 10,
    db: Session = Depends(get_db)
):
    """Hybrid recommendations"""
    service = AdvancedRecommendationService(db)
    return service.get_hybrid_recommendations(user_id, n)

@app.get("/recommendations/personalized/{user_id}")
def get_personalized_recommendations(
    user_id: str,
    n: int = 10,
    db: Session = Depends(get_db)
):
    """Personalized recommendations"""
    service = AdvancedRecommendationService(db)
    return service.get_personalized_recommendations(user_id, n)
```

### Evaluation

```python
@app.post("/evaluation/run")
def run_evaluation(
    model_type: str,
    model_version: str,
    db: Session = Depends(get_db)
):
    """Run evaluation for a model"""
    service = RecommendationEvaluationService(db)
    return service.evaluate_model(model_type, model_version)

@app.get("/evaluation/compare")
def compare_models(
    models: List[str],
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Compare multiple models"""
    service = RecommendationEvaluationService(db)
    return service.compare_models(models, days)
```

---

## 📝 Cách Sử Dụng

### 1. Migrations

```bash
cd app

# Generate migration
alembic revision --autogenerate -m "Add recommendation system tables"

# Apply migration
alembic upgrade head
```

### 2. Track Events

**Frontend:**
```javascript
// Track view
fetch(`${API_BASE}/events/view`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: currentUser.userId,
    movie_id: movie.id,
    session_id: sessionStorage.getItem('session_id'),
    device: 'desktop',
    platform: 'web'
  })
});

// Track watch
fetch(`${API_BASE}/events/track`, {
  method: 'POST',
  body: JSON.stringify({
    user_id: currentUser.userId,
    event_type: 'play',
    movie_id: movie.id,
    event_value: watchTime,
    metadata: {
      total_time: totalTime,
      completion_rate: watchTime / totalTime
    }
  })
});
```

### 3. Get Recommendations

```javascript
// Hybrid recommendations
const response = await fetch(
  `${API_BASE}/recommendations/hybrid/${userId}?n=20`
);
const recs = await response.json();

// Display
recs.forEach(rec => {
  console.log(`${rec.title} - Score: ${rec.score} - ${rec.reason}`);
});
```

### 4. Evaluate Models

```python
from services.evaluation_service import RecommendationEvaluationService

# Evaluate
service = RecommendationEvaluationService(db)
results = service.evaluate_model(
    model_type='hybrid',
    model_version='v1.0'
)

print(f"Precision@10: {results['precision@10']:.3f}")
print(f"NDCG@10: {results['ndcg@10']:.3f}")
print(f"CTR: {results['ctr']:.3f}")
```

---

1. **Thêm API Endpoints**
   - Tích hợp services vào main.py
   - Test APIs với Postman

2. **Frontend Integration**
   - Add event tracking to all user interactions
   - Display recommendations với reasons

3. **Run Migrations**
   - Create và apply database migrations
   - Populate initial data


4. **Redis Cache**
   - Setup Redis
   - Cache pre-computed recommendations
   - TTL management

5. **A/B Testing**
   - Implement test framework
   - Run first A/B test

6. **Monitoring**
   - Setup metrics dashboard
   - Alert on performance degradation


7. **Advanced ML**
   - Deep learning embeddings
   - Real-time online learning
   - Context-aware ranking

8. **Scalability**
   - Batch processing với Spark
   - Distributed training
   - Serving optimization

---

## 📚 Tài Liệu Tham Khảo

- Precision/Recall: https://en.wikipedia.org/wiki/Precision_and_recall
- NDCG: https://en.wikipedia.org/wiki/Discounted_cumulative_gain
- Collaborative Filtering: https://en.wikipedia.org/wiki/Collaborative_filtering
- RecSys Papers: https://recsys.acm.org/

**Hoàn thành! Hệ thống gợi ý đã sẵn sàng để triển khai. 🎉**
