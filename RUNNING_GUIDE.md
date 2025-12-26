# 🎬 Hướng Dẫn Chạy Dự Án Movie Recommendation với Cá Nhân Hóa

## ✅ Các Lỗi Đã Fix

1. **Syntax Errors**: Fixed IndentationError và unmatched ')' trong `app/api/main.py`
2. **Import Errors**: Fixed tất cả imports để sử dụng `app.` prefix
3. **Database Setup**: PostgreSQL đã chạy với 4,741 movies và 13,668 ratings
4. **Dependencies**: Đã cài đặt đầy đủ requirements (FastAPI, uvicorn, pandas, etc.)

## 🚀 Cách Chạy Backend

### Option 1: Chạy trực tiếp với Python
```bash
# Kích hoạt virtual environment
.\.venv\Scripts\Activate.ps1

# Chạy backend server
python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Option 2: Chạy với Docker Compose (Recommended)
```bash
# Chạy tất cả services (PostgreSQL + Backend + Frontend)
docker-compose up -d

# Xem logs
docker-compose logs -f backend

# Dừng services
docker-compose down
```

## 🎯 Tính Năng Cá Nhân Hóa

### 1. **Personalized Recommendations**
Hệ thống phân tích hành vi người dùng để đưa ra gợi ý phù hợp:

- ✅ **Lịch sử xem phim** (Watch History)
- ✅ **Thể loại yêu thích** (Favorite Genres)
- ✅ **Thời gian xem** (Viewing Patterns)
- ✅ **Xu hướng xem gần đây** (Recent Trends)
- ✅ **Ratings và phản hồi** (User Ratings)
- ✅ **Thập kỷ ưa thích** (Preferred Decade)

### 2. **Các Loại Gợi Ý**

#### a) **Collaborative Filtering**
Gợi ý dựa trên người dùng tương tự
```bash
GET /recommendations?rec_type=collaborative&user_id=1&n=10
```

#### b) **Content-Based Filtering**
Gợi ý phim tương tự dựa trên nội dung
```bash
GET /recommendations?rec_type=content&movie_id=123&n=10
```

#### c) **Hybrid Model**
Kết hợp Collaborative và Content-Based
```bash
GET /recommendations?rec_type=hybrid&user_id=1&movie_id=123&n=10
```

#### d) **Personalized Recommendations** ⭐ (Tốt Nhất)
Cá nhân hóa dựa trên toàn bộ hành vi người dùng
```bash
GET /recommendations?rec_type=personalized&user_id=1&n=10
```

### 3. **API Endpoints Quan Trọng**

```bash
# Health check
GET /health

# Tìm kiếm phim
GET /movies/search?q=avatar&limit=20

# Lấy thông tin phim
GET /movies/{movie_id}

# Trending movies
GET /movies/trending?limit=20

# New releases
GET /movies/new-releases?limit=20

# Thêm phim vào watchlist
POST /user/{user_id}/watchlist/toggle
{
  "movie_id": 123
}

# Lấy watchlist
GET /user/{user_id}/watchlist

# Thêm rating
POST /movies/{movie_id}/rate
{
  "rating": 4.5,
  "user_id": "1"
}

# Login (mock authentication)
POST /auth/login
{
  "email": "user@example.com",
  "password": "anything"
}
```

## 🧪 Test Cá Nhân Hóa

Chạy script test để verify personalization:

```bash
# Install requests if needed
pip install requests

# Run test
python test_personalization.py
```

Script sẽ:
- ✅ Kiểm tra server health
- ✅ Lấy recommendations cho nhiều users khác nhau
- ✅ So sánh recommendations giữa các users
- ✅ Phân tích genre preferences
- ✅ Test các loại recommendation khác nhau

## 📊 Cách Hoạt Động của Personalization

### PersonalizedRecommendationModel
Located at: `app/models/personalized_model.py`

**Phân tích hành vi người dùng:**
```python
behavior = {
    'favorite_genres': [],      # Top 5 thể loại yêu thích
    'recent_genres': [],        # Thể loại xem gần đây (7 ngày)
    'watch_times': [],          # Giờ trong ngày thường xem
    'avg_rating': 0,            # Rating trung bình
    'total_watched': 0,         # Tổng số phim đã xem
    'preferred_decade': None,   # Thập kỷ ưa thích
    'genre_weights': {}         # Trọng số cho từng thể loại
}
```

**Scoring Algorithm:**
1. **Genre Matching (50%)**: Khớp với thể loại yêu thích
2. **Recent Trends (15%)**: Xu hướng xem gần đây
3. **Rating Match (20%)**: Phim có rating phù hợp
4. **Decade Preference (10%)**: Thập kỷ ưa thích
5. **Time Context (5%)**: Ngữ cảnh thời gian

## 🎓 Ví Dụ Sử Dụng

### Test với curl
```bash
# Lấy recommendations cho User 1
curl "http://127.0.0.1:8000/recommendations?rec_type=personalized&user_id=1&n=5"

# Lấy recommendations cho User 2
curl "http://127.0.0.1:8000/recommendations?rec_type=personalized&user_id=2&n=5"

# So sánh kết quả - mỗi user nên nhận được recommendations khác nhau!
```

### Test với Python
```python
import requests

# Get personalized recommendations
response = requests.get(
    "http://127.0.0.1:8000/recommendations",
    params={
        "rec_type": "personalized",
        "user_id": "1",
        "n": 10
    }
)

recommendations = response.json()
print(f"Got {len(recommendations['results'])} movies")
for movie in recommendations['results']:
    print(f"- {movie['title']} ({movie['year']}) - {movie['genres']}")
```

## 📁 Cấu Trúc Database

PostgreSQL database với các bảng:
- `movies` - Thông tin phim (4,741 movies)
- `users` - Người dùng
- `ratings` - Đánh giá phim (13,668 ratings)
- `reviews` - Review chi tiết
- `watch_history` - Lịch sử xem phim
- `watchlist` - Danh sách muốn xem

## 🔧 Configuration

File `.env` trong `app/` folder:
```env
# Database
DATABASE_URL=postgresql://filmflow_user:filmflow_pass123@localhost:5432/filmflow

# API Keys (optional)
TMDB_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:80

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

## 💡 Tips

1. **Caching**: Recommendations được cache 5 phút để tăng performance
2. **Fallback**: Nếu không có đủ data, hệ thống fallback về collaborative filtering
3. **Popular Movies**: Dùng để fill gaps khi không có recommendations
4. **Parallel Processing**: Poster enrichment chạy parallel để tăng tốc

## 🐛 Troubleshooting

### Server không start
```bash
# Check PostgreSQL
docker ps | grep postgres

# Start PostgreSQL nếu chưa chạy
docker-compose up -d postgres

# Check logs
docker-compose logs backend
```

### Import errors
- Đảm bảo đang ở thư mục `D:/cn/phim`
- Virtual environment đã được activate
- Dependencies đã được cài: `pip install -r app/api/requirements.txt`

### No recommendations
- Check database có data: `python -c "from app.data.db_postgresql import *; ..."`
- User ID phải tồn tại trong database
- Thử với collaborative filtering trước

## 📚 Tài Liệu Thêm

- [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md) - Chi tiết về hệ thống gợi ý
- [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md) - Hướng dẫn migrate database
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## ✅ Checklist Triển Khai

- [x] Fix syntax errors trong main.py
- [x] Fix import paths (app. prefix)
- [x] PostgreSQL running và có data
- [x] Backend server chạy thành công
- [x] Personalized recommendations hoạt động
- [x] Test script để verify personalization
- [x] Documentation đầy đủ

## 🎉 Kết Luận

Dự án đã được fix và chạy thành công với:
- ✅ Backend API hoạt động tốt
- ✅ PostgreSQL database đầy đủ data
- ✅ 4 loại recommendation models
- ✅ Personalization dựa trên user behavior
- ✅ Caching và optimization
- ✅ Full API documentation

**Backend đang chạy tại: http://127.0.0.1:8000**
**API Docs: http://127.0.0.1:8000/docs**
