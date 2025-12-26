# 🚀 Quick Start Guide

Hướng dẫn nhanh để chạy FilmFlow và sử dụng các tính năng mới.

## ⚡ Cài Đặt Nhanh

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd phim
```

### 2. Cấu Hình Environment Variables

**Frontend:**
```bash
cd frontend
cp .env.example .env
# File .env đã được tạo với giá trị mặc định
```

**Backend:**
```bash
cd app
cp .env.example .env
# Chỉnh sửa file .env và điền API keys:
```

```env
TMDB_API_KEY=your_tmdb_api_key
YOUTUBE_API_KEY=your_youtube_api_key
DATABASE_URL=postgresql://phim_user:phim_password@db:5432/phim_db
CORS_ORIGINS=http://localhost:3000,http://localhost:80
RATE_LIMIT_PER_MINUTE=100
```

### 3. Chạy với Docker

```bash
# Từ thư mục root
docker-compose up --build
```

### 4. Truy Cập

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🛠️ Development Setup

### Frontend Development

```bash
cd frontend

# Cài dependencies
npm install

# Chạy dev server
npm start

# Lint code
npm run lint

# Fix lint errors
npm run lint:fix

# Format code
npm run format

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage --watchAll=false
```

### Backend Development

```bash
cd app

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate     # Windows

# Cài dependencies
pip install -r api/requirements.txt

# Cài dev dependencies
pip install pytest pytest-cov flake8 black

# Chạy backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Lint
flake8 .

# Format
black .

# Run tests
pytest

# Tests with coverage
pytest --cov=. --cov-report=html
```

---

## 🧪 Chạy Tests

### Tất Cả Tests

```bash
# Frontend tests
cd frontend && npm test -- --watchAll=false

# Backend tests
cd app && pytest

# Hoặc dùng Docker
docker-compose run frontend npm test -- --watchAll=false
docker-compose run backend pytest
```

### Specific Tests

```bash
# Test một file cụ thể
npm test Pagination.test.js
pytest tests/test_api.py

# Test với keyword
npm test -- --testNamePattern="pagination"
pytest -k "rate_limit"
```

---

## 🔧 Sử Dụng Các Component Mới

### 1. LazyImage Component

```javascript
import LazyImage from './components/LazyImage';

function MovieCard({ movie }) {
  return (
    <div className="movie-card">
      <LazyImage
        src={movie.poster_url}
        alt={movie.title}
        className="movie-poster"
        placeholder="data:image/svg+xml,..."
      />
    </div>
  );
}
```

**Features:**
- Tự động lazy load khi scroll vào viewport
- Placeholder trong lúc loading
- Fade-in animation khi load xong
- Fallback cho broken images

---

### 2. Pagination Component

```javascript
import Pagination from './components/Pagination';
import { useState } from 'react';

function MovieList() {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const movies = [...]; // Your movies array
  const totalItems = movies.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  
  // Get current page items
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentMovies = movies.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div>
      {/* Render movies */}
      {currentMovies.map(movie => (
        <MovieCard key={movie.id} movie={movie} />
      ))}
      
      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        itemsPerPage={itemsPerPage}
        totalItems={totalItems}
      />
    </div>
  );
}
```

**Features:**
- First, Previous, Next, Last buttons
- Page numbers với smart ellipsis
- Hiển thị info (showing X-Y of Z items)
- Responsive design
- Keyboard navigation

---

## 🔒 Security Features

### Rate Limiting

API tự động giới hạn requests:
- Mặc định: **100 requests/phút** mỗi IP
- HTTP 429 khi vượt giới hạn
- Tự động reset sau 1 phút

**Test rate limiting:**
```bash
# Gửi nhiều requests liên tục
for i in {1..110}; do 
  curl http://localhost:8000/movies?limit=1
done

# Request thứ 101 sẽ trả về 429
```

**Cấu hình:**
```env
# app/.env
RATE_LIMIT_PER_MINUTE=200  # Tăng lên 200 req/min
```

---

### CORS Protection

CORS chỉ cho phép origins trong whitelist:

```env
# app/.env
CORS_ORIGINS=http://localhost:3000,http://localhost:80,https://yourdomain.com
```

**Production:**
```env
CORS_ORIGINS=https://filmflow.com,https://www.filmflow.com
```

---

## 📊 CI/CD Pipeline

### GitHub Actions

Pipeline tự động chạy khi:
- Push lên `main` hoặc `develop`
- Tạo Pull Request

**Workflow bao gồm:**
1. ✅ Frontend: lint, test, build
2. ✅ Backend: lint, test với PostgreSQL
3. ✅ Docker: build images

**Xem kết quả:**
- Vào tab **Actions** trên GitHub
- Click vào commit/PR để xem chi tiết
- Download artifacts (coverage reports)

---

## 🐛 Debugging

### Frontend Debug

```javascript
// Enable React DevTools
// Chrome: Install React Developer Tools extension

// Console logging
console.log('Current page:', currentPage);
console.log('Movies:', movies);

// Error boundaries
class ErrorBoundary extends React.Component {
  componentDidCatch(error, info) {
    console.error('Error:', error, info);
  }
}
```

### Backend Debug

```python
# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"User: {user_id}, Movies: {len(movies)}")

# IPython debugger
import ipdb; ipdb.set_trace()

# Print requests
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"{request.method} {request.url}")
    response = await call_next(request)
    return response
```

---

## 📈 Performance Tips

### Frontend

1. **Lazy loading images**
   - Sử dụng `LazyImage` component
   - Thêm `loading="lazy"` attribute

2. **Code splitting**
   ```javascript
   const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
   ```

3. **Memoization**
   ```javascript
   const MemoizedMovieCard = React.memo(MovieCard);
   ```

### Backend

1. **Database indexing**
   ```sql
   CREATE INDEX idx_movie_title ON movies(title);
   CREATE INDEX idx_rating_user ON ratings(user_id);
   ```

2. **Query optimization**
   ```python
   # Sử dụng pagination
   movies = db.query(Movie).limit(20).offset(page * 20).all()
   ```

3. **Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_recommendations(user_id, n=20):
       # Expensive computation
       return recommendations
   ```

---

## 🆘 Common Issues

### "Module not found"
```bash
# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install

# Backend
pip install --upgrade -r api/requirements.txt
```

### "Port already in use"
```bash
# Tìm process sử dụng port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill process
kill -9 <PID>

# Hoặc dùng docker
docker-compose down
```

### "Database connection error"
```bash
# Kiểm tra PostgreSQL
docker-compose ps
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d db
```

### "Tests failing"
```bash
# Clear test cache
npm test -- --clearCache

# Update snapshots
npm test -- -u

# Verbose output
npm test -- --verbose
```

---

## 📚 Tài Liệu Bổ Sung

- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Chi tiết các cải thiện
- [README.md](README.md) - Tổng quan dự án
- [API Docs](http://localhost:8000/docs) - OpenAPI documentation

---

## 🎉 All Set!

Bạn đã sẵn sàng! Các tính năng mới:

✅ LazyImage - tối ưu hình ảnh  
✅ Pagination - phân trang  
✅ Rate Limiting - bảo vệ API  
✅ Unit Tests - đảm bảo chất lượng  
✅ CI/CD - tự động hóa  
✅ ESLint/Prettier - code quality  

**Enjoy coding! 🚀**
