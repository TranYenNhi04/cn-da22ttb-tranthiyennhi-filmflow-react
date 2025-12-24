# 🎬 FilmFlow - Hệ Thống Gợi Ý Phim Thông Minh

<div align="center">

![FilmFlow Banner](https://img.shields.io/badge/FilmFlow-Movie%20Recommendation-ffc107?style=for-the-badge)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Nền tảng xem phim với AI gợi ý cá nhân hóa, giao diện đẹp mắt và trải nghiệm người dùng tuyệt vời**

[Tính Năng](#-tính-năng-nổi-bật) • [Cài Đặt](#-cài-đặt) • [Sử Dụng](#-hướng-dẫn-sử-dụng) • [API](#-api-documentation) • [Công Nghệ](#-công-nghệ-sử-dụng)

</div>

---

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng Nổi Bật](#-tính-năng-nổi-bật)
- [Demo & Screenshots](#-demo--screenshots)
- [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Hướng Dẫn Sử Dụng](#-hướng-dẫn-sử-dụng)
- [API Documentation](#-api-documentation)
- [Thuật Toán Gợi Ý](#-thuật-toán-gợi-ý)
- [Đóng Góp](#-đóng-góp)
- [License](#-license)

---

## 🎯 Giới Thiệu

**FilmFlow** là một hệ thống gợi ý phim thông minh được xây dựng với các thuật toán Machine Learning tiên tiến. Dự án kết hợp giữa **Content-Based Filtering**, **Collaborative Filtering** và **Hybrid Recommendation** để mang đến trải nghiệm xem phim được cá nhân hóa tối đa cho từng người dùng.

### 🌟 Điểm Nổi Bật

- 🤖 **AI-Powered Recommendations** - Gợi ý thông minh dựa trên sở thích cá nhân
- 🎨 **Beautiful UI/UX** - Giao diện hiện đại, mượt mà với animations đẹp mắt
- ⚡ **Blazing Fast** - Tối ưu hiệu năng với caching và lazy loading
- 🔍 **Smart Search** - Tìm kiếm phim nhanh chóng với autocomplete
- 📱 **Responsive Design** - Hoạt động tuyệt vời trên mọi thiết bị
- 🎬 **Rich Media** - Tích hợp TMDB API và YouTube trailers
- 💾 **Data Persistence** - Lưu trữ lịch sử xem và đánh giá người dùng
- 🐳 **Docker Ready** - Dễ dàng deploy với Docker Compose

---

## ✨ Tính Năng Nổi Bật

### 🎥 Xem Phim & Khám Phá

- **Hero Section động** với animated movie posters grid
- **Trending Movies** - Phim đang hot nhất
- **New Releases** - Phim mới cập nhật
- **Top Rated** - Phim được đánh giá cao
- **Collections** - Bộ sưu tập phim theo chủ đề
- **Continue Watching** - Tiếp tục xem từ lịch sử

### 🔍 Tìm Kiếm & Lọc

- **Real-time Search** với autocomplete
- **Advanced Filters**:
  - Lọc theo thể loại (Action, Comedy, Drama, Horror, Romance...)
  - Lọc theo năm phát hành
  - Sắp xếp theo đánh giá, mới nhất, tên A-Z
- **Smart Caching** cho tốc độ tải nhanh

### 🤖 Hệ Thống Gợi Ý Thông Minh

1. **Content-Based Filtering**
   - Gợi ý dựa trên nội dung phim (thể loại, mô tả, từ khóa)
   - TF-IDF Vectorization cho text features
   - Cosine Similarity để tính độ tương đồng

2. **Collaborative Filtering**
   - Matrix Factorization với SVD (Singular Value Decomposition)
   - Dự đoán rating dựa trên hành vi người dùng tương tự
   - Cold-start handling cho người dùng mới

3. **Hybrid Recommendation**
   - Kết hợp cả Content-Based và Collaborative
   - Weighted scoring để cân bằng các phương pháp
   - Context-aware recommendations

4. **Personalized Recommendations**
   - Học từ lịch sử xem của người dùng
   - Tích hợp thời gian xem (buổi sáng/tối)
   - Diversity trong gợi ý để tránh filter bubble

### 👤 Quản Lý Người Dùng

- **Authentication** - Đăng nhập/Đăng ký
- **Profile Management** - Quản lý thông tin cá nhân
- **Watchlist** - Danh sách phim yêu thích
- **Watch History** - Lịch sử xem phim
- **Ratings & Reviews** - Đánh giá và nhận xét phim

### 🎬 Thông Tin Phim Chi Tiết

- **Movie Details** - Thông tin đầy đủ về phim
- **Cast & Crew** - Diễn viên, đạo diễn
- **YouTube Trailers** - Xem trailer trực tiếp
- **Similar Movies** - Phim tương tự
- **User Reviews** - Đánh giá từ cộng đồng
- **Quick Rating** - Đánh giá nhanh với stars

---

## 📸 Demo & Screenshots

### Hero Section với Animated Posters
```
[Animated movie poster grid với 3D effects và particles]
```

### Movie Browsing với Smart Filters
```
[Movie grid với filters và smooth animations]
```

### Movie Details & Recommendations
```
[Chi tiết phim với trailer, cast, và similar movies]
```

---

## 🛠 Công Nghệ Sử Dụng

### Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core Language | 3.11+ |
| **FastAPI** | REST API Framework | 0.100+ |
| **Pandas** | Data Processing | Latest |
| **NumPy** | Numerical Computing | Latest |
| **Scikit-learn** | ML Algorithms | Latest |
| **Uvicorn** | ASGI Server | Latest |

**ML Libraries:**
- `scikit-learn` - TF-IDF, Cosine Similarity, SVD
- `pandas` - Data manipulation
- `numpy` - Matrix operations

**APIs:**
- `TMDB API` - Movie metadata và posters
- `YouTube API` - Movie trailers

### Frontend

| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI Framework | 18+ |
| **CSS3** | Styling | - |
| **JavaScript ES6+** | Logic | - |

**Features:**
- Modern React Hooks (useState, useEffect, useRef)
- Responsive Design với CSS Grid/Flexbox
- CSS Animations cho smooth transitions
- LocalStorage để cache và persistence
- Lazy Loading cho images
- Debounced Search
- Skeleton Loading states

### DevOps & Tools

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Git** | Version control |
| **Nginx** | Frontend serving |

---

## 🏗 Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────┐
│                   User Browser                      │
│              (React Frontend - Port 3000)           │
└────────────────────┬────────────────────────────────┘
                     │
                     │ HTTP/REST API
                     │
┌────────────────────▼────────────────────────────────┐
│              FastAPI Backend (Port 8000)            │
│  ┌──────────────────────────────────────────────┐  │
│  │         API Layer (main.py)                  │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼──────────┬────────────────────┐  │
│  │  Movie Controller       │  Recommendation    │  │
│  │  - Search               │  Controller        │  │
│  │  - Filter               │  - Content-Based   │  │
│  │  - Details              │  - Collaborative   │  │
│  │  - Reviews              │  - Hybrid          │  │
│  └─────────────────────────┴────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼───────────────────────────────┐  │
│  │           ML Models Layer                    │  │
│  │  - TF-IDF Vectorizer                         │  │
│  │  - Cosine Similarity                         │  │
│  │  - SVD Matrix Factorization                  │  │
│  │  - Hybrid Scoring                            │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼───────────────────────────────┐  │
│  │         Data Layer (CSV/In-Memory)           │  │
│  │  - movies_processed.csv                      │  │
│  │  - ratings_processed.csv                     │  │
│  │  - reviews.csv                               │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼───────────────────────────────┐  │
│  │       External APIs (Utils)                  │  │
│  │  - TMDB API (Posters/Metadata)               │  │
│  │  - YouTube API (Trailers)                    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống

- **Docker** và **Docker Compose** (Khuyến nghị)
- Hoặc:
  - Python 3.11+
  - Node.js 18+
  - npm hoặc yarn

### Cách 1: Sử Dụng Docker (Khuyến Nghị) 🐳

1. **Clone repository**
```bash
git clone https://github.com/TranYenNhi04/cn-da22ttb-tranthiyennhi-filmflow-react.git
cd cn-da22ttb-tranthiyennhi-filmflow-react
```

2. **Tạo file `.env`** (optional)
```bash
# .env
YOUTUBE_API_KEY=your_youtube_api_key_here
TMDB_API_KEY=your_tmdb_api_key_here
```

3. **Chạy Docker Compose**
```bash
docker-compose up --build
```

4. **Truy cập ứng dụng**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Cách 2: Cài Đặt Thủ Công

#### Backend Setup

```bash
# Di chuyển vào thư mục backend
cd app

# Tạo virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r api/requirements.txt

# Chạy backend server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies
npm install

# Tạo file .env (nếu cần)
echo "REACT_APP_API_BASE=http://localhost:8000" > .env

# Chạy development server
npm start

# Hoặc build production
npm run build
```

---

## 📖 Hướng Dẫn Sử Dụng

### Đăng Nhập/Đăng Ký

1. Mở ứng dụng tại http://localhost:3000
2. Nhập tên và email để đăng nhập
3. Hệ thống tự động tạo user ID duy nhất

### Khám Phá Phim

1. **Browse Movies**: Cuộn trang chủ để xem các mục:
   - 🔥 Đang Hot Nhất
   - 🆕 Phim Mới Cập Nhật
   - ⭐ Đánh Giá Cao Nhất
   
2. **Search**: Nhập tên phim vào thanh tìm kiếm
   - Autocomplete sẽ gợi ý phim phù hợp
   
3. **Filter**: Sử dụng bộ lọc:
   - Chọn thể loại phim
   - Chọn năm phát hành
   - Sắp xếp theo tiêu chí

### Xem Chi Tiết Phim

1. Click vào poster phim
2. Xem thông tin chi tiết:
   - Synopsis, Cast, Director
   - Đánh giá và reviews
   - Trailer YouTube (nếu có)
3. Đánh giá phim với star rating
4. Xem phim tương tự được gợi ý

### Nhận Gợi Ý Cá Nhân Hóa

1. Xem và đánh giá nhiều phim
2. Hệ thống AI sẽ học sở thích của bạn
3. Nhận gợi ý phim phù hợp trong:
   - Section "Gợi Ý Dành Riêng Cho Bạn"
   - Trang Recommendations

### Quản Lý Hồ Sơ

1. Click "Hồ Sơ" ở sidebar
2. Xem thống kê:
   - Tổng số phim đã xem
   - Tổng số đánh giá
   - Watchlist
3. Quản lý watchlist và xóa lịch sử

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Movies

```http
GET /movies
# Lấy danh sách phim với pagination
Parameters: skip, limit

GET /movies/{movie_id}
# Lấy chi tiết một phim

GET /movies/autocomplete?q={query}&n={limit}
# Tìm kiếm phim với autocomplete

GET /movies/trending?limit={limit}
# Lấy phim trending

GET /movies/top-rated?limit={limit}
# Lấy phim đánh giá cao

GET /movies/new-releases?limit={limit}
# Lấy phim mới phát hành

GET /movies/search?q={query}
# Tìm kiếm phim
```

#### Recommendations

```http
GET /recommendations?rec_type={type}&n={count}&user_id={user_id}
# Lấy gợi ý phim
# rec_type: collaborative | content-based | hybrid | personalized
# n: số lượng phim gợi ý
# user_id: ID người dùng (optional)

GET /recommendations/similar/{movie_id}?n={count}
# Lấy phim tương tự
```

#### Reviews & Ratings

```http
GET /reviews/{movie_id}
# Lấy reviews của phim

POST /reviews/{movie_id}
# Thêm review mới
Body: {
  "rating": 5,
  "review_text": "Great movie!",
  "username": "user123"
}

GET /reviews/{movie_id}/stats
# Lấy thống kê reviews

GET /reviews/{movie_id}/count
# Đếm số reviews
```

#### Users

```http
POST /users
# Tạo user mới
Body: {
  "userId": "user_123",
  "metadata": "{\"name\":\"John\",\"email\":\"john@email.com\"}"
}

GET /users/{user_id}
# Lấy thông tin user

POST /users/{user_id}/watch-history
# Lưu lịch sử xem
Body: {
  "movieId": "123",
  "timestamp": 1234567890
}

POST /users/{user_id}/watchlist
# Thêm vào watchlist
Body: {
  "movieId": "123"
}
```

#### Collections

```http
GET /collections/best_2024?limit={limit}
# Lấy phim hay nhất 2024
```

---

## 🧠 Thuật Toán Gợi Ý

### 1. Content-Based Filtering

**Ý tưởng**: Gợi ý phim dựa trên nội dung tương tự với phim người dùng đã xem

**Cách hoạt động**:
```python
# 1. Tạo feature vector từ metadata
features = movie['genres'] + ' ' + movie['overview'] + ' ' + movie['keywords']

# 2. TF-IDF Vectorization
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(features)

# 3. Tính cosine similarity
similarity_scores = cosine_similarity(tfidf_matrix[movie_idx], tfidf_matrix)

# 4. Lấy top N phim tương tự
similar_movies = similarity_scores.argsort()[-n:][::-1]
```

**Ưu điểm**:
- Không cần data từ users khác
- Hoạt động tốt với người dùng mới (cold-start)
- Giải thích được tại sao gợi ý

**Nhược điểm**:
- Over-specialization (chỉ gợi ý giống nhau)
- Phụ thuộc vào chất lượng metadata

### 2. Collaborative Filtering

**Ý tưởng**: Gợi ý dựa trên hành vi của người dùng tương tự

**Cách hoạt động**:
```python
# 1. Tạo user-item rating matrix
ratings_matrix = pd.pivot_table(
    ratings_df, 
    values='rating', 
    index='userId', 
    columns='movieId'
)

# 2. SVD Matrix Factorization
svd = TruncatedSVD(n_components=50)
matrix_factorized = svd.fit_transform(ratings_matrix)

# 3. Dự đoán rating cho các phim chưa xem
predicted_ratings = np.dot(matrix_factorized, svd.components_)

# 4. Lấy top N phim có rating dự đoán cao nhất
recommended_movies = predicted_ratings.argsort()[-n:][::-1]
```

**Ưu điểm**:
- Phát hiện patterns phức tạp
- Gợi ý đa dạng (serendipity)
- Không cần feature engineering

**Nhược điểm**:
- Cold-start problem (user/item mới)
- Data sparsity
- Scalability issues

### 3. Hybrid Approach

**Ý tưởng**: Kết hợp cả Content-Based và Collaborative

**Cách hoạt động**:
```python
# 1. Lấy gợi ý từ cả 2 phương pháp
content_scores = get_content_based_scores(user_id)
collab_scores = get_collaborative_scores(user_id)

# 2. Weighted combination
alpha = 0.6  # weight cho collaborative
beta = 0.4   # weight cho content-based

hybrid_scores = alpha * collab_scores + beta * content_scores

# 3. Lấy intersection và diverse set
recommendations = get_diverse_recommendations(hybrid_scores, n)
```

**Ưu điểm**:
- Kết hợp ưu điểm của cả 2 phương pháp
- Giảm over-specialization
- Handle cold-start tốt hơn

### 4. Personalized Recommendations

**Ý tưởng**: Tích hợp context và user behavior để cá nhân hóa sâu hơn

**Features được sử dụng**:
- Lịch sử xem phim
- Thời gian xem (sáng/chiều/tối)
- Thể loại yêu thích
- Rating patterns
- Recent interactions

**Context-aware factors**:
```python
# Time-based adjustments
if current_time == 'evening':
    boost_genres(['thriller', 'horror', 'drama'])
elif current_time == 'morning':
    boost_genres(['comedy', 'family', 'animation'])

# Diversity injection
recommendations = inject_diversity(
    recommendations,
    diversity_factor=0.2
)
```

---

## 🎨 UI/UX Highlights

### Design Principles

1. **Visual Hierarchy** - Thông tin quan trọng nổi bật
2. **Consistency** - Design language thống nhất
3. **Feedback** - Loading states, animations
4. **Accessibility** - Dễ sử dụng cho mọi người
5. **Performance** - Fast loading, smooth animations

### Key Features

- **Animated Hero Section**: 3D poster grid với particles effects
- **Smooth Transitions**: CSS animations và transforms
- **Skeleton Loading**: Placeholder trong lúc load data
- **Hover Effects**: Interactive feedback
- **Gradient Text**: Eye-catching typography
- **Glassmorphism**: Modern UI trends
- **Responsive Grid**: Adaptive layouts

---

## 🤝 Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp! 

### Cách Đóng Góp

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

### Development Guidelines

- Viết code clean và có comment
- Follow PEP 8 cho Python
- Follow ESLint rules cho JavaScript
- Viết unit tests cho features mới
- Update documentation

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👥 Team

- **Developer**: Trần Thị Yến Nhi
- **Student ID**: DA22TTB
- **GitHub**: [@TranYenNhi04](https://github.com/TranYenNhi04)
- **Project**: Đồ án Chuyên Ngành - FilmFlow Movie Recommendation System

---

## 🙏 Acknowledgments

- [The Movie Database (TMDB)](https://www.themoviedb.org/) - Movie data và APIs
- [YouTube Data API](https://developers.google.com/youtube/v3) - Trailer videos
- [MovieLens](https://grouplens.org/datasets/movielens/) - Ratings dataset
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://reactjs.org/) - Frontend library
- Khoa Công Nghệ Thông Tin - Trường Đại Học Trà Vinh

---

## 📞 Contact & Support

Có câu hỏi hoặc cần hỗ trợ?

- 🐛 Issues: [GitHub Issues](https://github.com/TranYenNhi04/cn-da22ttb-tranthiyennhi-filmflow-react/issues)
- 📧 Email: tranthiyennhi.tvu@gmail.com
- 💻 GitHub: [@TranYenNhi04](https://github.com/TranYenNhi04)

---

<div align="center">

**Made with ❤️ and ☕**

⭐ Star us on GitHub — it helps!

[⬆ Back to Top](#-filmflow---hệ-thống-gợi-ý-phim-thông-minh)

</div>