# Fix Poster - Tóm Tắt

## ✅ Đã Fix

1. **Cải thiện logic lấy poster** trong `enrich_movies_parallel()`:
   - Ưu tiên dùng poster có sẵn từ database
   - Gọi TMDB API nếu có key
   - Fallback về placeholder nếu không có

2. **Tạo hướng dẫn** trong [FIX_POSTER_GUIDE.md](FIX_POSTER_GUIDE.md)

## 🎯 Giải Pháp Nhanh

### Để có poster đúng với tên phim:

**Bước 1**: Lấy TMDB API Key (Miễn phí)
- Đăng ký tại: https://www.themoviedb.org/signup
- Vào Settings → API → Create → Copy API Key

**Bước 2**: Cập nhật `app/.env`
```env
TMDB_API_KEY=your_key_here
```

**Bước 3**: Restart backend
```powershell
.\start_backend.ps1
```

## 🐛 Vấn Đề Hiện Tại

### Tại sao poster không đúng?

Hệ thống đang dùng **placeholder images** vì:
1. `TMDB_API_KEY` trong `.env` đang để trống
2. Database không có `poster_url` cho các phim
3. Code fallback về random placeholder

### Tại sao cần TMDB API?

- TMDB (The Movie Database) có poster chính thức cho 99% phim
- API miễn phí, 40 requests/10 seconds
- Tự động lấy poster đúng theo tên + năm phim

## 🚀 Chạy Ngay

### Option A: Local (Đã chạy được)
```powershell
.\start_backend.ps1
# Truy cập: http://localhost:8000
```

### Option B: Docker (Cần fix imports)
```bash
docker-compose up --build
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

**Note**: Docker hiện có lỗi import vì structure khác. Cần adjust imports hoặc dùng local.

## 📝 Chi Tiết

Xem [FIX_POSTER_GUIDE.md](FIX_POSTER_GUIDE.md) để biết:
- Cách lấy TMDB API key từng bước
- Troubleshooting nếu vẫn không hoạt động  
- Alternative solutions

## ✨ Kết Quả Sau Fix

Khi có TMDB API key:
- ✅ Poster Harry Potter hiển thị đúng ảnh phim
- ✅ Mọi phim có poster chính thức thay vì ảnh ngẫu nhiên
- ✅ Trailer videos từ YouTube/TMDB
- ✅ Metadata chính xác

**Ước tính thời gian**: 5 phút để lấy API key + restart backend

---

*Nếu không muốn dùng TMDB API (vẫn miễn phí), hệ thống sẽ tiếp tục dùng placeholder. Nhưng để có trải nghiệm tốt nhất, khuyến nghị lấy API key.*
