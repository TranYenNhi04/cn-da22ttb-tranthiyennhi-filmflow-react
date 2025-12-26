# 🎬 Hướng Dẫn Fix Poster Hiển Thị Đúng

## Vấn Đề

Các poster phim đang hiển thị ảnh placeholder ngẫu nhiên thay vì poster thật của phim.

## Nguyên Nhân

Hệ thống cần TMDB API key để lấy poster phim từ The Movie Database (TMDB). Hiện tại `TMDB_API_KEY` trong file `.env` đang để trống.

## Giải Pháp

### Option 1: Lấy TMDB API Key (KHUYẾN NGHỊ - Miễn Phí)

1. **Đăng ký tài khoản TMDB**
   - Truy cập: https://www.themoviedb.org/signup
   - Điền thông tin và xác nhận email

2. **Tạo API Key**
   - Đăng nhập vào https://www.themoviedb.org
   - Vào **Settings** → **API**
   - Click **Create` → **Developer**
   - Điền thông tin:
     - Application Name: `Movie Recommendation`
     - Application URL: `http://localhost:3000`
     - Application Summary: `Personal movie recommendation system`
   - Đồng ý với Terms of Use
   - Copy **API Key (v3 auth)**

3. **Cập nhật file .env**
   
   Mở file `app/.env` và thêm API key:
   ```env
   TMDB_API_KEY=your_api_key_here
   ```

4. **Restart Backend**
   ```powershell
   # Nếu đang chạy backend, nhấn Ctrl+C để dừng, sau đó chạy lại:
   .\start_backend.ps1
   ```

### Option 2: Chạy Với Docker (Đơn Giản Hơn)

1. **Tạo file .env** ở thư mục gốc (ngang với docker-compose.yml):
   ```env
   TMDB_API_KEY=your_api_key_here
   YOUTUBE_API_KEY=
   ```

2. **Chạy với Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   Backend sẽ chạy tại: http://localhost:8000
   Frontend sẽ chạy tại: http://localhost:3000

## Kiểm Tra

Sau khi cập nhật API key và restart:

1. **Mở trình duyệt**: http://localhost:3000
2. **Kiểm tra poster**: Các phim như Harry Potter should hiển thị poster đúng
3. **Check backend logs**: Sẽ thấy `✅ Using PostgreSQL for user data` và `TMDB_AVAILABLE = True`

## Troubleshooting

### Poster vẫn không đúng?

1. **Check API key**:
   ```bash
   # Test TMDB API
   curl "https://api.themoviedb.org/3/search/movie?api_key=YOUR_KEY&query=Harry+Potter"
   ```

2. **Check backend logs**:
   - Nếu thấy `TMDB_API_KEY chưa được set` → API key chưa được load
   - Nếu thấy `poster_url: https://image.tmdb.org/t/p/w500/...` → Đang hoạt động!

3. **Clear cache**:
   - Xóa cache trình duyệt (Ctrl+Shift+Del)
   - Hoặc mở Incognito mode (Ctrl+Shift+N)

### Docker không fix imports?

Docker container có cấu trúc khác. Tôi cần fix imports cho Docker:

**Fix trong docker-compose.yml**:
```yaml
backend:
  command: uvicorn api.main:app --host 0.0.0.0 --port 8000
  # Thay vì: app.api.main:app
```

## Lưu Ý

- **TMDB API**: Free tier cho phép 40 requests/10 seconds (đủ dùng)
- **Poster caching**: Backend cache 5 phút để tránh gọi API nhiều lần
- **Fallback**: Nếu không có API key, vẫn hiển thị placeholder

## Alternative: Sử dụng Poster Có Sẵn

Nếu không muốn dùng TMDB API, có thể:

1. Download poster pack từ TMDB
2. Lưu vào `app/data/posters/`
3. Update logic để serve local files

Nhưng cách này phức tạp hơn và cần nhiều storage.

## Kết Luận

**Khuyến nghị**: Lấy TMDB API key miễn phí (mất 5 phút) để có poster đúng 100%.

Sau khi setup:
- ✅ Poster hiển thị đúng với phim
- ✅ Trailer videos từ TMDB
- ✅ Metadata chính xác (release date, ratings, etc.)
